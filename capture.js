// CDP screenshot driver — captures specific scroll positions at a realistic viewport
const { spawn } = require('child_process');
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const URL = "file:///D:/Desktop/VAST%20CHALLENGE/index.html";
const PORT = 9233;

const chrome = spawn(CHROME, [
  "--headless=new","--disable-gpu","--hide-scrollbars","--no-first-run",
  `--remote-debugging-port=${PORT}`,
  "--window-size=1440,960", URL
]);

const sleep = ms => new Promise(r=>setTimeout(r,ms));

async function main(){
  await sleep(2500);
  // find page target
  let targets;
  for(let i=0;i<20;i++){
    try{ targets = await (await fetch(`http://localhost:${PORT}/json`)).json(); if(targets.find(t=>t.type==='page'))break; }catch(e){}
    await sleep(300);
  }
  const page = targets.find(t=>t.type==='page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id=0; const pend={};
  ws.addEventListener('message',ev=>{const m=JSON.parse(ev.data);if(m.id&&pend[m.id]){pend[m.id](m.result);delete pend[m.id];}});
  await new Promise(r=>ws.addEventListener('open',r));
  const cmd=(method,params={})=>new Promise(res=>{const i=++id;pend[i]=res;ws.send(JSON.stringify({id:i,method,params}));});

  await cmd('Page.enable');
  await cmd('Runtime.enable');
  await cmd('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});
  await sleep(3500); // let fonts + JS render

  const shots = require('./_shotspec.json'); // [{name, scrollFn}]
  for(const s of shots){
    await cmd('Runtime.evaluate',{expression:s.js});
    await sleep(800);
    const r = await cmd('Page.captureScreenshot',{format:'png'});
    require('fs').writeFileSync(s.name, Buffer.from(r.data,'base64'));
    console.log('wrote',s.name);
  }
  ws.close(); chrome.kill(); process.exit(0);
}
main().catch(e=>{console.error(e);chrome.kill();process.exit(1);});
