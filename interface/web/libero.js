const API_URL=window.LIBERO_API_URL||((window.location.protocol==='file:'||['3000','5500'].includes(window.location.port))?`${window.location.protocol==='https:'?'https':'http'}://${window.location.hostname||'localhost'}:8080`:window.location.origin);
const EDGE_URL=window.LIBERO_EDGE_URL||`http://${window.location.hostname||'localhost'}:8081`;
const CAMERA_PREVIEW_KEY='libero:camera-preview';
let USER=null;let IDOSO_ID='dona-maria';let avatarState='idle';let avatarBundlePromise=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=s=>s?new Date(s).toLocaleString('en-US',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}):'now';
const displayUserName=()=>String(USER?.nome||'Family').replace(/\s*\(Filha\)/i,' (Daughter)').replace(/\s*\(Cuidador\)/i,' (Caregiver)');
const saudacaoAtual=()=>{const hora=new Date().getHours();return hora<12?'Good morning':hora<18?'Good afternoon':'Good evening'};
const idiomaDaMensagem=texto=>/[ãõáàâéêíóôúç]/i.test(texto)||/\b(oi|olá|você|obrigado|obrigada|bom dia|boa noite|tudo|não|quero|estou)\b/i.test(texto)?'pt-BR':navigator.language||'en-US';
function speakResponse(text,language=navigator.language||'pt-BR'){if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window)){setAvatarEstado('idle');toast('Voice playback is not available in this browser.');return}const portuguese=String(language).toLowerCase().startsWith('pt'),prefix=portuguese?'pt':'en',locale=portuguese?'pt-BR':'en-US';window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.lang=locale;const voices=window.speechSynthesis.getVoices();utterance.voice=voices.find(v=>v.lang.toLowerCase()===locale.toLowerCase())||voices.find(v=>v.lang.toLowerCase().startsWith(prefix))||null;utterance.rate=0.9;utterance.onstart=()=>setAvatarEstado('falando');utterance.onend=()=>setAvatarEstado('idle');utterance.onerror=()=>setAvatarEstado('idle');setAvatarEstado('falando');window.speechSynthesis.speak(utterance)}
function toast(text){const e=document.querySelector('.toast');if(!e)return;e.textContent=text;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),3200)}
async function req(path,options={}){const r=await fetch(API_URL+path,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});const j=await r.json();if(!r.ok){const e=new Error(j.error||'This action could not be completed.');e.status=r.status;throw e}return j}
function cameraPreviewRequested(){return sessionStorage.getItem(CAMERA_PREVIEW_KEY)==='1'}
function renderCameraPreview(){if(document.getElementById('camera-floating-preview'))return;const panel=document.createElement('aside');panel.id='camera-floating-preview';panel.className='camera-floating';panel.setAttribute('aria-label','Live camera preview');const heading=document.createElement('div');heading.className='camera-floating-heading';const title=document.createElement('strong');title.textContent='Camera preview stays on';const hide=document.createElement('button');hide.className='quiet';hide.type='button';hide.textContent='Hide';hide.setAttribute('aria-label','Hide camera preview');hide.addEventListener('click',stopCamera);heading.append(title,hide);const image=document.createElement('img');image.src=`${EDGE_URL}/stream`;image.alt='Live view of the care environment';image.onerror=()=>{const message=document.createElement('p');message.className='camera-message';message.textContent='Live preview unavailable. Check the Edge camera.';image.replaceWith(message)};panel.append(heading,image);document.body.append(panel)}
function nav(active){const items=[['dashboard.html','Today'],['alertas.html','Alerts'],['chat.html','Conversations'],['memorias.html','Memories'],['rede.html','Care network'],['perfil.html','Care profile'],['ambiente.html','Environment']];return `<aside class="nav">${items.map(([h,n])=>`<a class="${active===h?'active':''}" href="${h}">${n}</a>`).join('')}<div class="privacy"><strong>Privacy first</strong>Audio is captured while the edge is running and may be sent to the transcription provider. Camera use requires consent; hiding the stream does not stop capture.</div></aside>`}
function shell(active,content){document.body.innerHTML=`<div class="orb one"></div><div class="orb two"></div><div class="orb three"></div><main class="shell"><header class="topbar"><a class="brand" href="dashboard.html"><img class="brand-icon" src="assets/photon-knot.svg" alt="Libero photon knot"><span><strong>LIBERO</strong><small>Care that stays with you</small></span></a><div class="user-tools"><span id="mic-badge" class="tag warn" style="margin-right:8px" title="Ambient microphone">🎤</span><span>${esc(displayUserName())}</span><div class="avatar">${esc(displayUserName().slice(0,1))}</div><button class="quiet" onclick="abrirModoTV()">Care screen</button><button class="logout" onclick="logout()">Log out</button></div></header><div class="layout">${nav(active)}<section class="page">${content}</section></div></main><div class="toast" aria-live="polite"></div>`;if(cameraPreviewRequested()&&active!=='ambiente.html')renderCameraPreview()}
async function boot(){try{USER=await req('/auth/me');IDOSO_ID=USER.idoso_id&&USER.idoso_id!=='*'?USER.idoso_id:'dona-maria';conectarWebSocket();const page=document.body.dataset.page;const pages={hoje,tasks,chat,memorias,alertas,ambiente,rede,perfil};(pages[page]||hoje)()}catch(e){if(document.body.dataset.page==='hoje')loginScreen();else location.href='dashboard.html'}}
function abrirModoTV(){const url=new URL('idoso.html?modo=tv',location.href);const popup=window.open(url.href,'libero-care-screen');if(!popup)toast('Allow the new window to open the care screen.')}
function mountReactBackground(){if(document.getElementById('libero-react-background'))return;const host=document.createElement('div');host.id='libero-react-background';host.setAttribute('aria-hidden','true');document.body.prepend(host);const css=document.createElement('link');css.rel='stylesheet';css.href='assets/react-background/libero-background.css';css.onload=()=>{const script=document.createElement('script');script.src='assets/react-background/libero-background.js';script.onload=()=>window.LiberoBackground?.mount(host);document.head.append(script)};document.head.append(css)}
function loginScreen(){document.body.innerHTML=`<div class="orb one"></div><div class="orb two"></div><div class="orb three"></div><main class="elder-page" style="max-width:460px;padding-top:12vh"><header class="elder-head"><img class="login-icon" src="assets/photon-knot.svg" alt="Libero photon knot"><div class="eyebrow">CARE THAT STAYS WITH YOU</div><h1>Welcome to your care network.</h1><p class="muted">Sign in to stay informed and present.</p></header><section class="card" style="text-align:left;margin-top:28px"><label class="muted">Email<input id="login-email" class="field" type="email" autocomplete="username" placeholder="you@example.com"></label><br><label class="muted">Password<input id="login-password" class="field" type="password" autocomplete="current-password" placeholder="Your password"></label><p id="login-error" class="muted" style="color:var(--danger)"></p><button class="primary" style="width:100%" onclick="login()">Sign in to Libero</button></section></main>`}async function login(){const email=document.querySelector('#login-email').value.trim(),senha=document.querySelector('#login-password').value,err=document.querySelector('#login-error');if(!email||!senha){err.textContent='Enter your email and password.';return}try{USER=await req('/auth/login',{method:'POST',body:JSON.stringify({email,senha})});const destino=sessionStorage.getItem('libero-return-to')||'dashboard.html';sessionStorage.removeItem('libero-return-to');location.href=destino}catch(e){err.textContent=e.message}}
async function logout(){try{sessionStorage.removeItem(`libero:chat:v1:${IDOSO_ID}`);sessionStorage.removeItem(CAMERA_PREVIEW_KEY)}catch(e){console.error('Could not clear the local session state during logout.',e)}try{await req('/auth/logout',{method:'POST'})}catch(e){}location.href='dashboard.html'}
async function hoje(){shell('dashboard.html',`<div class="hero"><div><div class="eyebrow">Family overview</div><h1>${saudacaoAtual()}, ${esc(localStorage.getItem('libero-preferred-name')||'Maria')}.</h1><p>A calm view of the day, so you can care with more presence and less worry.</p></div><a class="primary" href="chat.html">View conversation</a></div><section class="status-card"><div class="eyebrow">Right now</div><h2 id="current-state">Monitoring status not verified.</h2><div class="status-row"><span class="dot"></span><span id="state-detail">History does not confirm that sensors are active.</span></div></section><section class="grid stats"><div class="card"><h3>Recorded interactions</h3><div class="metric" id="stat-interactions">—</div><p class="muted">conversation and support records</p></div><div class="card"><h3>Saved memories</h3><div class="metric" id="stat-memories">—</div><p class="muted">stories that become a legacy</p></div><div class="card"><h3>Recorded alerts</h3><div class="metric" id="stat-alerts">—</div><p class="muted">events that needed attention</p></div></section><section class="card" style="margin-top:16px"><div class="section-title"><h2>Safety &amp; sound events</h2><a class="muted" href="ambiente.html">View environment</a></div><div class="grid stats" id="sound-events"><div class="card"><h3>Falls</h3><div class="metric" id="ev-quedas">0</div></div><div class="card"><h3>Shouts</h3><div class="metric" id="ev-gritos">0</div></div><div class="card"><h3>Movements</h3><div class="metric" id="ev-movimentos">0</div></div><div class="card"><h3>Loud sounds</h3><div class="metric" id="ev-sons">0</div></div></div></section><div class="grid split"><section class="card"><div class="section-title"><h2>Recent activity</h2><a class="muted" href="chat.html">View conversations</a></div><div class="timeline" id="timeline"><div class="empty">Loading today's activity.</div></div></section><section class="card"><div class="section-title"><h2>Next care task</h2><a class="muted" href="tasks.html">View routine</a></div><div id="next-care"><div class="empty">Loading routine.</div></div></section></div>`);try{const [messages,tasks]=await Promise.all([req(`/chat/${IDOSO_ID}/mensagens?limite=8`),req(`/tasks/${IDOSO_ID}`)]);const s=messages.estatisticas||{};document.querySelector('#stat-interactions').textContent=s.total_mensagens||0;document.querySelector('#stat-memories').textContent=s.total_memorias||0;document.querySelector('#stat-alerts').textContent=s.total_emergencias||0;const entries=(messages.mensagens||[]).slice(0,5);document.querySelector('#timeline').innerHTML=entries.length?entries.map(m=>`<div class="timeline-item"><span class="time">${date(m.timestamp).split(', ').pop()}</span><div><span class="item-title">${m.autor==='libero'?'Libero responded to a conversation':m.autor==='idoso'?'A conversation was recorded':'Family care'}</span><br><span class="muted">${esc(m.texto).slice(0,108)}</span></div></div>`).join(''):'<div class="empty">No moments have been recorded today.</div>';const next=(tasks.tasks||[]).filter(t=>t.status==='pendente').sort((a,b)=>a.hora.localeCompare(b.hora))[0];document.querySelector('#next-care').innerHTML=next?`<div class="notice"><strong>${esc(next.hora)} · ${esc(next.titulo)}</strong><br>This item is in the routine; automatic reminders are not connected yet.</div>`:'<div class="empty">No pending care tasks.</div>';try{const ev=await req(`/eventos/${IDOSO_ID}/resumo`);const r=ev.resumo||{};const q=document.querySelector('#ev-quedas');if(q)q.textContent=r.quedas||0;const g=document.querySelector('#ev-gritos');if(g)g.textContent=r.gritos||0;const m=document.querySelector('#ev-movimentos');if(m)m.textContent=r.movimentos||0;const s=document.querySelector('#ev-sons');if(s)s.textContent=r.sons_altos||0}catch(e){}}catch(e){toast(e.message)}}
async function tasks(){shell('tasks.html',`<div class="hero"><div><div class="eyebrow">Care routine</div><h1>A lighter day.</h1><p>Medication, meals, water, and small rituals in one place.</p></div></div><section class="card"><div class="form-grid"><input id="task-title" class="field" placeholder="e.g. Blood pressure medication"><input id="task-hour" class="field" type="time" value="08:00"><select id="task-type" class="field"><option value="remedio">Medication</option><option value="agua">Water</option><option value="refeicao">Meal</option><option value="atividade">Activity</option><option value="outro">Other</option></select><button class="primary" onclick="addTask()">Add</button></div></section><div class="section-title"><h2>Today</h2><span class="muted" id="task-summary"></span></div><section class="card"><div id="task-list"><div class="empty">Loading routine.</div></div></section>`);loadTasks()}
async function loadTasks(){try{const {tasks=[]}=await req(`/tasks/${IDOSO_ID}`);tasks.sort((a,b)=>a.hora.localeCompare(b.hora));document.querySelector('#task-summary').textContent=`${tasks.filter(t=>t.status==='feito').length} of ${tasks.length} completed`;document.querySelector('#task-list').innerHTML=tasks.length?tasks.map(t=>`<div class="task-row ${t.status==='feito'?'done':''}"><span class="hour">${esc(t.hora||'—')}</span><div><strong>${esc(t.titulo)}</strong><small>${esc(({remedio:'Medication',agua:'Water',refeicao:'Meal',atividade:'Activity',outro:'Other'})[t.tipo]||t.tipo)}</small></div><span class="tag ${t.status==='feito'?'ok':t.status==='ignorado'?'alert':'warn'}">${t.status==='feito'?'Completed':t.status==='ignorado'?'Skipped':'Pending'}</span><button class="quiet" onclick="toggleTask('${esc(t.id)}','${t.status}')">${t.status==='feito'?'Reopen':'Complete'}</button></div>`).join(''):'<div class="empty">Add a care task to get started.</div>'}catch(e){toast(e.message)}}
async function addTask(){const titulo=document.querySelector('#task-title').value.trim();if(!titulo)return toast('Enter a care task name.');try{await req(`/tasks/${IDOSO_ID}`,{method:'POST',body:JSON.stringify({titulo,hora:document.querySelector('#task-hour').value,tipo:document.querySelector('#task-type').value})});document.querySelector('#task-title').value='';toast('Care task added to the routine.');loadTasks()}catch(e){toast(e.message)}}async function toggleTask(id,status){try{await req(`/tasks/${IDOSO_ID}/${id}`,{method:'PUT',body:JSON.stringify({status:status==='feito'?'pendente':'feito'})});loadTasks()}catch(e){toast(e.message)}}
async function chat(){
  shell('chat.html',`<div class="hero"><div><div class="eyebrow">Caring conversations</div><h1>Stay informed without intruding.</h1><p>Send a message to Libero and follow the conversation here.</p></div><button class="quiet" onclick="abrirModoTV()">Open care screen</button></div><div id="chat-react-root"><section class="card"><div class="empty">Loading conversations…</div></section></div>`);
  clearInterval(window._chatRefreshInterval);
  try {
    const bridge=await carregarAvatarBundle();
    const container=document.querySelector('#chat-react-root');
    if(container)bridge.mountChat(container,IDOSO_ID,setAvatarEstado,USER);
  } catch(e) {
    const container=document.querySelector('#chat-react-root');
    if(container)container.id='chat-container';
    toast('Using the compatible chat view: '+e.message);
    loadChat();
    window._chatRefreshInterval=setInterval(()=>{
      if(document.querySelector('#chat-container')&&!document.hidden)loadChat(true);
    },15000);
  }
}
async function memorias(){
  shell('memorias.html',`<div class="hero"><div><div class="eyebrow">Family memories</div><h1>Stories that stay close.</h1><p>Personal stories saved from conversations and available to Libero for later context.</p></div></div><section id="memory-list" class="grid"><div class="empty">Loading saved stories.</div></section>`);
  try{
    const {memorias:items=[]}=await req(`/chat/${IDOSO_ID}/memorias`);
    const container=document.querySelector('#memory-list');
    container.innerHTML=items.length?[...items].reverse().map(m=>{
      const original=String(m.texto_original||'');
      const summary=String(m.resumo||original);
      const people=Array.isArray(m.pessoas)?m.pessoas.filter(Boolean):[];
      const tags=Array.isArray(m.tags)?m.tags.filter(Boolean):[];
      return `<article class="card memory-card"><span class="eyebrow">${date(m.timestamp)}</span><h3>${esc(m.titulo||'A story remembered')}</h3><p>${esc(summary)}</p>${original&&original!==summary?`<details><summary>Original story</summary><p>${esc(original)}</p></details>`:''}${people.length?`<p class="muted">People: ${people.map(esc).join(', ')}</p>`:''}${tags.length?`<p class="muted">${tags.map(esc).join(' · ')}</p>`:''}</article>`;
    }).join(''):'<div class="empty">No stories have been saved yet. A personal story shared in a conversation may appear here.</div>';
  }catch(e){
    document.querySelector('#memory-list').innerHTML='<div class="empty">Saved stories could not be loaded. Check the connection and try again.</div>';
    toast(e.message);
  }
}
async function alertas(){
  shell('alertas.html',`<div class="hero"><div><div class="eyebrow">Alerts</div><h1>What needed attention.</h1><p>Recorded events and their status. External actions are not executed automatically.</p></div></div><section id="alert-list" class="grid"><div class="empty">Loading alerts.</div></section>`);
  try{
    const {emergencias=[]}=await req(`/chat/${IDOSO_ID}/emergencias`);
    document.querySelector('#alert-list').innerHTML=emergencias.length?[...emergencias].reverse().map(event=>`<article class="card"><div class="list-row"><div><span class="tag alert">Recorded event</span><strong>${esc(event.metadata?.titulo||event.tipo||'Safety event')}</strong><small>${date(event.timestamp)} · Suggestions do not contact emergency services.</small></div><a class="quiet" href="ambiente.html">View environment</a></div><p class="muted">${esc(event.texto||'')}</p></article>`).join(''):'<div class="card"><div class="notice"><strong>No alerts recorded.</strong><br>This does not confirm that sensors are active or that no event occurred.</div></div>';
  }catch(e){document.querySelector('#alert-list').innerHTML='<div class="empty">Alerts could not be loaded. Check the API connection.</div>';toast(e.message)}
}
async function ambiente(){
  shell('ambiente.html',`<div class="hero"><div><div class="eyebrow">Environment &amp; privacy</div><h1>Check sensor status.</h1><p>The camera preview stays open while you move between pages. Hiding the preview does not stop edge capture.</p></div></div><div class="grid split"><section><div class="camera" id="camera-frame"><div class="camera-message"><strong>Preview closed</strong><p>Open the stream only when consent is active.</p></div></div><div class="camera-controls"><button class="primary" onclick="startCamera()">Open camera preview</button><button class="quiet" onclick="stopCamera()">Hide preview</button></div></section><section class="card"><h2>Live status</h2><div class="list"><div class="list-row"><span>Edge service</span><span id="edge-state" class="tag warn">Checking</span></div><div class="list-row"><span>Microphone</span><span id="audio-state" class="tag warn">Checking</span></div><div class="list-row"><span>Camera</span><span id="camera-state" class="tag warn">Checking</span></div><div class="list-row"><span>Transcribed phrases</span><span id="audio-count" class="muted">—</span></div><div class="list-row"><span>Latest camera frame</span><span id="frame-state" class="muted">Checking</span></div></div><p id="edge-error" class="muted" role="status"></p><div class="notice" style="margin-top:16px"><strong>Prototype limitation</strong><br>Events and alerts are experimental. Libero does not guarantee continuous monitoring or emergency response.</div></section></div>`);
  if(cameraPreviewRequested())await startCamera();
  await atualizarStatusEdge();
  if(window._edgeStatusInterval)clearInterval(window._edgeStatusInterval);
  window._edgeStatusInterval=setInterval(atualizarStatusEdge,5000);
}
async function buscarStatusEdge(){const r=await fetch(`${EDGE_URL}/status`,{cache:'no-store'});if(!r.ok)throw new Error(`Edge returned HTTP ${r.status}`);return r.json()}async function atualizarStatusEdge(){try{const s=await buscarStatusEdge(),audio=s.listener||{},camera=s.camera||{};const edge=document.querySelector('#edge-state'),mic=document.querySelector('#audio-state'),cam=document.querySelector('#camera-state'),count=document.querySelector('#audio-count'),frame=document.querySelector('#frame-state'),error=document.querySelector('#edge-error');if(!edge)return;edge.textContent=s.edge_running?'Connected':'Stopped';edge.className=`tag ${s.edge_running?'ok':'warn'}`;const micState=audio.estado_microfone||(audio.rodando?'ouvindo':'parado');mic.textContent=micState==='ouvindo'?'Active':micState==='inicializando'?'Starting':micState==='travado'?'Initialization stalled':micState==='erro'?'Unavailable':'Stopped';mic.className=`tag ${micState==='ouvindo'?'ok':micState==='travado'||micState==='erro'?'alert':'warn'}`;count.textContent=audio.frases_processadas??0;cam.textContent=camera.ativa?(camera.consentimento?'Active with consent':'Active'):(camera.consentimento?'Consented, no image':'Disabled');cam.className=`tag ${camera.ativa?'ok':'warn'}`;frame.textContent=s.camera_frame_atual?'Current':`No recent frame${s.camera_frame_age_seconds!=null?' · '+s.camera_frame_age_seconds+'s':''}`;if(error)error.textContent=audio.ultimo_erro||''}catch(e){const edge=document.querySelector('#edge-state'),mic=document.querySelector('#audio-state'),cam=document.querySelector('#camera-state'),error=document.querySelector('#edge-error');if(edge){edge.textContent='Unavailable';edge.className='tag alert'}if(mic){mic.textContent='Could not verify';mic.className='tag warn'}if(cam){cam.textContent='Could not verify';cam.className='tag warn'}if(error)error.textContent='Start the edge process and confirm LIBERO_EDGE_ALLOWED_ORIGINS for this origin.'}}async function startCamera(){try{const s=await buscarStatusEdge();if(!s.camera?.ativa){toast('The edge camera is not active. Check consent and the edge process.');return}sessionStorage.setItem(CAMERA_PREVIEW_KEY,'1');const frame=document.querySelector('#camera-frame');if(frame)frame.innerHTML=`<img src="${EDGE_URL}/stream" alt="Edge camera stream" style="width:100%;height:100%;object-fit:cover;border-radius:12px" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'camera-message',innerHTML:'<strong>Stream unavailable</strong><p>Check the edge process and consent.</p>'}))">`;else renderCameraPreview();toast('Preview opened; it will stay visible as you move between pages. Edge capture continues in the background.')}catch(e){toast('Could not open the camera preview: '+e.message)}}function stopCamera(){sessionStorage.removeItem(CAMERA_PREVIEW_KEY);document.getElementById('camera-floating-preview')?.remove();const frame=document.querySelector('#camera-frame');if(frame)frame.innerHTML='<div class="camera-message"><strong>Preview hidden</strong><p>Edge capture continues according to device settings.</p></div>';toast('Preview hidden; edge capture continues.')}
function rede(){shell('rede.html',`<div class="hero"><div><div class="eyebrow">Care network</div><h1>Everyone who cares, in sync.</h1><p>Choose who receives each alert and who can help in each situation.</p></div><button class="primary" onclick="addPerson()">Add person</button></div><section class="card"><h2>People in your network</h2><div id="people" class="people"></div></section><section class="card" style="margin-top:16px"><h2>Response plan</h2><p class="muted">This response plan is a local demo. Invites, alerts, and escalation are not connected yet.</p><div class="notice">1. Ana, daughter · 2. Carlos, caregiver · 3. Helena, trusted neighbor</div></section>`);renderPeople()}function people(){return JSON.parse(localStorage.getItem('libero-care-network')||'[{"name":"Ana Rivera","role":"Daughter and primary contact","initial":"A","enabled":true},{"name":"Carlos Smith","role":"Caregiver","initial":"C","enabled":true},{"name":"Dr. Helen Lima","role":"Doctor","initial":"H","enabled":false}]')}function renderPeople(){const list=people();document.querySelector('#people').innerHTML=list.map((p,i)=>`<div class="person"><div class="avatar">${esc(p.initial)}</div><div class="grow"><strong>${esc(p.name)}</strong><div class="muted">${esc(p.role)}</div></div><span class="muted">Receives alerts</span><button class="switch ${p.enabled?'on':''}" aria-label="Toggle alerts for ${esc(p.name)}" onclick="togglePerson(${i})"></button></div>`).join('')}function togglePerson(i){const l=people();l[i].enabled=!l[i].enabled;localStorage.setItem('libero-care-network',JSON.stringify(l));renderPeople()}function addPerson(){toast('This button could invite someone by email or WhatsApp in a future version.');}
function perfil(){shell('perfil.html',`<div class="hero"><div><div class="eyebrow">Care profile</div><h1>What makes her feel at home.</h1><p>Demo form: only the preferred name is saved in this browser; the other fields do not guide the agent yet.</p></div><button class="primary" onclick="saveProfile()">Save preferences</button></div><section class="card"><div class="grid profile-grid"><label>Preferred name<input id="preferred-name" class="field" value="Maria"></label><label>Comforting routine<input class="field" value="Morning coffee with music"></label><label>Important people<input class="field" value="Ana, Carlos, grandchildren"></label><label>Favorite music and topics<input class="field" value="Samba, stories from her youth"></label><label>What helps her feel calm<textarea class="field" rows="3">Speak slowly, validate the feeling, and offer a happy memory.</textarea></label><label>Plan for a crisis<textarea class="field" rows="3">Offer comfort, remove risks, and notify Ana if agitation continues.</textarea></label></div></section><section class="card" style="margin-top:16px"><h2>How Libero uses this information</h2><p class="muted">Only the preferred name is saved. The other fields are not used by the agent or to create reminders.</p></section>`)}function saveProfile(){localStorage.setItem('libero-preferred-name',document.querySelector('#preferred-name').value);toast('Only the preferred name is saved on this device; the other fields are not saved.');}
async function bootElder(){
  try {
    USER=await req('/auth/me');
    IDOSO_ID=USER.idoso_id&&USER.idoso_id!=='*'?USER.idoso_id:'dona-maria';
    conectarWebSocket();
    elder();
  } catch(e) {
    sessionStorage.setItem('libero-return-to',location.href);
    loginScreen();
  }
}
function elder(){
  document.body.innerHTML=`<main class="care-screen"><header class="care-screen-top"><a href="dashboard.html" class="care-screen-brand" aria-label="Libero home"><img src="assets/photon-knot.svg" alt="Libero"></a></header><section class="care-screen-center"><div id="care-screen-avatar"><button type="button" class="care-character" data-state="idle" onclick="cumprimentarCompanion()" aria-label="Toque para ouvir uma mensagem do Libero"><span class="care-character-aura" aria-hidden="true"></span><img src="assets/companion-avatar.svg" alt=""><span class="care-character-ondas" aria-hidden="true"><i></i><i></i><i></i></span></button><p class="care-character-prompt">Toque no Libero para conversar</p></div></section><footer class="care-screen-controls"><div class="care-screen-buttons"><button class="primary" onclick="ativarTelaCheia()">Full Screen</button><button class="quiet" onclick="sairTelaCheia()">Exit</button><button class="quiet" onclick="location.href='dashboard.html'">Back to Dashboard</button></div></footer></main>`;
  if(cameraPreviewRequested())renderCameraPreview();
  carregarMensagensTela(true);
  if(window._careScreenInterval)clearInterval(window._careScreenInterval);
  window._careScreenInterval=setInterval(()=>{if(!document.hidden)carregarMensagensTela(false)},15000);
}

