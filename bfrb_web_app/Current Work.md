# BFRB Detection System — Current Work
**Project:** ENEB453 Web-Based Application Development — Final Project
**Student:** Nishanth Tiglao
**Date:** April 13, 2026
**Status:** Active Development — v2 Rule-Based + Pinch-Pull Engine

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [What is a BFRB?](#2-what-is-a-bfrb)
3. [All BFRB Movements To Be Tracked](#3-all-bfrb-movements-to-be-tracked)
4. [Technology Stack](#4-technology-stack)
5. [What Has Been Built So Far](#5-what-has-been-built-so-far)
6. [Detection Mathematics — Every Formula Explained](#6-detection-mathematics--every-formula-explained)
7. [Detection Engine Architecture](#7-detection-engine-architecture)
8. [Kaggle Approach (v1) — What Was Tried and Why It Failed](#8-kaggle-approach-v1--what-was-tried-and-why-it-failed)
9. [Current Approach (v2) — Rule-Based State Machine](#9-current-approach-v2--rule-based-state-machine)
10. [File Structure](#10-file-structure)
11. [What Still Needs To Be Done](#11-what-still-needs-to-be-done)

---

## 1. Project Overview

This project is a **real-time Body-Focused Repetitive Behavior (BFRB) detection web application** that uses a standard webcam to identify when a person is performing a BFRB gesture. The system runs entirely in the browser using **MediaPipe Holistic** for hand and face landmark detection, and a custom detection engine written in JavaScript that analyzes the geometric relationships between hand landmarks and face landmarks every frame.

The app is served by a **Flask (Python) web server** and runs at `http://localhost:5000`.

### Core Goal
Detect, in real time, when a person is:
- Touching their face/head with their hand in a compulsive/repetitive way
- Pulling their hair from scalp, eyebrows, or eyelashes
- Picking at skin on their face or body
- Biting their nails or cuticles
- Picking their nose
- Biting or picking their lips

And **not** trigger a false alarm when the person:
- Waves hello
- Types on a keyboard
- Scratches an itch quickly
- Briefly touches their face while speaking
- Moves their hand past their face

---

## 2. What is a BFRB?

**Body-Focused Repetitive Behaviors (BFRBs)** are a group of related disorders characterized by repetitive self-grooming behaviors that involve touching, pulling, picking, or biting one's own hair, skin, or nails. They are classified under **Obsessive-Compulsive and Related Disorders** in the DSM-5.

### Common Types
| Clinical Name | Common Name | Body Target |
|---|---|---|
| Trichotillomania | Hair Pulling | Scalp, eyebrows, eyelashes, facial hair |
| Excoriation Disorder | Skin Picking | Face, arms, back, any skin surface |
| Onychophagia | Nail Biting | Fingernails, toenails, cuticles |
| Rhinotillexis | Nose Picking | Nasal passages |
| Dermatophagia | Skin Biting | Fingers, cheeks, lips |
| Morsicatio Buccarum | Cheek Biting | Inner cheeks |
| Trichophagia | Hair Eating | Hair (pulled then eaten) |

### Why Detection Matters
BFRBs affect approximately **5% of the population**. People are often unaware they are doing it — the behaviors happen automatically, especially during stress or distraction. Real-time detection can provide **self-awareness alerts** that interrupt the behavior before it escalates.

---

## 3. All BFRB Movements To Be Tracked

The following are the specific physical gestures this system must detect, based on:
- The Kaggle CMI dataset gesture labels
- Clinical BFRB movement patterns from research
- MediaPipe landmark capabilities

### 3.1 Hair Pulling (Trichotillomania)

**Physical description:** Hand moves toward scalp or eyebrow/eyelash area. Fingers form a **pinch** (thumb + index, or thumb + multiple fingers). Fingers close around a hair strand. Hand then **pulls away** from the scalp/face with force.

**Key sub-types:**
- Scalp hair pull (top/back of head) — hand approaches from above
- Hairline pull (forehead area) — fingers near forehead, pull upward/forward
- Eyebrow pull — fingertips near eyebrow ridge
- Eyelash pull — fingertips near eye/eyelid area
- Sideburn/temple pull — fingers near ear/temple

**Distinguishing motion:** The defining feature is the **pinch-then-pull** motion. The hand comes toward the scalp, forms a tight pinch, then moves AWAY from the head. This is what separates hair pulling from just scratching your head.

**From Kaggle dataset (gesture labels):**
- "Forehead - pull hairline"
- "Eyelash - pull hair"
- "Above ear - pull hair"
- "Eyebrow - pull hair"
- "Scalp - pull hair" (various orientations)

---

### 3.2 Skin Picking (Excoriation)

**Physical description:** Hand approaches face or other skin surface. **Multiple fingertips cluster together** (not just 2-finger pinch — all 5 tips bunch up). Fingers make a small gathering/pinching motion on the skin surface. Hand may or may not pull away significantly — often stays on skin and works a spot repeatedly.

**Key sub-types:**
- Cheek picking — fingers near cheek, slow repetitive motion
- Forehead picking — fingers near forehead
- Chin picking — fingers near chin/jaw
- Neck picking — fingers at neck
- Nose picking/biting — fingers at nose tip

**Distinguishing motion:** Unlike hair pulling, skin picking often involves **staying in one spot** with slow micro-movements rather than a single pull-away. The cluster of all fingertips bunching together is the diagnostic signal.

**From Kaggle dataset:**
- "Cheek - pinch skin"
- "Neck - pinch skin"
- "Forehead - scratch"
- "Neck - scratch"
- "Chin - pinch skin"

---

### 3.3 Nail Biting (Onychophagia)

**Physical description:** Hand raises toward mouth. **One or two fingertips** (usually index or thumb) approach the **upper lip / teeth area**. The finger(s) remain near or at the mouth. Often involves a slight up-down or side-to-side movement of the finger at the lip.

**Distinguishing motion:** This is a **proximity + dwell** behavior. The fingertip(s) stay near the mouth for an extended period (unlike drinking, which is a brief touch).

**From Kaggle dataset:**
- "Nail - bite"
- "Thumb - suck"
- "Cuticle - pick" (at mouth)

---

### 3.4 Nose Picking (Rhinotillexis)

**Physical description:** Index finger (sometimes thumb) approaches the **nose tip** and enters or contacts the nostril area. Typically slow, deliberate motion with a single fingertip.

**Distinguishing motion:** Single fingertip proximity to nose, sustained, with low velocity. The index finger is nearly always the active finger.

**From Kaggle dataset:**
- "Nose - pick"

---

### 3.5 Face Touching (General)

**Physical description:** Palm, wrist, or multiple fingers make contact with the general face area (not a specific feature). The hand moves toward the face and rests there. Often involves the palm on the cheek or forehead.

**Distinguishing motion:** Slow approach + sustained contact. Wrist proximity to nose is the primary signal when palm/full hand is on face.

**From Kaggle dataset:**
- "Face - touch"
- "Cheek - rest hand"
- "Pull air toward your face"

---

### 3.6 Lip Picking / Biting

**Physical description:** Index finger or thumb touches the **lower lip**. Can involve repeated small motions. Different from nail biting in that the finger touches the lip itself, not the teeth.

**Distinguishing motion:** Index/thumb tip close to lower lip landmark with dwell time.

---

### 3.7 Eyebrow / Eyelash Pulling (Sub-type of Hair Pulling)

**Physical description:** Thumb and index finger form a very precise **2-finger pinch** near the eyebrow ridge or eyelid. Motion is a small upward/outward pull.

**Distinguishing motion:** Precise pinch (small pinch area, not full multi-finger cluster) + very close to eyebrow/eye face landmarks + small pull distance.

**From Kaggle dataset:**
- "Eyebrow - pull hair"
- "Eyelash - pull hair"

---

### Summary Table — All Movements

| # | BFRB Name | Primary Landmarks | Key Signal | Detection Method |
|---|---|---|---|---|
| 1 | Hair Pulling (scalp) | Grab point → Forehead | Pinch + pull-away ≥ 0.28fw | Pinch-Pull Engine |
| 2 | Hair Pulling (eyebrow) | Thumb+Index → Eyebrow | Precise 2-finger pinch + small pull | Pinch-Pull Engine |
| 3 | Hair Pulling (eyelash) | Thumb+Index → Eye | Precise pinch near eye | Pinch-Pull Engine |
| 4 | Hair Pulling (temple) | Grab point → Left Cheek | Pinch near temple + pull | Pinch-Pull Engine |
| 5 | Skin Picking (cheek) | All fingertips → Left/Right Cheek | Cluster + dwell | Cluster + Dwell |
| 6 | Skin Picking (forehead) | All fingertips → Forehead | Cluster + dwell | Cluster + Dwell |
| 7 | Skin Picking (chin) | All fingertips → Chin | Cluster + dwell | Cluster + Dwell |
| 8 | Nail Biting | Index/Thumb tip → Upper Lip | Proximity + dwell | Dwell Engine |
| 9 | Nose Picking | Index tip → Nose Tip | Proximity + dwell | Dwell Engine |
| 10 | Face Touching | Wrist/Index → Nose | Proximity + dwell | Dwell Engine |
| 11 | Lip Picking | Index tip → Lower Lip | Proximity + dwell | Dwell Engine |
| 12 | Forehead Touching | Wrist/Index → Forehead | Proximity + dwell | Dwell Engine |

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.11, Flask 3.1 | Serve web app, host trained ML model |
| Landmark Detection | MediaPipe Holistic (JS CDN) | Extract 543 landmarks per frame (21 hand + 468 face + 33 pose) |
| Detection Logic | Vanilla JavaScript | State machine, math, pinch-pull engine |
| ML Model (v1, archived) | scikit-learn Random Forest | Trained on Kaggle sensor data |
| Data Normalization | MinMaxScaler (sklearn) | Kaggle feature normalization |
| Report Charts | matplotlib (Python) | Training result visualizations |
| Frontend | HTML5, CSS3, Canvas API | UI, video overlay, real-time display |

---

## 5. What Has Been Built So Far

### Phase 1 — Kaggle Data Transformation (v1, Archived)
- Downloaded and analyzed the **CMI Kaggle dataset** (574,945 rows, 8,151 sequences, 341 columns)
- Engineered **16 semantic features** from wrist sensor data (accelerometer, quaternion, thermal, 5×ToF depth grids)
- Trained a **Random Forest classifier** (200 trees): 77% accuracy, AUC-ROC = **0.837** on Kaggle test set
- Attempted to bridge Kaggle sensor features → MediaPipe landmark features via normalization
- **Result: Too many false positives** due to domain gap between physical sensor units and image coordinates
- Full failure analysis documented in `report_assets/kaggle_approach_report.html`
- All artifacts archived: `model/bfrb_model.pkl`, `templates/index_kaggle_v1.html`

### Phase 2 — Rule-Based Detection Engine (v2, Current)
- Replaced ML model with a **4-state machine** running directly on MediaPipe landmarks
- Implemented **adaptive thresholds** that scale with detected face width
- Implemented **EMA smoothing** on all distances and velocity
- Implemented **velocity filter** to block fast movements from triggering
- Implemented **dwell timer** with proximity → dwell → BFRB state progression
- Implemented **BFRB type classification** by nearest face landmark

### Phase 3 — Pinch-Pull Detection (v2 Enhancement, Current)
- Added **pinch strength measurement** (thumb-to-index distance normalized by face width)
- Added **fingertip cluster measurement** (mean spread of all 5 fingertips from centroid)
- Added **pinch-near-face detection** with location-specific zones (scalp, cheek, chin, nose)
- Added **pull-back confirmation** (hand moves ≥ 28% face width away while still pinched)
- Pinch-pull fires **immediately** (no 1-second dwell needed) for hair pulling and skin picking
- State history shows **purple dots** during pinch formation, red on confirmation

---

## 6. Detection Mathematics — Every Formula Explained

### 6.1 Euclidean Distance (2D)

Used for all landmark-to-landmark measurements. **2D only** (x, y) — the z-axis from MediaPipe is unreliable depth estimation that inflates distances.

```
dist(A, B) = sqrt((A.x - B.x)² + (A.y - B.y)²)
```

**Units:** MediaPipe normalizes all landmarks to the range [0.0, 1.0] where (0,0) is top-left and (1,1) is bottom-right of the camera frame.

---

### 6.2 Face Width (Adaptive Baseline)

The face width is the distance between the **left cheek** (landmark 234) and **right cheek** (landmark 454) of the MediaPipe Face Mesh.

```
faceWidth = dist(face[234], face[454])
           = sqrt((face[234].x - face[454].x)² + (face[234].y - face[454].y)²)
```

**Why this matters:** If you sit closer to the camera, your face appears larger. A fixed pixel-distance threshold would fire too easily up close and never fire from far away. By dividing all distances by `faceWidth`, every threshold is expressed in **"face-width units"** — scale-invariant regardless of camera distance.

**Typical values:** `faceWidth` ≈ 0.08 (sitting far) to 0.25 (sitting very close), in normalized image coordinates.

---

### 6.3 Face-Width Normalization

Every distance measurement is divided by `faceWidth` before any comparison:

```
d_normalized = dist(handLandmark, faceLandmark) / faceWidth
```

**Example interpretation:**
- `d_normalized = 0.5` → hand is half a face-width away from that face point
- `d_normalized = 0.2` → hand is 20% of a face-width away (getting close)
- `d_normalized = 0.05` → hand is basically touching that face point

---

### 6.4 Exponential Moving Average (EMA) Smoothing

Applied to: distances, velocity, pinch strength, cluster strength.

```
s_t = α × x_t + (1 - α) × s_{t-1}
```

Where:
- `s_t` = smoothed value at frame t
- `x_t` = raw measured value at frame t
- `s_{t-1}` = previous smoothed value
- `α` = smoothing factor (0 = no response, 1 = no smoothing)

**Values used:**
- `α = 0.25` — for distances and overall proximity (moderate smoothing)
- `α = 0.20` — for wrist velocity (heavier smoothing, more lag = less jitter)
- `α = 0.30` — for pinch strength and cluster (faster response needed)

**Why EMA:** MediaPipe detects landmarks at 30fps. Individual frames can have detection errors (a landmark jumps slightly). EMA prevents a single bad frame from triggering a state change.

---

### 6.5 Minimum Proximity Distance

The overall "hand near face" signal uses the minimum distance across all monitored landmark pairs:

```
rawMin = min(
  dist(wrist, nose),
  dist(indexTip, upperLip),
  dist(thumbTip, upperLip),
  dist(indexTip, nose),
  dist(indexTip, leftCheek),
  dist(grabPoint, forehead)
) / faceWidth

smoothDist = 0.25 × rawMin + 0.75 × prevSmoothDist
```

**Threshold:** `smoothDist < 0.35` = hand is within 35% of one face-width from any monitored face point → enters PROXIMITY state.

---

### 6.6 Wrist Velocity

Measures how fast the wrist is moving between consecutive frames.

```
rawVelocity_t = dist(wrist_t, wrist_{t-1})
             = sqrt((wrist_t.x - wrist_{t-1}.x)² + (wrist_t.y - wrist_{t-1}.y)²)

smoothVelocity = 0.20 × rawVelocity_t + 0.80 × prevSmoothVelocity
```

**Threshold:** `smoothVelocity < 0.08` = slow/stationary movement.

**Why velocity matters:** A BFRB is a slow, deliberate, often repetitive motion. Waving your hand past your face registers a high velocity. Holding your finger near your mouth while biting registers very low velocity. The velocity filter prevents fast passing motions from triggering the BFRB state.

---

### 6.7 Dwell Timer

Measures how long the hand has continuously been in the proximity zone.

```
if (smoothDist < threshold) AND (dwellStartTime is null):
    dwellStartTime = currentTimestamp

dwellDuration = currentTimestamp - dwellStartTime   (in milliseconds)
```

**Thresholds:**
- `dwellDuration ≥ 500ms` → advance from PROXIMITY to DWELL state
- `dwellDuration ≥ 1000ms` AND `smoothVelocity < 0.08` → advance from DWELL to BFRB state

**Why dwell time:** Intentional brief face touches (adjusting glasses, wiping sweat) last < 300ms. Compulsive BFRB behaviors are sustained — the hand lingers. Requiring 1 full second filters out nearly all accidental touches.

---

### 6.8 Pinch Strength

Measures how tightly the thumb and index finger (or thumb and middle finger) are pressed together — the "grabbing" grip used to pinch hair or skin.

```
d_thumbToIndex  = dist(hand[4], hand[8])  / faceWidth
d_thumbToMiddle = dist(hand[4], hand[12]) / faceWidth

minPinchDist = min(d_thumbToIndex, d_thumbToMiddle)

rawPinchStrength = max(0, min(1,  1 - (minPinchDist - 0.05) / 0.30))
```

**Interpretation:**
- `minPinchDist ≤ 0.05fw` → rawPinchStrength = 1.0 (fully closed pinch)
- `minPinchDist = 0.20fw` → rawPinchStrength = 0.5 (half pinch)
- `minPinchDist ≥ 0.35fw` → rawPinchStrength = 0.0 (open hand)

After EMA smoothing (α = 0.30):
```
smoothPinch = 0.30 × rawPinchStrength + 0.70 × prevSmoothPinch
```

**Detection threshold:** `smoothPinch > 0.55` = fingers are definitely pinching.

**Why thumb + middle also:** Hair pulling sometimes uses a 3-finger pinch (thumb + index + middle). Checking the minimum of both ensures either type is detected.

---

### 6.9 Fingertip Cluster Score

Measures how tightly ALL five fingertips are grouped together — the characteristic posture for skin picking (multiple fingers gather skin surface).

```
tips = [hand[4], hand[8], hand[12], hand[16], hand[20]]
        (thumb,  index,   middle,   ring,     pinky tips)

centroid.x = (tips[0].x + tips[1].x + tips[2].x + tips[3].x + tips[4].x) / 5
centroid.y = (tips[0].y + tips[1].y + tips[2].y + tips[3].y + tips[4].y) / 5

meanSpread = (1/5) × Σ dist(tips[i], centroid) / faceWidth
           = (1/5) × Σ sqrt((tips[i].x - centroid.x)² + (tips[i].y - centroid.y)²) / faceWidth

rawClusterStrength = max(0, min(1,  1 - (meanSpread - 0.04) / 0.21))
```

**Interpretation:**
- `meanSpread ≤ 0.04fw` → rawClusterStrength = 1.0 (all tips touching)
- `meanSpread = 0.125fw` → rawClusterStrength = 0.5
- `meanSpread ≥ 0.25fw` → rawClusterStrength = 0.0 (hand fully spread)

After EMA smoothing (α = 0.30):
```
smoothCluster = 0.30 × rawClusterStrength + 0.70 × prevSmoothCluster
```

**Detection threshold:** `smoothCluster > 0.22` = fingertips are notably clustered.

---

### 6.10 Grab Point (Pinch Center)

The "grabbing point" is the midpoint between thumb tip and index tip — the actual point where a hair or skin would be grabbed.

```
grabPoint.x = (hand[4].x + hand[8].x) / 2
grabPoint.y = (hand[4].y + hand[8].y) / 2
```

This point is used to check if the pinch is happening near a face/scalp zone.

---

### 6.11 Pinch-Zone Proximity Check

For a pinch to be considered "near the face/scalp," the grab point must be within a zone radius of a specific face landmark:

```
zoneDistance = dist(grabPoint, face[zoneLandmark]) / faceWidth

isInZone = (zoneDistance < zoneRadius)
```

**Zone radii (in face-width units):**
| Zone | Face Landmark | Radius | BFRB Type |
|---|---|---|---|
| Forehead/scalp | face[10] (forehead) | 0.80fw | Hair Pulling |
| Temple/sideburn | face[234] (left cheek) | 0.75fw | Hair Pulling |
| Left cheek | face[234] | 0.55fw | Skin Picking |
| Right cheek | face[454] | 0.55fw | Skin Picking |
| Chin | face[152] | 0.55fw | Skin Picking |
| Nose | face[1] | 0.45fw | Skin Picking |

**Why larger zones for hair pulling:** The scalp is above and behind the face. Face landmarks are on the face surface, not the top of the head. A larger radius is needed to catch a hand reaching up into the hairline.

---

### 6.12 Pull-Back Distance

After a pinch is confirmed near a face/scalp zone, the system tracks how far the hand has moved away from where the pinch started:

```
pullDistance = smoothDist_current - smoothDist_atPinchStart
```

**Trigger threshold:** `pullDistance ≥ 0.28fw` = hand moved at least 28% of face width away from the pinch origin = confirmed pull-back.

**Why 0.28fw:** A natural hair pull involves the hand moving approximately 2–4 inches away from the scalp. At a normal camera distance, this corresponds to roughly 25–35% of face width in image coordinates. 0.28 is the lower bound that ensures genuine pulls are caught while minor finger repositioning is not.

---

### 6.13 Confidence Score

The confidence score (0.0 to 1.0) represents how certain the system is that a BFRB is occurring. It's used for the UI progress bar and color coding.

**For dwell-based detection:**
```
if state == BFRB:
    confidence = min(1.0,  dwellDuration / (BFRB_MS × 1.5))

if state == DWELL:
    confidence = (dwellDuration - DWELL_MS) / (BFRB_MS - DWELL_MS) × 0.6

if state == PROXIMITY:
    confidence = dwellDuration / DWELL_MS × 0.25
```

**For pinch-pull detection:**
```
confidence = 1.0   (immediate — pull-back is unambiguous)
```

---

### 6.14 MediaPipe Landmark Reference

MediaPipe Holistic provides 543 landmarks per frame:

**Hand Landmarks (21 per hand, index 0–20):**
```
0  = Wrist
1  = Thumb CMC       4  = Thumb Tip
5  = Index MCP       8  = Index Tip
9  = Middle MCP     12  = Middle Tip
13 = Ring MCP       16  = Ring Tip
17 = Pinky MCP      20  = Pinky Tip
```

**Face Mesh Landmarks (468 total) — Key ones used:**
```
1   = Nose Tip
10  = Forehead Center
13  = Upper Lip (top edge)
14  = Lower Lip (bottom edge)
152 = Chin
234 = Left Cheek (outer)
454 = Right Cheek (outer)
```

---

## 7. Detection Engine Architecture

```
Camera Feed (30fps)
       │
       ▼
MediaPipe Holistic
  ├── 21 Hand Landmarks (x, y, z)
  ├── 468 Face Mesh Landmarks (x, y, z)
  └── 33 Pose Landmarks (x, y, z)
       │
       ▼
BFRBDetector.update(hand, face, timestamp)
       │
       ├── [1] Face width computed → adaptive scale baseline
       │
       ├── [2] All distances computed → normalized by faceWidth
       │       wrist→nose, index→mouth, thumb→mouth, index→nose,
       │       index→cheek, grabPoint→forehead
       │
       ├── [3] EMA smoothing on rawMin distance → smoothDist
       │
       ├── [4] Wrist velocity computed → EMA smoothed → smoothVel
       │
       ├── [5] Pinch strength computed → EMA smoothed → smoothPinch
       │
       ├── [6] Cluster strength computed → EMA smoothed → smoothCluster
       │
       ├── [7] PINCH-PULL ENGINE (parallel track)
       │       NONE → [pinch near zone?] → PINCHED
       │       PINCHED → [pull ≥ 0.28fw?] → CONFIRMED → fire BFRB immediately
       │
       ├── [8] DWELL STATE MACHINE (main track)
       │       IDLE → [dist < 0.35fw?] → PROXIMITY
       │       PROXIMITY → [500ms elapsed?] → DWELL
       │       DWELL → [1000ms elapsed AND slow?] → BFRB
       │       BFRB → [dist > threshold for 300ms?] → IDLE
       │
       ├── [9] BFRB Type Classification
       │       Which face landmark is closest to hand?
       │       → Nail Biting / Nose Picking / Face Touching /
       │         Hair Pulling / Skin Picking / Lip Touching
       │
       └── [10] Result: { state, bfrbType, confidence, isBFRB, isPinchPull, ... }
                          │
                          ▼
                    updateUI()
                  Draw on canvas + Update side panel
```

---

## 8. Kaggle Approach (v1) — What Was Tried and Why It Failed

### What Was Done
- Used **CMI Detect Behavior with Sensor Data** from Kaggle
- Dataset: 574,945 rows, 8,151 sequences, 341 sensor columns
- Sensors: accelerometer (acc_x/y/z), quaternion rotation (rot_w/x/y/z), 5 thermal sensors (thm_1..5), 5 Time-of-Flight depth grids (tof_1..5, each 8×8 = 64 values)

### Feature Engineering
Extracted 16 features per gesture sequence:

| # | Feature | Kaggle Computation | MediaPipe Analog |
|---|---|---|---|
| 1 | acc_mag_mean | mean(√(ax²+ay²+az²)) | mean wrist velocity |
| 2 | acc_mag_std | std(acceleration magnitude) | std wrist velocity |
| 3 | acc_mag_max | max(acceleration magnitude) | max wrist velocity |
| 4 | rot_speed_mean | mean(‖Δquaternion‖) | palm normal direction change |
| 5 | thm_mean | mean(thm_1..5) in °C | hand-face overlap fraction (mean) |
| 6 | thm_max | max(thm_1..5) in °C | hand-face overlap fraction (max) |
| 7–8 | tof1_min/mean_mean | avg of per-row min/mean of ToF1 8×8 grid | wrist-to-nose distance |
| 9–10 | tof2_min/mean_mean | ToF sensor 2 | index-to-mouth distance |
| 11–12 | tof3_min/mean_mean | ToF sensor 3 | thumb-to-cheek distance |
| 13–14 | tof4_min/mean_mean | ToF sensor 4 | palm-to-forehead distance |
| 15–16 | tof5_min/mean_mean | ToF sensor 5 | wrist-to-chin distance |

### Training Results
- Model: RandomForestClassifier (200 trees, max_depth=12, balanced class weights)
- Accuracy: **77%**
- AUC-ROC: **0.837**
- BFRB F1: **0.82** / No-BFRB F1: 0.68

### Why It Failed
1. **Thermal → face overlap mismatch:** `thm_max` was the #1 most important feature (13.8% importance). Thermal sensors detect actual skin temperature rising from contact. The MediaPipe analog (fingertips within 0.18 radius of nose) fires on any raised hand — completely different physical event.

2. **Scale mismatch:** Kaggle ToF values are in millimeters (50–300mm range). MediaPipe distances are in normalized image coordinates (0–0.8 range). Even after MinMaxScaler normalization, the decision boundaries learned from millimeter-scale patterns don't transfer to image-coordinate-scale patterns.

3. **No temporal modeling:** Model trained on per-sequence features (entire gesture aggregated). MediaPipe ran on 30-frame windows. This means mid-gesture clips were classified the same as complete behaviors.

4. **Zero shot domain transfer:** The model never saw a single MediaPipe-derived feature during training. Transfer learning without target domain data requires the domains to be much more similar than these two are.

**Full report:** `report_assets/kaggle_approach_report.html`

---

## 9. Current Approach (v2) — Rule-Based State Machine

### Core Design Philosophy
Instead of training on one domain and hoping it transfers to another, v2 **operates natively in MediaPipe space**. Every threshold and formula is defined in terms of face-width-normalized MediaPipe landmark distances — the same space we're detecting in.

### Why Rule-Based Works for BFRB
Published BFRB detection apps (BFRBye, Hands Off, StopBitingNails, Naily) all use rule-based proximity + dwell time detection, not trained classifiers. The reason: BFRBs have **clear, consistent geometric signatures** that don't require learned representations:
- Hair pulling always requires proximity to the scalp AND a pinch AND a pull-away
- Nail biting always requires a fingertip near the mouth AND sustained presence
- These are physics-constrained events, not learned patterns

### Two Detection Pathways

**Pathway 1 — Dwell-Based (face touching, nail biting, nose picking)**
- Detects behaviors where the hand **stays near** the face
- Requires sustained proximity for ≥ 1 second with slow movement
- Guards against: fast passes, accidental touches, gestures while talking

**Pathway 2 — Pinch-Pull (hair pulling, skin picking)**
- Detects the **grab-and-pull** motion specific to hair pulling and skin picking
- Does NOT require a 1-second dwell — a confirmed pull-back triggers immediately
- Guards against: open-hand face touches, slow resting hand on face

---

## 10. File Structure

```
bfrb_web_app/
├── app.py                          Flask server (serves HTML, hosts archived ML model)
├── transform_and_train.py          Kaggle data transformation + RF training (v1, archived)
├── requirements.txt                Python dependencies
│
├── model/                          Trained ML artifacts (v1, archived)
│   ├── bfrb_model.pkl              Random Forest classifier
│   ├── scaler.pkl                  MinMaxScaler
│   └── feature_meta.json           Feature names, descriptions, normalization bounds
│
├── templates/
│   ├── index.html                  CURRENT — v2 rule-based detection engine
│   └── index_kaggle_v1.html        ARCHIVED — v1 Kaggle ML approach
│
├── report_assets/
│   ├── kaggle_approach_report.html Full technical report on v1 failure analysis
│   ├── feature_importances.png     RF feature importance chart
│   ├── confusion_matrix.png        Test set confusion matrix
│   ├── roc_curve.png               ROC curve (AUC = 0.837)
│   ├── class_distribution.png      Dataset class counts
│   ├── feature_distributions.png   BFRB vs No-BFRB per feature box plots
│   └── feature_mapping_diagram.png Kaggle ↔ MediaPipe feature bridge diagram
│
└── Current Work.md                 THIS FILE
```

---

## 11. What Still Needs To Be Done

### Detection Improvements Needed
- [ ] **Eyelash/eyebrow pulling** — need tighter pinch zone near eye landmarks (face[33], face[133] for eyes)
- [ ] **Scalp hair pulling** — hand goes above frame (MediaPipe loses it). Need to handle the "hand exits top of frame while pinched near forehead" case
- [ ] **Skin biting (dermatophagia)** — biting fingers/cuticles. Requires detecting finger(s) actually inside the mouth region, not just near it
- [ ] **Cheek biting** — requires detecting hand at side of face near jaw, mouth slightly open (pose landmark for jaw needed)
- [ ] **Repetition counter** — count how many times a BFRB occurs in a session and graph frequency over time

### Technical Improvements Needed
- [ ] **Database logging** — log each BFRB event (timestamp, type, duration) to SQLite via Flask for session history
- [ ] **User calibration screen** — let user set distance from camera and confirm face detection quality before starting
- [ ] **Alert system** — audio alert + browser notification when BFRB confirmed (currently only visual)
- [ ] **Session report** — end-of-session summary showing BFRB frequency, types, time patterns

### For Final Presentation
- [ ] Live demo with all 5 core BFRBs demonstrated
- [ ] Show feature bars moving in real time
- [ ] Show state history dot trail going purple (pinch) → red (BFRB)
- [ ] Screenshot the confusion matrix and ROC curve from report assets for slides

---

*Last updated: April 13, 2026 — Nishanth Tiglao — ENEB453 Spring 2026*
