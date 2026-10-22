const API_URL=window.LIBERO_API_URL||((window.location.protocol==='file:'||(['3000','5500'].includes(window.location.port)&&['localhost','127.0.0.1'].includes(window.location.hostname))?`http://${window.location.hostname||'localhost'}:8080`:window.location.origin));
const EDGE_URL=window.LIBERO_EDGE_URL||`http://${window.location.hostname||'localhost'}:8081`;
let USER=null;let IDOSO_ID='dona-maria';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=s=>s?new Date(s).toLocaleString('en-US',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}):'now';
const displayUserName=()=>String(USER?.nome||'Family').replace(/\s*\(Filha\)/i,' (Daughter)').replace(/\s*\(Cuidador\)/i,' (Caregiver)');
function speakResponse(text,language='en'){if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window)){toast('Voice playback is not available in this browser.');return}const portuguese=String(language).toLowerCase().startsWith('pt'),prefix=portuguese?'pt':'en',locale=portuguese?'pt-BR':'en-US';window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.lang=locale;const voices=window.speechSynthesis.getVoices();utterance.voice=voices.find(v=>v.lang.toLowerCase()===locale.toLowerCase())||voices.find(v=>v.lang.toLowerCase().startsWith(prefix))||null;utterance.rate=0.9;window.speechSynthesis.speak(utterance)}
function toast(text){const e=document.querySelector('.toast');if(!e)return;e.textContent=text;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),3200)}
async function req(path,options={}){const r=await fetch(API_URL+path,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});const j=await r.json();if(!r.ok){const e=new Error(j.error||'This action could not be completed.');e.status=r.status;throw e}return j}
let MCP_PROTOCOL=null;let MCP_REQUEST_ID=0;let MCP_READY=null;function setMCPStatus(text,state='warn'){const e=document.querySelector('#mcp-status');if(e){e.textContent=text;e.className=`tag ${state}`}}
async function mcpPost(message,protocol=MCP_PROTOCOL){const headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'};if(protocol)headers['MCP-Protocol-Version']=protocol;const response=await fetch(API_URL+'/mcp',{method:'POST',credentials:'include',headers,body:JSON.stringify(message)});if(response.status===202)return null;const body=await response.json().catch(()=>({}));if(!response.ok||body.error){throw new Error(body.error?.message||body.error||`MCP returned HTTP ${response.status}`)}return body}
async function mcpInitialize(){if(MCP_READY)return MCP_READY;setMCPStatus('Connecting to MCP…','warn');MCP_READY=(async()=>{const initialized=await mcpPost({jsonrpc:'2.0',id:++MCP_REQUEST_ID,method:'initialize',params:{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'libero-family-web',version:'1.0.0'}}},null);if(!initialized?.result?.protocolVersion)throw new Error('The MCP server did not complete initialization.');MCP_PROTOCOL=initialized.result.protocolVersion;await mcpPost({jsonrpc:'2.0',method:'notifications/initialized',params:{}},MCP_PROTOCOL);const discovery=await mcpPost({jsonrpc:'2.0',id:++MCP_REQUEST_ID,method:'tools/list',params:{}},MCP_PROTOCOL);if(!Array.isArray(discovery?.result?.tools))throw new Error('Could not discover MCP tools.');setMCPStatus(`MCP ${MCP_PROTOCOL} connected · ${discovery.result.tools.length} tools`,'ok');return discovery.result.tools})();try{return await MCP_READY}catch(e){MCP_READY=null;setMCPStatus('MCP connection failed','alert');throw e}}
async function mcpCallTool(name,args){const available=await mcpInitialize();if(!available.some(t=>t.name===name))throw new Error(`The MCP tool ${name} was not announced by the server.`);const response=await mcpPost({jsonrpc:'2.0',id:++MCP_REQUEST_ID,method:'tools/call',params:{name,arguments:args}},MCP_PROTOCOL);const result=response?.result;if(!result)throw new Error(response?.error?.message||'The MCP call returned no result.');if(result.isError)throw new Error(result.content?.map(c=>c.text||'').join('\n')||'The MCP tool failed.');setMCPStatus(`MCP ${MCP_PROTOCOL} · ${name} completed`,'ok');const text=result.content?.find(c=>c.type==='text')?.text;if(!text)return result;try{return JSON.parse(text)}catch{return {resposta:text}}}
function nav(active){const items=[['dashboard.html','Today'],['alertas.html','Alerts'],['chat.html','Conversations'],['memorias.html','Memories'],['rede.html','Care network'],['perfil.html','Care profile'],['ambiente.html','Environment']];return `<aside class="nav">${items.map(([h,n])=>`<a class="${active===h?'active':''}" href="${h}">${n}</a>`).join('')}<div class="privacy"><strong>Privacy first</strong>Audio is captured while the edge is running and may be sent to the transcription provider. Camera use requires consent; hiding the stream does not stop capture.</div></aside>`}
function shell(active,content){document.body.innerHTML=`<div class="orb one"></div><div class="orb two"></div><div class="orb three"></div><main class="shell"><header class="topbar"><a class="brand" href="dashboard.html"><img class="brand-icon" src="assets/photon-knot.svg" alt="Libero photon knot"><span><strong>LIBERO</strong><small>Care that stays with you</small></span></a><div class="user-tools"><span id="mic-badge" class="tag warn" style="margin-right:8px" title="Ambient microphone">🎤</span><span>${esc(displayUserName())}</span><div class="avatar">${esc(displayUserName().slice(0,1))}</div><button class="logout" onclick="logout()">Log out</button></div></header><div class="layout">${nav(active)}<section class="page">${content}</section></div></main><div class="toast" aria-live="polite"></div>`}
async function boot(){try{USER=await req('/auth/me');IDOSO_ID=USER.idoso_id&&USER.idoso_id!=='*'?USER.idoso_id:'dona-maria';const page=document.body.dataset.page;({hoje,tasks,chat,memorias,alertas,ambiente,rede,perfil}[page]||hoje)()}catch(e){if(document.body.dataset.page==='hoje')loginScreen();else location.href='dashboard.html'}}
function mountReactBackground(){if(document.getElementById('libero-react-background'))return;const host=document.createElement('div');host.id='libero-react-background';host.setAttribute('aria-hidden','true');document.body.prepend(host);const css=document.createElement('link');css.rel='stylesheet';css.href='assets/react-background/libero-background.css';css.onload=()=>{const script=document.createElement('script');script.src='assets/react-background/libero-background.js';script.onload=()=>window.LiberoBackground?.mount(host);document.head.append(script)};document.head.append(css)}
function loginScreen(){document.body.innerHTML=`<div class="orb one"></div><div class="orb two"></div><div class="orb three"></div><main class="elder-page" style="max-width:460px;padding-top:12vh"><header class="elder-head"><img class="login-icon" src="assets/photon-knot.svg" alt="Libero photon knot"><div class="eyebrow">CARE THAT STAYS WITH YOU</div><h1>Welcome to your care network.</h1><p class="muted">Sign in to stay informed and present.</p></header><section class="card" style="text-align:left;margin-top:28px"><label class="muted">Email<input id="login-email" class="field" type="email" autocomplete="username" placeholder="you@example.com"></label><br><label class="muted">Password<input id="login-password" class="field" type="password" autocomplete="current-password" placeholder="Your password"></label><p id="login-error" class="muted" style="color:var(--danger)"></p><button class="primary" style="width:100%" onclick="login()">Sign in to Libero</button></section></main>`}async function login(){const email=document.querySelector('#login-email').value.trim(),senha=document.querySelector('#login-password').value,err=document.querySelector('#login-error');if(!email||!senha){err.textContent='Enter your email and password.';return}try{USER=await req('/auth/login',{method:'POST',body:JSON.stringify({email,senha})});location.href='dashboard.html'}catch(e){err.textContent=e.message}}
async function logout(){try{await req('/auth/logout',{method:'POST'})}catch(e){}location.href='dashboard.html'}
async function hoje(){shell('dashboard.html',`<div class="hero"><div><div class="eyebrow">Family overview</div><h1>Good morning, ${esc(localStorage.getItem('libero-preferred-name')||'Maria')}.</h1><p>A calm view of the day, so you can care with more presence and less worry.</p></div><a class="primary" href="chat.html">View conversation</a></div><section class="status-card"><div class="eyebrow">Right now</div><h2 id="current-state">Monitoring status not verified.</h2><div class="status-row"><span class="dot"></span><span id="state-detail">History does not confirm that sensors are active.</span></div></section><section class="grid stats"><div class="card"><h3>Recorded interactions</h3><div class="metric" id="stat-interactions">—</div><p class="muted">conversation and support records</p></div><div class="card"><h3>Saved memories</h3><div class="metric" id="stat-memories">—</div><p class="muted">stories that become a legacy</p></div><div class="card"><h3>Recorded alerts</h3><div class="metric" id="stat-alerts">—</div><p class="muted">events that needed attention</p></div></section><section class="card" style="margin-top:16px"><div class="section-title"><h2>Safety &amp; sound events</h2><a class="muted" href="ambiente.html">View environment</a></div><div class="grid stats" id="sound-events"><div class="card"><h3>Falls</h3><div class="metric" id="ev-quedas">0</div></div><div class="card"><h3>Shouts</h3><div class="metric" id="ev-gritos">0</div></div><div class="card"><h3>Movements</h3><div class="metric" id="ev-movimentos">0</div></div><div class="card"><h3>Loud sounds</h3><div class="metric" id="ev-sons">0</div></div></div></section><div class="grid split"><section class="card"><div class="section-title"><h2>Recent activity</h2><a class="muted" href="chat.html">View conversations</a></div><div class="timeline" id="timeline"><div class="empty">Loading today's activity.</div></div></section><section class="card"><div class="section-title"><h2>Next care task</h2><a class="muted" href="tasks.html">View routine</a></div><div id="next-care"><div class="empty">Loading routine.</div></div></section></div>`);try{const [messages,tasks]=await Promise.all([req(`/chat/${IDOSO_ID}/mensagens?limite=8`),req(`/tasks/${IDOSO_ID}`)]);const s=messages.estatisticas||{};document.querySelector('#stat-interactions').textContent=s.total_mensagens||0;document.querySelector('#stat-memories').textContent=s.total_memorias||0;document.querySelector('#stat-alerts').textContent=s.total_emergencias||0;const entries=(messages.mensagens||[]).slice(0,5);document.querySelector('#timeline').innerHTML=entries.length?entries.map(m=>`<div class="timeline-item"><span class="time">${date(m.timestamp).split(', ').pop()}</span><div><span class="item-title">${m.autor==='libero'?'Libero responded to a conversation':m.autor==='idoso'?'A conversation was recorded':'Family care'}</span><br><span class="muted">${esc(m.texto).slice(0,108)}</span></div></div>`).join(''):'<div class="empty">No moments have been recorded today.</div>';const next=(tasks.tasks||[]).filter(t=>t.status==='pendente').sort((a,b)=>a.hora.localeCompare(b.hora))[0];document.querySelector('#next-care').innerHTML=next?`<div class="notice"><strong>${esc(next.hora)} · ${esc(next.titulo)}</strong><br>This item is in the routine; automatic reminders are not connected yet.</div>`:'<div class="empty">No pending care tasks.</div>';try{const ev=await req(`/eventos/${IDOSO_ID}/resumo`);const r=ev.resumo||{};const q=document.querySelector('#ev-quedas');if(q)q.textContent=r.quedas||0;const g=document.querySelector('#ev-gritos');if(g)g.textContent=r.gritos||0;const m=document.querySelector('#ev-movimentos');if(m)m.textContent=r.movimentos||0;const s=document.querySelector('#ev-sons');if(s)s.textContent=r.sons_altos||0}catch(e){}}catch(e){toast(e.message)}}
async function tasks(){shell('tasks.html',`<div class="hero"><div><div class="eyebrow">Care routine</div><h1>A lighter day.</h1><p>Medication, meals, water, and small rituals in one place.</p></div></div><section class="card"><div class="form-grid"><input id="task-title" class="field" placeholder="e.g. Blood pressure medication"><input id="task-hour" class="field" type="time" value="08:00"><select id="task-type" class="field"><option value="remedio">Medication</option><option value="agua">Water</option><option value="refeicao">Meal</option><option value="atividade">Activity</option><option value="outro">Other</option></select><button class="primary" onclick="addTask()">Add</button></div></section><div class="section-title"><h2>Today</h2><span class="muted" id="task-summary"></span></div><section class="card"><div id="task-list"><div class="empty">Loading routine.</div></div></section>`);loadTasks()}
async function loadTasks(){try{const {tasks=[]}=await req(`/tasks/${IDOSO_ID}`);tasks.sort((a,b)=>a.hora.localeCompare(b.hora));document.querySelector('#task-summary').textContent=`${tasks.filter(t=>t.status==='feito').length} of ${tasks.length} completed`;document.querySelector('#task-list').innerHTML=tasks.length?tasks.map(t=>`<div class="task-row ${t.status==='feito'?'done':''}"><span class="hour">${esc(t.hora||'—')}</span><div><strong>${esc(t.titulo)}</strong><small>${esc(({remedio:'Medication',agua:'Water',refeicao:'Meal',atividade:'Activity',outro:'Other'})[t.tipo]||t.tipo)}</small></div><span class="tag ${t.status==='feito'?'ok':t.status==='ignorado'?'alert':'warn'}">${t.status==='feito'?'Completed':t.status==='ignorado'?'Skipped':'Pending'}</span><button class="quiet" onclick="toggleTask('${esc(t.id)}','${t.status}')">${t.status==='feito'?'Reopen':'Complete'}</button></div>`).join(''):'<div class="empty">Add a care task to get started.</div>'}catch(e){toast(e.message)}}
async function addTask(){const titulo=document.querySelector('#task-title').value.trim();if(!titulo)return toast('Enter a care task name.');try{await req(`/tasks/${IDOSO_ID}`,{method:'POST',body:JSON.stringify({titulo,hora:document.querySelector('#task-hour').value,tipo:document.querySelector('#task-type').value})});document.querySelector('#task-title').value='';toast('Care task added to the routine.');loadTasks()}catch(e){toast(e.message)}}async function toggleTask(id,status){try{await req(`/tasks/${IDOSO_ID}/${id}`,{method:'PUT',body:JSON.stringify({status:status==='feito'?'pendente':'feito'})});loadTasks()}catch(e){toast(e.message)}}
async function chat(){
  shell('chat.html',`<div class="hero"><div><div class="eyebrow">Caring conversations</div><h1>Stay informed without intruding.</h1><p>Type a message below to talk to Libero, or speak to the edge device.</p><span id="mcp-status" class="tag warn">MCP ready · not connected</span></div></div><section class="card"><div id="chat-messages" class="chat-container"><div class="empty-state"><div class="empty-icon">&#128172;</div><div class="empty-title">Loading conversations</div></div></div><div class="composer" style="margin-top:20px;display:flex;gap:12px"><input id="message-text" class="field" maxlength="2000" placeholder="Type here..." style="flex:1"><button class="primary" onclick="sendMessage()">Send</button></div></section>`);
  loadMessages();
  if(window._chatInterval)clearInterval(window._chatInterval);
  window._chatInterval=setInterval(loadMessages,5000);
}async function sendMessage(){
  const el = document.querySelector('#message-text');
  const texto = el.value.trim();
  if(!texto) return toast('Write a message before sending.');

  try {
    el.value = '';
    const res = await mcpCallTool('iniciar_conversa', {
      idoso_id: IDOSO_ID,
      mensagem: texto,
      contexto: { nome: 'Maria' }
    });
    if(res.resposta) {
      speakResponse(res.resposta,res.idioma);
    }
    await loadMessages();
  } catch(e) {
    setMCPStatus('MCP request failed','alert');
    toast(e.message);
  }
}async function buscarStatusEdge(){const r=await fetch(`${EDGE_URL}/status`,{cache:'no-store'});if(!r.ok)throw new Error(`Edge returned HTTP ${r.status}`);return r.json()}async function atualizarStatusEdge(){try{const s=await buscarStatusEdge(),audio=s.listener||{},camera=s.camera||{};const edge=document.querySelector('#edge-state'),mic=document.querySelector('#audio-state'),cam=document.querySelector('#camera-state'),count=document.querySelector('#audio-count'),frame=document.querySelector('#frame-state'),error=document.querySelector('#edge-error');if(!edge)return;edge.textContent=s.edge_running?'Connected':'Stopped';edge.className=`tag ${s.edge_running?'ok':'warn'}`;const micState=audio.estado_microfone||(audio.rodando?'ouvindo':'parado');mic.textContent=micState==='ouvindo'?'Active':micState==='inicializando'?'Starting':micState==='travado'?'Initialization stalled':micState==='erro'?'Unavailable':'Stopped';mic.className=`tag ${micState==='ouvindo'?'ok':micState==='travado'||micState==='erro'?'alert':'warn'}`;count.textContent=audio.frases_processadas??0;cam.textContent=camera.ativa?(camera.consentimento?'Active with consent':'Active'):(camera.consentimento?'Consented, no image':'Disabled');cam.className=`tag ${camera.ativa?'ok':'warn'}`;frame.textContent=s.camera_frame_atual?'Current':`No recent frame${s.camera_frame_age_seconds!=null?' · '+s.camera_frame_age_seconds+'s':''}`;if(error)error.textContent=audio.ultimo_erro||''}catch(e){const edge=document.querySelector('#edge-state'),mic=document.querySelector('#audio-state'),cam=document.querySelector('#camera-state'),error=document.querySelector('#edge-error');if(edge){edge.textContent='Unavailable';edge.className='tag alert'}if(mic){mic.textContent='Could not verify';mic.className='tag warn'}if(cam){cam.textContent='Could not verify';cam.className='tag warn'}if(error)error.textContent='Start the edge process and confirm LIBERO_EDGE_ALLOWED_ORIGINS for this origin.'}}async function startCamera(){try{const s=await buscarStatusEdge();if(!s.camera?.ativa){toast('The edge camera is not active. Check consent and the edge process.');return}document.querySelector('#camera-frame').innerHTML=`<img src="${EDGE_URL}/stream" alt="Edge camera stream" style="width:100%;height:100%;object-fit:cover;border-radius:12px" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'camera-message',innerHTML:'<strong>Stream unavailable</strong><p>Check the edge process and consent.</p>'}))">`;toast('Preview opened; edge capture remains active.')}catch(e){toast('Could not query the edge: '+e.message)}}function stopCamera(){document.querySelector('#camera-frame').innerHTML='<div class="camera-message"><strong>Preview hidden</strong><p>Edge capture continues according to device settings.</p></div>';toast('Image hidden; stop the edge to stop capture.')}
function rede(){shell('rede.html',`<div class="hero"><div><div class="eyebrow">Care network</div><h1>Everyone who cares, in sync.</h1><p>Choose who receives each alert and who can help in each situation.</p></div><button class="primary" onclick="addPerson()">Add person</button></div><section class="card"><h2>People in your network</h2><div id="people" class="people"></div></section><section class="card" style="margin-top:16px"><h2>Response plan</h2><p class="muted">This response plan is a local demo. Invites, alerts, and escalation are not connected yet.</p><div class="notice">1. Ana, daughter · 2. Carlos, caregiver · 3. Helena, trusted neighbor</div></section>`);renderPeople()}function people(){return JSON.parse(localStorage.getItem('libero-care-network')||'[{"name":"Ana Rivera","role":"Daughter and primary contact","initial":"A","enabled":true},{"name":"Carlos Smith","role":"Caregiver","initial":"C","enabled":true},{"name":"Dr. Helen Lima","role":"Doctor","initial":"H","enabled":false}]')}function renderPeople(){const list=people();document.querySelector('#people').innerHTML=list.map((p,i)=>`<div class="person"><div class="avatar">${esc(p.initial)}</div><div class="grow"><strong>${esc(p.name)}</strong><div class="muted">${esc(p.role)}</div></div><span class="muted">Receives alerts</span><button class="switch ${p.enabled?'on':''}" aria-label="Toggle alerts for ${esc(p.name)}" onclick="togglePerson(${i})"></button></div>`).join('')}function togglePerson(i){const l=people();l[i].enabled=!l[i].enabled;localStorage.setItem('libero-care-network',JSON.stringify(l));renderPeople()}function addPerson(){toast('This button could invite someone by email or WhatsApp in a future version.');}
function perfil(){shell('perfil.html',`<div class="hero"><div><div class="eyebrow">Care profile</div><h1>What makes her feel at home.</h1><p>Demo form: only the preferred name is saved in this browser; the other fields do not guide the agent yet.</p></div><button class="primary" onclick="saveProfile()">Save preferences</button></div><section class="card"><div class="grid profile-grid"><label>Preferred name<input id="preferred-name" class="field" value="Maria"></label><label>Comforting routine<input class="field" value="Morning coffee with music"></label><label>Important people<input class="field" value="Ana, Carlos, grandchildren"></label><label>Favorite music and topics<input class="field" value="Samba, stories from her youth"></label><label>What helps her feel calm<textarea class="field" rows="3">Speak slowly, validate the feeling, and offer a happy memory.</textarea></label><label>Plan for a crisis<textarea class="field" rows="3">Offer comfort, remove risks, and notify Ana if agitation continues.</textarea></label></div></section><section class="card" style="margin-top:16px"><h2>How Libero uses this information</h2><p class="muted">Only the preferred name is saved. The other fields are not used by the agent or to create reminders.</p></section>`)}function saveProfile(){localStorage.setItem('libero-preferred-name',document.querySelector('#preferred-name').value);toast('Only the preferred name is saved on this device; the other fields are not saved.');}
function elder(){document.body.innerHTML=`<div class="elder-page"><header class="elder-head"><img src="assets/libero-logo.jpeg" alt="Logo Libero"><div class="eyebrow">LIBERO</div><h1>Hello, Maria.</h1><p class="muted">I'm here with you.</p></header><p class="notice">Demo: the buttons below show simulated responses. They do not play music, display photos, or send notifications.</p><section class="elder-actions"><button onclick="elderReply('Let's talk. I'm here to listen.')">Talk to Libero</button><button onclick="elderReply('I'll play some relaxing music for you.')">Listen to music</button><button onclick="elderReply('Let's look at some lovely family memories.')">View family photos</button><button onclick="elderReply('This help request is a demo. No notification was sent.')">Ask for help</button></section><p id="elder-response" class="notice" hidden></p></div>`}function elderReply(text){const e=document.querySelector('#elder-response');e.hidden=false;e.textContent=text}
window.addEventListener('DOMContentLoaded',()=>{if(document.body.dataset.public==='elder'){elder();mountReactBackground();return}boot().finally(mountReactBackground)});