function updateCareScreenAvatar(){
  document.querySelector('#care-screen-avatar .care-character')?.setAttribute('data-state',avatarState);
}
function cumprimentarCompanion(){
  if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window)){toast('A fala não está disponível neste navegador.');return}
  const fala=new SpeechSynthesisUtterance('Oi, que bom ter você aqui. Quer conversar comigo?');
  fala.lang='pt-BR';
  fala.onstart=()=>setAvatarEstado('falando',false);
  fala.onend=()=>setAvatarEstado('idle',false);
  fala.onerror=()=>setAvatarEstado('idle',false);
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(fala);
}
async function carregarMensagensTela(inicial=false){
  try {
    const dados=await req(`/chat/${IDOSO_ID}/mensagens?limite=3`);
    const atual=(dados.mensagens||[])[0];
    if(!atual)return;
    if(inicial){window._careScreenLastMessage=atual.id;return}
    if(atual.id===window._careScreenLastMessage)return;
    window._careScreenLastMessage=atual.id;
    if(atual.autor==='cuidador')setAvatarEstado('pensando');
    if(atual.autor==='libero'&&atual.texto){
      setAvatarEstado('falando');
      if('speechSynthesis' in window&&'SpeechSynthesisUtterance' in window){
        window.speechSynthesis.cancel();
        const fala=new SpeechSynthesisUtterance(atual.texto);
        fala.lang=idiomaDaMensagem(atual.texto);
        fala.onend=()=>setAvatarEstado('idle');
        fala.onerror=()=>setAvatarEstado('idle');
        window.speechSynthesis.speak(fala);
      } else setAvatarEstado('idle');
    }
  } catch(e) {
    if(e.status===401){window.dispatchEvent(new Event('libero:unauthorized'));return}
    const status=document.querySelector('#care-screen-connection');
    if(status)status.textContent='Reconnecting to Libero…';
  }
}
async function ativarTelaCheia(){
  try {
    if('speechSynthesis' in window)window.speechSynthesis.resume();
    if(!document.fullscreenElement)await document.documentElement.requestFullscreen();
    document.querySelector('.care-screen').classList.add('fullscreen-active');
  } catch(e) { toast('Fullscreen is not available in this browser.'); }
}
async function sairTelaCheia(){if(document.fullscreenElement)await document.exitFullscreen();document.querySelector('.care-screen')?.classList.remove('fullscreen-active')}
function elderReply(text){const e=document.querySelector('#elder-response');e.hidden=false;e.textContent=text}
window.addEventListener('DOMContentLoaded',()=>{if(document.body.dataset.public==='elder'){bootElder();return}boot().finally(mountReactBackground)});
window.addEventListener('libero:unauthorized',()=>{
  if(document.body.dataset.public==='elder'){
    sessionStorage.setItem('libero-return-to',location.href);
    loginScreen();
  } else location.href='dashboard.html';
});
document.addEventListener('fullscreenchange',()=>document.querySelector('.care-screen')?.classList.toggle('fullscreen-active',Boolean(document.fullscreenElement)));


