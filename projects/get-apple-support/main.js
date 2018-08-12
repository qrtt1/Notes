const fs = require('fs');
const winston = require('winston');
const log = winston;
log.add(new winston.transports.Console({
  format: winston.format.simple()
}));

const puppeteer = require('puppeteer');

// a delay function for magic waiting
const delay = (time) => {
  return new Promise((resolve) => setTimeout(resolve, time));
};

// read login data {email, password}
var login_data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

var email = login_data['email'] || "";
var password = login_data['password'] || "";
var dev_mode = login_data['dev_mode'] || false;

log.info('load user configuration');

(async () => {
  const browser = await puppeteer.launch({
    ignoreHTTPSErrors: true,
    headless: !dev_mode,
    devtools: dev_mode
  });

  log.info('access getsupport.apple.com');
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768 });
  await page.goto('https://getsupport.apple.com/?caller=grl&locale=zh_TW');

  log.info('wait "Mac" button');
  await page.waitForSelector('span[aw-resource="Mac"]');
  await page.click('span[aw-resource="Mac"]');

  log.info('wait "Power" button');
  await page.waitForSelector('span[aw-resource="啟動或電源"]');
  await page.click('span[aw-resource="啟動或電源"]');
  await delay(5000);
  
  log.info('wait help button');
  await delay(1000);
  // console.log(await page.content());
  await page.waitForSelector('span[aw-resource="親自送修"]');
  await page.click('span[aw-resource="親自送修"]');

  // 登入頁的 selector 都抓不太到
  // 直接用 keyboard 處理唄
  log.info('start to login');
  // waitForNavigation 常抓不到狀態，只好強制 delay 了
  await delay(5000);
  await page.keyboard.type(email);
  await page.keyboard.press('Enter');
  await delay(1000);
  await page.keyboard.type(password);
  await page.keyboard.press('Enter');
  await page.waitForNavigation({waitUntil: "networkidle0"});
  
  // 輸入目前所在位置
  log.info('input location');
  await page.waitForSelector('input[placeholder="目前所在位置"]');
  await page.keyboard.press('Tab');
  await page.keyboard.type('台北 101');
  await page.keyboard.press('Enter');
  await page.waitForSelector('input[class="store-item"]');
  
  let texts = await page.evaluate(() => {
    let data = [];
    let elements = document.getElementsByClassName('store-details');
    for (var element of elements) {
      let store = element.textContent
        .replace(/[\t ]+/g, '')
        .replace(/\n+/g, '\n')
        .replace(/(^\n|\n$)/g, '');
      if (store.includes('可預約') && store.includes('台北')) {
        data.push(store);
      }
    }
    return data;
  });
  console.info(texts);
  await browser.close();
})();