// ============================================================
// MICROFONE DO CUIDADOR (toggle)
// ============================================================

let micCaregiverActive = false;

async function toggleMicrophone() {
  const btn = document.getElementById('mic-cuidador-btn');
  const status = document.getElementById('mic-cuidador-status');
  
  if (!micCaregiverActive) {
    const texto = prompt("What would you like to say to Maria?");
    if (!texto) return;
    
    try {
      await req('/audio/cuidador/enviar', {
        method: 'POST',
        body: JSON.stringify({
          texto: texto,
          idoso_id: IDOSO_ID
        })
      });
      
      btn.textContent = '🔴 Speaking...';
      btn.classList.add('gravando');
      status.textContent = 'Message sent';
      status.className = 'tag ok';
      
      setTimeout(() => {
        btn.textContent = '🎤 Speak to the older adult';
        btn.classList.remove('gravando');
        status.textContent = 'Ready to speak';
        status.className = 'tag warn';
      }, 3000);
    } catch (e) {
      toast('Error: ' + e.message);
    }
  }
}


// ============================================================
// BADGE DE MICROFONE
// ============================================================

async function atualizarBadgeMic() {
  try {
    const s = await buscarStatusEdge();
    const badge = document.getElementById('mic-badge');
    if (!badge) return;
    const estado = s.listener?.estado_microfone;
    const ativo = estado ? estado === 'ouvindo' : Boolean(s.listener?.rodando);
    badge.className = `tag ${ativo ? 'ok' : estado === 'travado' || estado === 'erro' ? 'alert' : 'warn'}`;
    badge.title = ativo
      ? `Microphone listening · ${s.listener.frases_processadas || 0} phrases transcribed`
      : estado === 'inicializando'
        ? 'Microphone starting'
        : estado === 'travado' || estado === 'erro'
          ? `Microphone unavailable · ${s.listener.ultimo_erro || 'check the audio device'}`
          : 'Edge unavailable or microphone stopped';
  } catch (e) {
    const badge = document.getElementById('mic-badge');
    if (badge) { badge.className = 'tag alert'; badge.title = 'Could not check the actual edge status'; }
  }
}