// ============================================================
// CHAT SIMPLES (sem React)
// ============================================================

let chatMessages = [];
let chatScrollPosition = 0;
let chatOffset = 50;
let chatHasOlder = false;
let chatError = '';
let chatLoadingOlder = false;

async function loadChat(silent = false) {
  if (chatLoadingOlder) return;
  try {
    const dados = await req(`/chat/${IDOSO_ID}/mensagens?limite=50`);
    const novas = [...(dados.mensagens || [])].reverse();
    const haviaErro = Boolean(chatError);
    const mensagensAnteriores = new Set(chatMessages.map(m => m.id));
    const adicionadas = novas.filter(m => !mensagensAnteriores.has(m.id));
    if (chatMessages.length) chatOffset += adicionadas.length;
    chatMessages = [...new Map([...chatMessages, ...novas].map(m => [m.id, m])).values()]
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    chatHasOlder = novas.length === 50;
    chatError = '';
    if (adicionadas.length || !silent || haviaErro) renderChat();
  } catch (e) {
    const erroAnterior = chatError;
    chatError = 'Could not load conversations: ' + e.message;
    if (!silent || !chatMessages.length || chatError !== erroAnterior) renderChat();
  }
}

async function loadOlderChat() {
  const button = document.querySelector('#chat-load-older');
  if (!button || button.disabled || chatLoadingOlder || !chatHasOlder) return;
  const list = document.querySelector('.chat-messages');
  const scrollTop = list?.scrollTop || 0;
  const scrollHeight = list?.scrollHeight || 0;
  chatLoadingOlder = true;
  button.disabled = true;
  button.textContent = 'Loading…';
  try {
    const dados = await req(`/chat/${IDOSO_ID}/mensagens?limite=50&offset=${chatOffset}`);
    const anteriores = [...(dados.mensagens || [])].reverse();
    chatMessages = [...new Map([...chatMessages, ...anteriores].map(m => [m.id, m])).values()]
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    chatOffset += anteriores.length;
    chatHasOlder = anteriores.length === 50;
    chatError = '';
    renderChat();
    const novaLista = document.querySelector('.chat-messages');
    if (novaLista) novaLista.scrollTop = scrollTop + novaLista.scrollHeight - scrollHeight;
  } catch (e) {
    chatError = 'Could not load older messages: ' + e.message;
    renderChat();
  } finally {
    chatLoadingOlder = false;
  }
}

