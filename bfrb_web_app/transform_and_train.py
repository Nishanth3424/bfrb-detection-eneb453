"""
BFRB Detection - Kaggle CMI Sensor Data to MediaPipe Feature Space Transformation
===================================================================================

WHY THIS WORKS
--------------
The Kaggle wrist device and MediaPipe webcam measure the SAME underlying behaviors
through different sensors. We bridge them with a shared 16-feature semantic space:

  Kaggle Sensor                    MediaPipe Analog
  ---------------------------------------------------------------------------
  acc_x/y/z magnitude (m/s^2)  ->  Wrist landmark velocity (normalized coords/frame)
  rot_w/x/y/z derivative        ->  Palm normal vector direction change (radians)
  thm_1..5 thermal (deg C)      ->  Hand-face overlap score (fraction of fingertips near face)
  tof_1 8x8 grid (mm)           ->  Wrist to Nose distance
  tof_2 8x8 grid (mm)           ->  Index fingertip to Mouth distance
  tof_3 8x8 grid (mm)           ->  Thumb tip to Cheek distance
  tof_4 8x8 grid (mm)           ->  Palm center to Forehead distance
  tof_5 8x8 grid (mm)           ->  Wrist to Chin distance

Both are normalized to [0, 1] before training so the model learns in a
scale-independent feature space. A BFRB gesture = low proximity + elevated
thermal/overlap + characteristic movement -- this pattern holds in both domains.

USAGE
-----
  python transform_and_train.py

Outputs:
  model/bfrb_model.pkl     - Trained Random Forest classifier
  model/scaler.pkl         - MinMaxScaler (for reference)
  model/feature_meta.json  - Feature descriptions and normalization bounds
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import joblib
import json
import os
import warnings
warnings.filterwarnings("ignore")

# --- CONFIG -------------------------------------------------------------------

DATA_PATH = (
    r"C:\Users\nisha\Videos\Combined Class Final Project"
    r"\ENEB456-Machine Learning Tools-Spring 2026 ntiglao"
    r"\Current\ML Project Proposal Presentation - FINAL PROJECT NOW"
    r"\cmi-detect-behavior-with-sensor-data\train.csv"
)

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_assets")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Feature names must match exactly what the Flask app receives from MediaPipe
FEATURE_NAMES = [
    "acc_mag_mean",    # Wrist movement intensity (mean)
    "acc_mag_std",     # Wrist movement variability
    "acc_mag_max",     # Peak wrist movement
    "rot_speed_mean",  # Wrist rotation dynamics
    "thm_mean",        # Skin warmth / face overlap (mean)
    "thm_max",         # Peak skin warmth / face overlap
    "tof1_min_mean",   # Closest object to ToF1 -> wrist-to-nose distance
    "tof1_mean_mean",  # Mean proximity to ToF1 -> mean wrist-to-nose
    "tof2_min_mean",   # Closest to ToF2 -> index fingertip-to-mouth
    "tof2_mean_mean",  # Mean ToF2 -> mean index-to-mouth
    "tof3_min_mean",   # Closest to ToF3 -> thumb-to-cheek
    "tof3_mean_mean",  # Mean ToF3 -> mean thumb-to-cheek
    "tof4_min_mean",   # Closest to ToF4 -> palm-to-forehead
    "tof4_mean_mean",  # Mean ToF4 -> mean palm-to-forehead
    "tof5_min_mean",   # Closest to ToF5 -> wrist-to-chin
    "tof5_mean_mean",  # Mean ToF5 -> mean wrist-to-chin
]

# Gestures that are Body-Focused Repetitive Behaviors
BFRB_KEYWORDS = [
    "cheek", "chin", "ear", "eye", "eyebrow", "eyelid",
    "face", "forehead", "hair", "lip", "mouth", "nail",
    "nose", "scalp", "skin", "teeth", "thumb",
]


# --- HELPERS ------------------------------------------------------------------

def is_bfrb(gesture: str) -> int:
    """Return 1 if this gesture is a BFRB, 0 otherwise."""
    g = str(gesture).lower()
    return int(any(kw in g for kw in BFRB_KEYWORDS))


def extract_tof_stats(group: pd.DataFrame, sensor: int):
    """
    Summarize one ToF sensor 8x8 depth grid across a sequence.

    Each row contains 64 distance readings from an 8x8 spatial grid (mm).
    -1 = out of range (treated as NaN). We compute:
      - per-row minimum  = closest object detected that timestep
      - per-row mean     = average proximity that timestep
    Then average both over the full sequence.
    """
    cols = [f"tof_{sensor}_v{i}" for i in range(64)]
    mat = group[cols].values.astype(float)
    mat[mat < 0] = np.nan

    with np.errstate(all="ignore"):
        row_mins  = np.nanmin(mat, axis=1)
        row_means = np.nanmean(mat, axis=1)

    # Rows where ALL pixels are invalid: sensor not firing, treat as 300mm (far)
    row_mins  = np.where(np.isnan(row_mins),  300.0, row_mins)
    row_means = np.where(np.isnan(row_means), 300.0, row_means)

    return float(row_mins.mean()), float(row_means.mean())


def extract_features(group: pd.DataFrame) -> dict:
    """
    Extract 16 semantic features from one gesture sequence.

    These features are designed to match what MediaPipe can compute:
      - Movement magnitude  <->  wrist landmark velocity
      - Rotation speed      <->  palm normal direction change
      - Thermal elevation   <->  hand-face overlap score
      - ToF proximity       <->  hand-to-face landmark distances
    """
    feats = {}

    # 1-3: Accelerometer -> wrist movement dynamics
    acc_mag = np.sqrt(
        group["acc_x"] ** 2 + group["acc_y"] ** 2 + group["acc_z"] ** 2
    )
    feats["acc_mag_mean"] = float(acc_mag.mean())
    feats["acc_mag_std"]  = float(acc_mag.std())
    feats["acc_mag_max"]  = float(acc_mag.max())

    # 4: Quaternion derivative -> wrist rotation speed
    rot_cols = ["rot_w", "rot_x", "rot_y", "rot_z"]
    rot = group[rot_cols].values.astype(float)
    rot_diff = np.diff(rot, axis=0)
    rot_speed = np.sqrt((rot_diff ** 2).sum(axis=1))
    feats["rot_speed_mean"] = float(rot_speed.mean()) if len(rot_speed) > 0 else 0.0

    # 5-6: Thermal -> skin contact / face proximity
    thm_cols = [c for c in group.columns if c.startswith("thm_")]
    thm_mat = group[thm_cols].values.astype(float)
    feats["thm_mean"] = float(thm_mat.mean())
    feats["thm_max"]  = float(thm_mat.max())

    # 7-16: ToF sensors -> proximity to face/body
    for s in range(1, 6):
        tof_check = [f"tof_{s}_v0"]
        if not all(c in group.columns for c in tof_check):
            feats[f"tof{s}_min_mean"]  = 300.0
            feats[f"tof{s}_mean_mean"] = 300.0
            continue
        tmin, tmean = extract_tof_stats(group, s)
        feats[f"tof{s}_min_mean"]  = tmin
        feats[f"tof{s}_mean_mean"] = tmean

    return feats


# --- VISUALIZATION ------------------------------------------------------------

def save_report_charts(clf, X_test, y_test, y_pred, feature_df, labels, FEATURE_NAMES):
    """Save all charts needed for the final report / presentation."""

    colors = {"bfrb": "#ef4444", "no_bfrb": "#3b82f6", "bg": "#0f172a", "text": "#e2e8f0"}
    plt.rcParams.update({
        "figure.facecolor": colors["bg"],
        "axes.facecolor":   "#1a2235",
        "axes.edgecolor":   "#334155",
        "text.color":       colors["text"],
        "axes.labelcolor":  colors["text"],
        "xtick.color":      "#94a3b8",
        "ytick.color":      "#94a3b8",
        "grid.color":       "#1e293b",
        "font.family":      "DejaVu Sans",
    })

    # ---- Chart 1: Feature Importances ----------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    importances = clf.feature_importances_
    idx = np.argsort(importances)
    bar_colors = [colors["bfrb"] if importances[i] > np.median(importances) else colors["no_bfrb"] for i in idx]
    ax.barh(range(len(idx)), importances[idx], color=bar_colors, edgecolor="none")
    ax.set_yticks(range(len(idx)))
    ax.set_yticklabels([FEATURE_NAMES[i] for i in idx], fontsize=9)
    ax.set_xlabel("Feature Importance (Gini)")
    ax.set_title("Random Forest Feature Importances\nKaggle CMI Sensor -> MediaPipe Feature Space", fontsize=12, pad=12)
    ax.grid(axis="x", alpha=0.3)
    high_patch = mpatches.Patch(color=colors["bfrb"],    label="High importance")
    low_patch  = mpatches.Patch(color=colors["no_bfrb"], label="Low importance")
    ax.legend(handles=[high_patch, low_patch], loc="lower right", fontsize=9)
    plt.tight_layout()
    path = os.path.join(REPORT_DIR, "feature_importances.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # ---- Chart 2: Class Distribution -----------------------------------------
    fig, ax = plt.subplots(figsize=(6, 5))
    counts = np.bincount(np.array(labels))
    bars = ax.bar(["No-BFRB", "BFRB"], counts, color=[colors["no_bfrb"], colors["bfrb"]],
                  width=0.5, edgecolor="none")
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                f"{count:,}", ha="center", va="bottom", fontsize=11, color=colors["text"])
    ax.set_ylabel("Number of Sequences")
    ax.set_title("Dataset Class Distribution\nKaggle CMI BFRB Gesture Dataset", fontsize=12, pad=12)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(counts) * 1.15)
    plt.tight_layout()
    path = os.path.join(REPORT_DIR, "class_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # ---- Chart 3: BFRB vs No-BFRB feature comparison (box plots) ------------
    y_arr = np.array(labels)
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    axes = axes.flatten()
    top8 = np.argsort(clf.feature_importances_)[::-1][:8]
    for ax_i, feat_i in enumerate(top8):
        fname = FEATURE_NAMES[feat_i]
        vals_bfrb    = feature_df.iloc[:, feat_i][y_arr == 1].values
        vals_no_bfrb = feature_df.iloc[:, feat_i][y_arr == 0].values
        bp = axes[ax_i].boxplot(
            [vals_no_bfrb, vals_bfrb],
            labels=["No-BFRB", "BFRB"],
            patch_artist=True,
            medianprops=dict(color="#f8fafc", linewidth=2),
            whiskerprops=dict(color="#94a3b8"),
            capprops=dict(color="#94a3b8"),
            flierprops=dict(marker=".", color="#475569", markersize=3),
        )
        bp["boxes"][0].set_facecolor(colors["no_bfrb"])
        bp["boxes"][1].set_facecolor(colors["bfrb"])
        axes[ax_i].set_title(fname, fontsize=8)
        axes[ax_i].grid(axis="y", alpha=0.3)
    fig.suptitle("Top 8 Features: BFRB vs No-BFRB Distribution", fontsize=12, y=1.01)
    plt.tight_layout()
    path = os.path.join(REPORT_DIR, "feature_distributions.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # ---- Chart 4: Confusion Matrix -------------------------------------------
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues", aspect="auto")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["No-BFRB", "BFRB"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["No-BFRB", "BFRB"])
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title("Confusion Matrix (Test Set)", fontsize=12, pad=12)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=16, fontweight="bold",
                    color="white" if cm[i, j] > cm.max()/2 else colors["text"])
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    path = os.path.join(REPORT_DIR, "confusion_matrix.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # ---- Chart 5: Feature Mapping Diagram ------------------------------------
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis("off")
    kaggle_items = [
        "acc_x/y/z (m/s^2)",
        "rot_w/x/y/z (quaternion)",
        "thm_1..5 (thermal, deg C)",
        "tof_1: 8x8 depth grid (mm)",
        "tof_2: 8x8 depth grid (mm)",
        "tof_3: 8x8 depth grid (mm)",
        "tof_4: 8x8 depth grid (mm)",
        "tof_5: 8x8 depth grid (mm)",
    ]
    mediapipe_items = [
        "Wrist velocity magnitude",
        "Palm normal direction change",
        "Hand-face overlap fraction",
        "Wrist to Nose distance",
        "Index tip to Mouth distance",
        "Thumb tip to Cheek distance",
        "Palm to Forehead distance",
        "Wrist to Chin distance",
    ]
    feature_out = [
        "acc_mag_mean/std/max",
        "rot_speed_mean",
        "thm_mean / thm_max",
        "tof1_min_mean / tof1_mean_mean",
        "tof2_min_mean / tof2_mean_mean",
        "tof3_min_mean / tof3_mean_mean",
        "tof4_min_mean / tof4_mean_mean",
        "tof5_min_mean / tof5_mean_mean",
    ]
    row_h = 1.0 / (len(kaggle_items) + 1)
    for i, (k, m, f) in enumerate(zip(kaggle_items, mediapipe_items, feature_out)):
        y = 1.0 - (i + 1.2) * row_h
        ax.text(0.02, y, k, fontsize=8, va="center", color="#93c5fd",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#1e3a5f", edgecolor="none"))
        ax.text(0.50, y, f, fontsize=8, va="center", ha="center", color="#fde68a",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#3d2f00", edgecolor="none"))
        ax.text(0.85, y, m, fontsize=8, va="center", color="#86efac",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#14532d", edgecolor="none"))
        ax.annotate("", xy=(0.45, y), xytext=(0.22, y),
                    arrowprops=dict(arrowstyle="->", color="#94a3b8", lw=1.2))
        ax.annotate("", xy=(0.82, y), xytext=(0.68, y),
                    arrowprops=dict(arrowstyle="->", color="#94a3b8", lw=1.2))
    ax.text(0.10, 0.97, "Kaggle Sensor Data", fontsize=10, fontweight="bold",
            ha="center", va="top", color="#93c5fd")
    ax.text(0.50, 0.97, "Shared 16-Feature Space [0,1]", fontsize=10, fontweight="bold",
            ha="center", va="top", color="#fde68a")
    ax.text(0.90, 0.97, "MediaPipe Landmark Data", fontsize=10, fontweight="bold",
            ha="center", va="top", color="#86efac")
    ax.set_title("Feature Transformation: Kaggle CMI Sensors <-> MediaPipe Landmarks",
                 fontsize=13, pad=16)
    plt.tight_layout()
    path = os.path.join(REPORT_DIR, "feature_mapping_diagram.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")

    # ---- Chart 6: ROC Curve --------------------------------------------------
    from sklearn.metrics import roc_curve, auc
    proba = clf.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, proba)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color=colors["bfrb"], lw=2, label=f"ROC curve (AUC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="#475569", lw=1, linestyle="--", label="Random classifier")
    ax.fill_between(fpr, tpr, alpha=0.1, color=colors["bfrb"])
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve - BFRB Detection\nRandom Forest on Kaggle CMI Features", fontsize=12)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(REPORT_DIR, "roc_curve.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# --- MAIN ---------------------------------------------------------------------

def main():
    import datetime
    run_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 60)
    print("BFRB Classifier Training Pipeline")
    print("Kaggle CMI Sensor Data -> MediaPipe Feature Space")
    print(f"Run date: {run_date}")
    print("=" * 60)

    # [1/5] Load data
    print("\n[1/5] Loading Kaggle CMI sensor data...")
    df = pd.read_csv(DATA_PATH)
    print(f"      Rows: {len(df):,}   |   Sequences: {df['sequence_id'].nunique():,}   |   Columns: {df.shape[1]}")

    seq_gestures = df.groupby("sequence_id")["gesture"].first()
    n_bfrb = seq_gestures.apply(is_bfrb).sum()
    print(f"      BFRB sequences:     {n_bfrb:,}")
    print(f"      Non-BFRB sequences: {len(seq_gestures) - n_bfrb:,}")

    top_gestures = seq_gestures.value_counts().head(12)
    print("\n      Top 12 gestures in dataset:")
    for gesture, count in top_gestures.items():
        tag = "[BFRB]" if is_bfrb(gesture) else "[----]"
        print(f"        {tag} {gesture:<45} {count:>5}")

    # [2/5] Extract features
    print(f"\n[2/5] Extracting {len(FEATURE_NAMES)} features per sequence...")
    feature_rows = []
    labels = []

    grouped = list(df.groupby("sequence_id"))
    total = len(grouped)

    for i, (seq_id, group) in enumerate(grouped):
        if i % 1000 == 0:
            pct = 100 * i / total
            print(f"      Progress: {i:>5}/{total}  ({pct:.0f}%)")
        feats = extract_features(group)
        feature_rows.append(feats)
        labels.append(is_bfrb(group["gesture"].iloc[0]))

    print(f"      Done. Extracted features for {total:,} sequences.")

    # [3/5] Build matrix
    print("\n[3/5] Building feature matrix...")
    feature_df = pd.DataFrame(feature_rows)[FEATURE_NAMES].fillna(0)
    X = feature_df.values
    y = np.array(labels)

    print(f"      Feature matrix shape: {X.shape}")
    counts = np.bincount(y)
    print(f"      Class distribution:   No-BFRB={counts[0]:,}  BFRB={counts[1]:,}")
    print(f"      BFRB ratio:           {counts[1]/len(y)*100:.1f}%")

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"      Train set: {len(X_train):,}   Test set: {len(X_test):,}")

    # [4/5] Train
    print("\n[4/5] Training Random Forest classifier...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    print("\n" + "=" * 60)
    print("MODEL RESULTS")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=["No-BFRB", "BFRB"]))

    importances = clf.feature_importances_
    top_idx = np.argsort(importances)[::-1][:8]
    print("Top 8 Feature Importances:")
    for i in top_idx:
        bar_len = int(importances[i] * 50)
        bar = "#" * bar_len
        print(f"  {FEATURE_NAMES[i]:<22} [{bar:<50}] {importances[i]:.4f}")

    # [5/5] Save model + charts
    print("\n[5/5] Saving model and report assets...")

    model_path  = os.path.join(MODEL_DIR, "bfrb_model.pkl")
    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    meta_path   = os.path.join(MODEL_DIR, "feature_meta.json")

    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)

    meta = {
        "feature_names": FEATURE_NAMES,
        "scaler_min": scaler.data_min_.tolist(),
        "scaler_max": scaler.data_max_.tolist(),
        "bfrb_keywords": BFRB_KEYWORDS,
        "training_date": run_date,
        "n_sequences": total,
        "n_bfrb": int(n_bfrb),
        "n_no_bfrb": int(len(seq_gestures) - n_bfrb),
        "feature_descriptions": {
            "acc_mag_mean":   "Mean wrist acceleration magnitude (Kaggle) -> Mean wrist velocity (MediaPipe)",
            "acc_mag_std":    "Std of wrist acceleration (Kaggle) -> Std of wrist velocity (MediaPipe)",
            "acc_mag_max":    "Peak wrist acceleration (Kaggle) -> Max wrist velocity (MediaPipe)",
            "rot_speed_mean": "Mean quaternion rotation speed (Kaggle) -> Mean palm-normal change (MediaPipe)",
            "thm_mean":       "Mean thermal reading deg C (Kaggle) -> Mean hand-face overlap fraction (MediaPipe)",
            "thm_max":        "Max thermal reading deg C (Kaggle) -> Max hand-face overlap fraction (MediaPipe)",
            "tof1_min_mean":  "Avg min ToF1 distance mm (Kaggle) -> Wrist-to-nose distance (MediaPipe)",
            "tof1_mean_mean": "Avg mean ToF1 distance mm (Kaggle) -> Mean wrist-to-nose (MediaPipe)",
            "tof2_min_mean":  "Avg min ToF2 distance mm (Kaggle) -> Index fingertip-to-mouth (MediaPipe)",
            "tof2_mean_mean": "Avg mean ToF2 distance mm (Kaggle) -> Mean index-to-mouth (MediaPipe)",
            "tof3_min_mean":  "Avg min ToF3 distance mm (Kaggle) -> Thumb tip-to-cheek (MediaPipe)",
            "tof3_mean_mean": "Avg mean ToF3 distance mm (Kaggle) -> Mean thumb-to-cheek (MediaPipe)",
            "tof4_min_mean":  "Avg min ToF4 distance mm (Kaggle) -> Palm center-to-forehead (MediaPipe)",
            "tof4_mean_mean": "Avg mean ToF4 distance mm (Kaggle) -> Mean palm-to-forehead (MediaPipe)",
            "tof5_min_mean":  "Avg min ToF5 distance mm (Kaggle) -> Wrist-to-chin (MediaPipe)",
            "tof5_mean_mean": "Avg mean ToF5 distance mm (Kaggle) -> Mean wrist-to-chin (MediaPipe)",
        },
        "mediapipe_normalization": {
            "note": "MediaPipe features are pre-normalized to [0,1] matching Kaggle normalized space",
            "velocity_max": 0.15,
            "rotation_max": 3.14159,
            "distance_max": 0.8,
            "overlap_max":  1.0,
        },
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  Model    saved -> {model_path}")
    print(f"  Scaler   saved -> {scaler_path}")
    print(f"  Metadata saved -> {meta_path}")

    # Generate report charts
    print("\nGenerating report charts...")
    save_report_charts(clf, X_test, y_test, y_pred, feature_df, labels, FEATURE_NAMES)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Run date:        {run_date}")
    print(f"  Total sequences: {total:,}")
    print(f"  Model location:  {model_path}")
    print(f"  Report assets:   {REPORT_DIR}")
    print("\nNext step: python app.py  ->  open http://localhost:5000")
    print("=" * 60)


if __name__ == "__main__":
    main()