// Refresh every 5 seconds
setInterval(atualizarBadgeMic, 5000);

// ============================================================
// REAL-TIME NOTIFICATIONS (WebSocket)
// ============================================================

let wsNotif = null;

function conectarWebSocket() {
  if (wsNotif && wsNotif.readyState === WebSocket.OPEN) return;
  
  const WS_URL = API_URL.replace(/^http/, 'ws') + '/ws';
  
  try {
    wsNotif = new WebSocket(WS_URL);
    
    wsNotif.onopen = () => {
      console.log('[Libero WS] Connected');
    };
    
    wsNotif.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.tipo === 'emergencia') {
          mostrarEmergencia(msg);
        }
      } catch (err) {}
    };
    
    wsNotif.onclose = () => {
      console.log('[Libero WS] Desconectado. Tentando reconectar em 5s...');
      setTimeout(conectarWebSocket, 5000);
    };
    
    wsNotif.onerror = (e) => {
      console.log('[Libero WS] Error:', e);
    };
  } catch (err) {
    console.log('[Libero WS] Erro ao conectar:', err);
  }
}

function mostrarEmergencia(msg) {
  // Optional alert sound
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.frequency.value = 880;
    osc.type = 'sine';
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1);
    osc.start();
    osc.stop(audioCtx.currentTime + 1);
  } catch (err) {}
  
  // Native browser notification
  if (Notification.permission === 'granted') {
    new Notification('EMERGENCY - Libero', {
      body: `${msg.evento} detected at ${msg.local}`,
      icon: '/assets/logo.svg',
      tag: 'emergencia'
    });
  }
  
  // Overlay visual
  const agora = new Date(msg.timestamp || Date.now()).toLocaleTimeString('en-US');
  const overlay = document.createElement('div');
  overlay.className = 'emergency-overlay';
  overlay.innerHTML = `
    <div class="em-icon">⚠️</div>
    <h1>EMERGENCY</h1>
    <p><strong>${(msg.evento || 'event').toUpperCase()}</strong> detected at ${msg.local || 'home'}</p>
    <p class="em-time">${agora} · Confidence ${((msg.confianca || 0) * 100).toFixed(0)}%</p>
    <button onclick="this.parentElement.remove()">Got it, view details</button>
  `;
  document.body.appendChild(overlay);
}