function formatDate(timestamp) {
  const date = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
}

function renderChat() {
  const container = document.querySelector('#chat-container');
  if (!container) return;

  const messagesDiv = container.querySelector('.chat-messages');
  const wasNearBottom = !messagesDiv ||
    messagesDiv.scrollHeight - messagesDiv.scrollTop - messagesDiv.clientHeight < 80;
  const previousInput = container.querySelector('#chat-input');
  const previousText = previousInput?.value || '';
  const inputHadFocus = document.activeElement === previousInput;
  if (messagesDiv) chatScrollPosition = messagesDiv.scrollTop;

  if (chatMessages.length === 0) {
    container.innerHTML = `<section class="card">${chatError ? `<p class="chat-load-error" role="alert">${esc(chatError)} <button class="quiet" type="button" onclick="loadChat()">Try again</button></p>` : ''}<div class="chat-messages"><div class="empty">${chatError ? 'Your saved conversation is unavailable right now.' : 'No conversations yet. Send a message to start talking with Libero.'}</div></div><form class="chat-composer" onsubmit="sendChatMessage(event)"><input type="text" id="chat-input" class="field" placeholder="Write a message to Libero..." maxlength="2000" /><button type="submit" class="primary" id="chat-send">Send</button></form></section>`;
    return;
  }

  // Agrupar mensagens por data
  const groupedMessages = {};
  chatMessages.forEach(m => {
    const dateKey = formatDate(m.timestamp);
    if (!groupedMessages[dateKey]) {
      groupedMessages[dateKey] = [];
    }
    groupedMessages[dateKey].push(m);
  });

  // Renderizar com separadores de data
  let html = '';
  Object.keys(groupedMessages).forEach(dateKey => {
    html += `<div class="chat-day-divider">${dateKey}</div>`;
    groupedMessages[dateKey].forEach(m => {
      const nome = m.autor === 'idoso'
        ? localStorage.getItem('libero-preferred-name') || 'Maria'
        : m.autor === 'libero' ? 'Libero' : displayUserName();
      html += `
        <div class="chat-bubble ${m.autor === 'idoso' ? 'idoso' : m.autor === 'libero' ? 'libero' : 'cuidador'}">
          <div class="chat-avatar">${esc(nome.slice(0, 1).toUpperCase())}</div>
          <div class="chat-content">
            <div class="chat-name">${esc(nome)}</div>
            <div class="chat-text">${esc(m.texto)}</div>
          </div>
        </div>
      `;
    });
  });

  container.innerHTML = `
    <section class="card">
      ${chatError ? `<p class="chat-load-error" role="alert">${esc(chatError)} <button class="quiet" type="button" onclick="loadChat()">Try again</button></p>` : ''}
      ${chatHasOlder ? '<button class="quiet chat-load-older" id="chat-load-older" type="button" onclick="loadOlderChat()">Load older messages</button>' : ''}
      <div class="chat-messages">${html}</div>
      <form class="chat-composer" onsubmit="sendChatMessage(event)">
        <input type="text" id="chat-input" class="field" placeholder="Write a message to Libero..." maxlength="2000" value="${esc(previousText)}" />
        <button type="submit" class="primary" id="chat-send">Send</button>
      </form>
    </section>
  `;

  // Restaurar posição do scroll ou ir para o fundo se for primeira carga
  const newMessagesDiv = container.querySelector('.chat-messages');
  if (newMessagesDiv) {
    newMessagesDiv.scrollTop = wasNearBottom
      ? newMessagesDiv.scrollHeight
      : chatScrollPosition;
  }
  const newInput = container.querySelector('#chat-input');
  if (newInput && inputHadFocus) {
    newInput.focus();
    newInput.setSelectionRange(previousText.length, previousText.length);
  }
}

