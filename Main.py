from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
from datetime import datetime
import os

app = FastAPI()

HTML_CODE = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChatWave</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:sans-serif}
body{background:#0e1621;color:#fff;height:100vh;display:flex;flex-direction:column}
.header{background:#17212b;padding:15px;display:flex;justify-content:space-between;border-bottom:1px solid #2b5278}
.logo{color:#5288c1;font-weight:bold;font-size:20px}
.groups{display:flex;gap:6px;padding:10px;background:#17212b;overflow-x:auto;border-bottom:1px solid #2b5278}
.gbtn{padding:7px 12px;border-radius:15px;border:none;background:#2b5278;color:white;font-size:12px}
.gbtn.active{background:#5288c1}
.messages{flex:1;overflow-y:auto;padding:15px;display:flex;flex-direction:column;gap:10px}
.bubble{max-width:75%;padding:10px 12px;border-radius:12px;font-size:14px}
.me{align-self:flex-end;background:#2b5278}.other{align-self:flex-start;background:#182533}
.time{font-size:10px;opacity:.6;text-align:right;margin-top:3px}
.input{display:flex;padding:10px;background:#17212b;gap:8px}
.input input{flex:1;padding:12px;border-radius:20px;border:none;background:#242f3d;color:white;outline:none}
.input button{width:45px;height:45px;border-radius:50%;border:none;background:#5288c1;color:white}
.login{position:fixed;inset:0;background:#0e1621;display:flex;align-items:center;justify-content:center;z-index:99}
.box{background:#17212b;padding:30px;border-radius:15px;width:90%;max-width:320px;text-align:center}
.box input{width:100%;padding:12px;margin:15px 0;border-radius:8px;border:none;background:#242f3d;color:white}
.box button{width:100%;padding:12px;background:#5288c1;border:none;border-radius:8px;color:white;font-weight:bold}
.users{padding:8px;font-size:12px;color:#7d8b99;background:#17212b}
</style></head><body>
<div class="login" id="login"><div class="box"><h1 style="color:#5288c1">CHATWAVE</h1><p>Telegram Clone Live</p>
<input id="uname" placeholder="Your name e.g David"><button onclick="join()">JOIN CHAT 🚀</button></div></div>
<div class="header"><div><div class="logo">ChatWave</div><div style="font-size:12px;color:#7d8b99" id="ocount">0 online</div></div><div id="myname"></div></div>
<div class="groups">
<button class="gbtn active" onclick="setG('general',this)">💬 General</button>
<button class="gbtn" onclick="setG('tech',this)">💻 Tech</button>
<button class="gbtn" onclick="setG('crypto',this)">📈 Crypto</button>
</div>
<div class="users" id="ulist"></div>
<div class="messages" id="msgs"></div>
<div class="input"><input id="minput" placeholder="Write a message..." onkeypress="if(event.key=='Enter')send()"><button onclick="send()">➤</button></div>
<script>
let ws, me, grp='general';
function join(){
  me=document.getElementById('uname').value.trim();
  if(!me)return alert('Enter name');
  document.getElementById('login').style.display='none';
  document.getElementById('myname').innerText='@'+me;
  let p=location.protocol=='https:'?'wss:':'ws:';
  ws=new WebSocket(p+'//'+location.host+'/ws/'+me);
  ws.onmessage=(e)=>{
    let d=JSON.parse(e.data);
    if(d.type=='init'){document.getElementById('ocount').innerText=d.users.length+' online';document.getElementById('ulist').innerText=d.users.join(', ');d.messages.forEach(m=>{if(m.group==grp)add(m)});}
    else if(d.type=='message'){if(d.group==grp)add(d);}
    else if(d.type=='join'||d.type=='leave'){document.getElementById('ocount').innerText=d.users.length+' online';document.getElementById('ulist').innerText=d.users.join(', ');}
  };
}
function add(m){let div=document.createElement('div');div.className='bubble '+(m.sender==me?'me':'other');div.innerHTML=(m.sender!=me?'<b style="color:#5288c1;font-size:11px">@'+m.sender+'</b><br>':'')+m.text+'<div class="time">'+m.time+'</div>';document.getElementById('msgs').appendChild(div);document.getElementById('msgs').scrollTop=99999;}
function send(){let i=document.getElementById('minput');if(!i.value.trim())return;ws.send(JSON.stringify({text:i.value,group:grp}));i.value='';}
function setG(g,btn){grp=g;document.querySelectorAll('.gbtn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');document.getElementById('msgs').innerHTML='';}
</script></body></html>
"""

users={}
messages=[]

@app.get("/")
async def home():
    return HTMLResponse(HTML_CODE)

@app.websocket("/ws/{username}")
async def ws_chat(websocket: WebSocket, username: str):
    await websocket.accept()
    users[username]=websocket
    await websocket.send_text(json.dumps({"type":"init","users":list(users.keys()),"messages":messages[-30:]}))
    for u,w in users.items():
        if u!=username:
            try: await w.send_text(json.dumps({"type":"join","users":list(users.keys())}))
            except: pass
    try:
        while True:
            data=await websocket.receive_text()
            d=json.loads(data)
            new={"type":"message","sender":username,"text":d.get("text",""),"group":d.get("group","general"),"time":datetime.now().strftime("%H:%M")}
            messages.append(new)
            for w in users.values():
                try: await w.send_text(json.dumps(new))
                except: pass
    except WebSocketDisconnect:
        if username in users: del users[username]
        for w in users.values():
            try: await w.send_text(json.dumps({"type":"leave","users":list(users.keys())}))
            except: pass