// Request notification permission
function pedirPermissaoNotificacao() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

// Connect WebSocket when the dashboard loads
window.addEventListener('load', () => {
  pedirPermissaoNotificacao();
  conectarWebSocket();
});


// ============================================================
// CONVERSATIONS (message bubbles)
// ============================================================


async function loadMessages(){
  try{
    const r = await req('/chat/' + IDOSO_ID + '/mensagens?limite=100');
    const mensagens = r.mensagens || [];
    const container = document.querySelector('#chat-messages');
    if(!container) return;
    
    const ordered = [...mensagens].reverse();
    
    if(!ordered.length){
      container.innerHTML = '<div class="empty-state"><div class="empty-icon">&#128172;</div><div class="empty-title">No conversations yet</div><div class="empty-text">Talk to Libero to start a conversation.</div></div>';
      return;
    }
    
    let ultimoDia = '';
    container.innerHTML = ordered.map(function(m){
      const data = new Date(m.timestamp);
      const dia = data.toLocaleDateString('en-US', {day:'2-digit', month:'long'});
      const hora = data.toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'});
      
      let divisor = '';
      if(dia !== ultimoDia){ divisor = '<div class="chat-day">' + dia + '</div>'; ultimoDia = dia; }
      
      const tipo = m.tipo || 'normal';
      const autor = m.autor || 'libero';
      
      let classe = 'eh-libero';
      let nome = 'Libero';
      let av = 'L';
      
      if(autor === 'idoso'){ classe = 'eh-idoso'; nome = 'Maria'; av = 'M'; }
      else if(autor === 'sistema' || autor === 'familia'){ classe = 'eh-sistema'; nome = 'Monitoring'; av = '!'; }
      else if(autor === 'cuidador'){ nome = 'You (caregiver)'; av = 'C'; }
      
      return divisor
        + '<div class="chat-bubble ' + classe + ' tipo-' + tipo + '">'
        + '<div class="chat-avatar">' + av + '</div>'
        + '<div class="chat-content">'
        + '<div class="chat-name">' + nome + '</div>'
        + '<div class="chat-text">' + esc(m.texto || '') + '</div>'
        + '<div class="chat-time">' + hora + (autor==='libero'&&m.metadata?.provedor_modelo?' · Model: '+esc(m.metadata.provedor_modelo==='bedrock'?'Amazon Bedrock':m.metadata.provedor_modelo==='groq'?'Groq':'local fallback'):'') + '</div>'
        + '</div>'
        + '</div>';
    }).join('');
    
    container.scrollTop = container.scrollHeight;
  }catch(e){
    toast(e.message);
  }
}