async function sendChatMessage(e) {
  e.preventDefault();
  const input = document.querySelector('#chat-input');
  const btn = document.querySelector('#chat-send');
  const texto = input.value.trim();

  if (!texto) return;

  btn.disabled = true;
  btn.textContent = 'Sending...';

  try {
    const resposta = await req(`/chat/${IDOSO_ID}/mensagem`, {
      method: 'POST',
      body: JSON.stringify({ texto })
    });
    input.value = '';
    await loadChat();
    speakResponse(resposta.resposta, resposta.idioma || idiomaDaMensagem(texto));
  } catch (err) {
    toast('Could not send message: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send';
  }
}

// Auto-refresh chat every 5 seconds (opcional - removido para evitar pulos)
// setInterval(() => {
//   if (document.querySelector('#chat-container')) {
//     loadChat();
//   }
// }, 5000);


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
    const estado = s.listener?.estado_microfone;
    const ativo = estado ? estado === 'ouvindo' : Boolean(s.listener?.rodando);
    if (ativo && !['falando', 'pensando'].includes(avatarState)) setAvatarEstado('ouvindo');
    else if (!ativo && avatarState === 'ouvindo') setAvatarEstado('idle');
    if (badge) {
      badge.className = `tag ${ativo ? 'ok' : estado === 'travado' || estado === 'erro' ? 'alert' : 'warn'}`;
      badge.title = ativo
        ? `Microphone listening · ${s.listener.frases_processadas || 0} phrases transcribed`
        : estado === 'inicializando'
          ? 'Microphone starting'
          : estado === 'travado' || estado === 'erro'
            ? `Microphone unavailable · ${s.listener.ultimo_erro || 'check the audio device'}`
            : 'Edge unavailable or microphone stopped';
    }
  } catch (e) {
    const badge = document.getElementById('mic-badge');
    if (badge) { badge.className = 'tag alert'; badge.title = 'Could not check the actual edge status'; }
  }
}

