const puppeteer = require('C:/Users/nisha/AppData/Roaming/npm/node_modules/puppeteer');
const path = require('path');

const WIREFRAME = 'file:///C:/Users/nisha/Videos/Combined%20Class%20Final%20Project/Final%20Project/ENEB453/wireframe/wireframe.html';
const ERD      = 'file:///C:/Users/nisha/Videos/Combined%20Class%20Final%20Project/Final%20Project/ENEB453/erd/erd_diagram.html';
const OUT_DIR  = 'C:/Users/nisha/Videos/Combined Class Final Project/Final Project/ENEB453/screenshots';

const fs = require('fs');
if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 1.5 });

  // Screenshot 1: Wireframe (full page)
  await page.goto(WIREFRAME, { waitUntil: 'networkidle0' });
  await page.screenshot({ path: OUT_DIR + '/wireframe.png', fullPage: true });
  console.log('Wireframe screenshot done');

  // Screenshot 2: ERD full page
  await page.goto(ERD, { waitUntil: 'networkidle0' });
  await page.screenshot({ path: OUT_DIR + '/erd.png', fullPage: true });
  console.log('ERD screenshot done');

  await browser.close();
  console.log('All screenshots saved to: ' + OUT_DIR);
})();
