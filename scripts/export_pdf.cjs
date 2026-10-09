// Optional PDF exporter. Install with: npm install playwright
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
async function main(){
  const [input,output,browserPath] = process.argv.slice(2);
  if(!input || !output) throw new Error('Usage: node scripts/export_pdf.cjs input.html output.pdf [browser-executable]');
  if(path.resolve(input) === path.resolve(output)) throw new Error('Output cannot overwrite source');
  const browser = await chromium.launch({headless:true,...(browserPath?{executablePath:browserPath}:{})});
  try {
    const page=await browser.newPage();
    await page.goto(pathToFileURL(path.resolve(input)).href,{waitUntil:'load'});
    await page.evaluate(()=>document.fonts.ready);
    await page.locator('.step-card img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
    fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});
    await page.pdf({path:output,format:'A4',printBackground:true,preferCSSPageSize:true});
    if(fs.statSync(output).size<100) throw new Error('PDF is empty');
    console.log(path.resolve(output));
  } finally {await browser.close();}
}
main().catch(e=>{console.error(e.message);process.exitCode=1;});
