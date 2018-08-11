const fs = require('fs');
const puppeteer = require('puppeteer');

// a delay function for magic waiting
const delay = (time) => {
  return new Promise((resolve) => setTimeout(resolve, time));
};

// read login data {email, password}
var login_data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));


(async () => {
  const browser = await puppeteer.launch({
    ignoreHTTPSErrors: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768 });
  await page.goto('https://getsupport.apple.com/?caller=grl&locale=zh_TW');

  let mac_product_selector = '#aw-page-wrapper > div.ng-scope > div > div.page-container.cas1._page-cas1 > div.page-body > div.awanimateclass5.ng-scope > div > div.ng-scope > div.ng-scope > div > ul > li:nth-child(1) > div > button > div > div > div.button-content-desc > span';
  await page.waitForSelector(mac_product_selector);
  await delay(1 * 1000);
  await page.click(mac_product_selector);
  await delay(1 * 1000);

  let power_situation_selector = '#aw-page-wrapper > div.ng-scope > div > div.page-container.cas2._page-cas2 > div.page-body > div.awanimateclass5.ng-scope > div > div > div > div:nth-child(3) > ul > li:nth-child(1) > div > button';
  await page.waitForSelector(power_situation_selector);
  await delay(1 * 1000);
  await page.click(power_situation_selector);
  await delay(1 * 1000);

  let genius_bar_selector = '#aw-page-wrapper > div.ng-scope > div > div.page-container.cas3._page-cas3 > div.page-body > div.awanimateclass5.ng-scope > div > div > div.container > ul > li:nth-child(3) > div > button';
  await page.waitForSelector(genius_bar_selector);
  await delay(1 * 1000);
  await page.click(genius_bar_selector);
  await delay(5 * 1000);
  await page.keyboard.type(login_data['email']);
  await page.keyboard.press('Enter');
  await delay(2 * 1000);
  await page.keyboard.type(login_data['password']);
  await page.keyboard.press('Enter');
  await delay(5 * 1000);
  await page.keyboard.press('Tab');
  await page.keyboard.type('台北 101');
  await page.keyboard.press('Enter');
  await delay(5 * 1000);

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
  console.log(texts);
  await browser.close();
})();