// Refresh every 5 seconds
setInterval(()=>{
  if(!document.hidden&&document.getElementById('mic-badge'))atualizarBadgeMic();
},30000);

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
      const status=document.querySelector('#care-screen-connection');
      if(status)status.textContent='Connected to this Libero account';
    };
    
    wsNotif.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.tipo === 'emergencia') {
          mostrarEmergencia(msg);
        }
        if (msg.tipo === 'mensagem_cliente' && msg.payload?.tipo === 'libero_estado_avatar') {
          setAvatarEstado(msg.payload.estado,false);
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

// ============================================================
// CONVERSATIONS (message bubbles)
// ============================================================


// ============================================================
// AVATAR DO LIBERO (VISUAL)
// ============================================================
function carregarAvatarBundle() {
  if (window.LiberoAvatar) return Promise.resolve(window.LiberoAvatar);
  if (avatarBundlePromise) return avatarBundlePromise;
  avatarBundlePromise = new Promise((resolve,reject) => {
    const script=document.createElement('script');
    script.src='/assets/libero-avatar/libero-avatar.js';
    script.onload=()=>window.LiberoAvatar ? resolve(window.LiberoAvatar) : reject(new Error('Avatar bundle loaded without its API'));
    script.onerror=()=>reject(new Error('Avatar bundle failed to load'));
    document.head.appendChild(script);
  });
  return avatarBundlePromise;
}

function setAvatarEstado(estado,anunciar=true) {
  if(!['idle','ouvindo','pensando','falando'].includes(estado))estado='idle';
  const mudou=avatarState!==estado;
  avatarState=estado;
  window.LiberoAvatar?.setState(estado);
  updateCareScreenAvatar();
  if(anunciar&&mudou&&wsNotif?.readyState===WebSocket.OPEN){
    wsNotif.send(JSON.stringify({tipo:'libero_estado_avatar',estado}));
  }
}
