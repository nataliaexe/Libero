const API_URL=window.LIBERO_API_URL||((window.location.protocol==='file:'||(['3000','5500'].includes(window.location.port)&&['localhost','127.0.0.1'].includes(window.location.hostname))?`http://${window.location.hostname||'localhost'}:8080`:window.location.origin));
let USER=null;let IDOSO_ID='dona-maria';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=s=>s?new Date(s).toLocaleString('pt-BR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}):'agora';
function toast(text){const e=document.querySelector('.toast');if(!e)return;e.textContent=text;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),3200)}
async function req(path,options={}){const r=await fetch(API_URL+path,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});const j=await r.json();if(!r.ok){const e=new Error(j.error||'Não foi possível concluir esta ação.');e.status=r.status;throw e}return j}
function nav(active){const items=[['dashboard.html','Hoje'],['alertas.html','Alertas'],['chat.html','Conversas'],['memorias.html','Memórias'],['rede.html','Rede de cuidado'],['perfil.html','Perfil de cuidado'],['ambiente.html','Ambiente']];return `<aside class="nav">${items.map(([h,n])=>`<a class="${active===h?'active':''}" href="${h}">${n}</a>`).join('')}<div class="privacy"><strong>Privacidade primeiro</strong>Áudio pode ser enviado ao serviço de transcrição configurado. A imagem é exibida sob demanda.</div></aside>`}
function shell(active,content){document.body.innerHTML=`<div class="orb one"></div><div class="orb two"></div><main class="shell"><header class="topbar"><a class="brand" href="dashboard.html"><svg class="brand-icon" width="40" height="40" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#7c5cbf"/><stop offset="100%" style="stop-color:#e94560"/></linearGradient></defs><rect x="10" y="10" width="100" height="100" rx="28" fill="url(#grad1)"/><path d="M20 60 L35 60 L42 42 L52 78 L60 50 L68 68 L75 60 L100 60" stroke="#f5f0e8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg><span><strong>LIBERO</strong><small>Cuidado que permanece</small></span></a><div class="user-tools"><span id="mic-badge" class="tag warn" style="margin-right:8px" title="Microfone ambiente">🎤</span><span>${esc(USER?.nome||'Família')}</span><div class="avatar">${esc((USER?.nome||'F').slice(0,1))}</div><button class="logout" onclick="logout()">Sair</button></div></header><div class="layout">${nav(active)}<section class="page">${content}</section></div></main><div class="toast" aria-live="polite"></div>`}
async function boot(){try{USER=await req('/auth/me');IDOSO_ID=USER.idoso_id&&USER.idoso_id!=='*'?USER.idoso_id:'dona-maria';const page=document.body.dataset.page;({hoje,tasks,chat,memorias,alertas,ambiente,rede,perfil}[page]||hoje)()}catch(e){if(document.body.dataset.page==='hoje')loginScreen();else location.href='dashboard.html'}}
function loginScreen(){document.body.innerHTML=`<div class="orb one"></div><div class="orb two"></div><main class="elder-page" style="max-width:460px;padding-top:12vh"><header class="elder-head"><svg class="login-icon" width="80" height="80" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#7c5cbf"/><stop offset="100%" style="stop-color:#e94560"/></linearGradient></defs><rect x="10" y="10" width="100" height="100" rx="28" fill="url(#grad2)"/><path d="M20 60 L35 60 L42 42 L52 78 L60 50 L68 68 L75 60 L100 60" stroke="#f5f0e8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg><div class="eyebrow">CUIDADO QUE PERMANECE</div><h1>Bem-vinda à rede de cuidado.</h1><p class="muted">Entre para acompanhar com clareza e presença.</p></header><section class="card" style="text-align:left;margin-top:28px"><label class="muted">E-mail<input id="login-email" class="field" type="email" autocomplete="username" placeholder="voce@email.com"></label><br><label class="muted">Senha<input id="login-password" class="field" type="password" autocomplete="current-password" placeholder="Sua senha"></label><p id="login-error" class="muted" style="color:var(--danger)"></p><button class="primary" style="width:100%" onclick="login()">Entrar no Libero</button></section></main>`}async function login(){const email=document.querySelector('#login-email').value.trim(),senha=document.querySelector('#login-password').value,err=document.querySelector('#login-error');if(!email||!senha){err.textContent='Preencha seu e-mail e sua senha.';return}try{USER=await req('/auth/login',{method:'POST',body:JSON.stringify({email,senha})});location.href='dashboard.html'}catch(e){err.textContent=e.message}}
async function logout(){try{await req('/auth/logout',{method:'POST'})}catch(e){}location.href='dashboard.html'}
async function hoje(){shell('dashboard.html',`<div class="hero"><div><div class="eyebrow">Visão da família</div><h1>Bom dia, ${esc((USER?.idoso_id||'Dona Maria').replace(/-/g,' '))}.</h1><p>Uma visão tranquila do dia, para você cuidar com mais presença e menos preocupação.</p></div><a class="primary" href="chat.html">Acompanhar conversa</a></div><section class="status-card"><div class="eyebrow">Agora</div><h2 id="current-state">Estado do monitoramento não verificado.</h2><div class="status-row"><span class="dot"></span><span id="state-detail">O histórico não confirma que os sensores estejam ativos.</span></div></section><section class="grid stats"><div class="card"><h3>Interações hoje</h3><div class="metric" id="stat-interactions">—</div><p class="muted">momentos de conversa e acolhimento</p></div><div class="card"><h3>Memórias guardadas</h3><div class="metric" id="stat-memories">—</div><p class="muted">histórias que viram legado</p></div><div class="card"><h3>Alertas recentes</h3><div class="metric" id="stat-alerts">—</div><p class="muted">eventos que pediram atenção</p></div></section><section class="card" style="margin-top:16px"><div class="section-title"><h2>Eventos sonoros</h2><a class="muted" href="ambiente.html">Ver ambiente</a></div><div class="grid stats" id="sound-events"><div class="card"><h3>Quedas</h3><div class="metric" id="ev-quedas">0</div></div><div class="card"><h3>Gritos</h3><div class="metric" id="ev-gritos">0</div></div><div class="card"><h3>Choros</h3><div class="metric" id="ev-choros">0</div></div><div class="card"><h3>Sons altos</h3><div class="metric" id="ev-sons">0</div></div></div></section><div class="grid split"><section class="card"><div class="section-title"><h2>Como foi o dia</h2><a class="muted" href="chat.html">Ver conversas</a></div><div class="timeline" id="timeline"><div class="empty">Carregando os acontecimentos de hoje.</div></div></section><section class="card"><div class="section-title"><h2>Próximo cuidado</h2><a class="muted" href="tasks.html">Ver rotina</a></div><div id="next-care"><div class="empty">Carregando rotina.</div></div></section></div>`);try{const [messages,tasks]=await Promise.all([req(`/chat/${IDOSO_ID}/mensagens?limite=8`),req(`/tasks/${IDOSO_ID}`)]);const s=messages.estatisticas||{};document.querySelector('#stat-interactions').textContent=s.total_mensagens||0;document.querySelector('#stat-memories').textContent=s.total_memorias||0;document.querySelector('#stat-alerts').textContent=s.total_emergencias||0;const entries=(messages.mensagens||[]).slice(0,5);document.querySelector('#timeline').innerHTML=entries.length?entries.map(m=>`<div class="timeline-item"><span class="time">${date(m.timestamp).split(', ').pop()}</span><div><span class="item-title">${m.autor==='libero'?'Libero acolheu uma conversa':m.autor==='idoso'?'Uma conversa foi registrada':'Cuidado da família'}</span><br><span class="muted">${esc(m.texto).slice(0,108)}</span></div></div>`).join(''):'<div class="empty">Ainda não há momentos registrados hoje.</div>';const next=(tasks.tasks||[]).filter(t=>t.status==='pendente').sort((a,b)=>a.hora.localeCompare(b.hora))[0];document.querySelector('#next-care').innerHTML=next?`<div class="notice"><strong>${esc(next.hora)} · ${esc(next.titulo)}</strong><br>O item está na rotina; lembretes automáticos ainda não estão conectados.</div>`:'<div class="empty">Nenhum cuidado pendente por enquanto.</div>';try{const ev=await req(`/eventos/${IDOSO_ID}/resumo`);const r=ev.resumo||{};const q=document.querySelector('#ev-quedas');if(q)q.textContent=r.quedas||0;const g=document.querySelector('#ev-gritos');if(g)g.textContent=r.gritos||0;const c=document.querySelector('#ev-choros');if(c)c.textContent=r.choros||0;const s=document.querySelector('#ev-sons');if(s)s.textContent=r.sons_altos||0}catch(e){}}catch(e){toast(e.message)}}
async function tasks(){shell('tasks.html',`<div class="hero"><div><div class="eyebrow">Rotina de cuidado</div><h1>O dia, com mais leveza.</h1><p>Remédios, refeições, água e pequenos rituais organizados em um só lugar.</p></div></div><section class="card"><div class="form-grid"><input id="task-title" class="field" placeholder="Ex.: Remédio da pressão"><input id="task-hour" class="field" type="time" value="08:00"><select id="task-type" class="field"><option value="remedio">Remédio</option><option value="agua">Água</option><option value="refeicao">Refeição</option><option value="atividade">Atividade</option><option value="outro">Outro</option></select><button class="primary" onclick="addTask()">Adicionar</button></div></section><div class="section-title"><h2>Hoje</h2><span class="muted" id="task-summary"></span></div><section class="card"><div id="task-list"><div class="empty">Carregando rotina.</div></div></section>`);loadTasks()}
async function loadTasks(){try{const {tasks=[]}=await req(`/tasks/${IDOSO_ID}`);tasks.sort((a,b)=>a.hora.localeCompare(b.hora));document.querySelector('#task-summary').textContent=`${tasks.filter(t=>t.status==='feito').length} de ${tasks.length} concluídos`;document.querySelector('#task-list').innerHTML=tasks.length?tasks.map(t=>`<div class="task-row ${t.status==='feito'?'done':''}"><span class="hour">${esc(t.hora||'—')}</span><div><strong>${esc(t.titulo)}</strong><small>${esc(t.tipo)}</small></div><span class="tag ${t.status==='feito'?'ok':t.status==='ignorado'?'alert':'warn'}">${t.status==='feito'?'Concluído':t.status==='ignorado'?'Ignorado':'Pendente'}</span><button class="quiet" onclick="toggleTask('${esc(t.id)}','${t.status}')">${t.status==='feito'?'Reabrir':'Concluir'}</button></div>`).join(''):'<div class="empty">Comece adicionando um cuidado para hoje.</div>'}catch(e){toast(e.message)}}
async function addTask(){const titulo=document.querySelector('#task-title').value.trim();if(!titulo)return toast('Escreva o nome do cuidado.');try{await req(`/tasks/${IDOSO_ID}`,{method:'POST',body:JSON.stringify({titulo,hora:document.querySelector('#task-hour').value,tipo:document.querySelector('#task-type').value})});document.querySelector('#task-title').value='';toast('Cuidado adicionado à rotina.');loadTasks()}catch(e){toast(e.message)}}async function toggleTask(id,status){try{await req(`/tasks/${IDOSO_ID}/${id}`,{method:'PUT',body:JSON.stringify({status:status==='feito'?'pendente':'feito'})});loadTasks()}catch(e){toast(e.message)}}
async function chat(){shell('chat.html',`<div class="hero"><div><div class="eyebrow">Conversas com cuidado</div><h1>Acompanhe sem invadir.</h1><p>Veja o histórico e envie uma mensagem ao Libero. As mensagens aparecem em tempo real.</p></div></div><section class="card"><div id="chat-messages" class="chat-container"><div class="empty-state"><div class="empty-icon">&#128172;</div><div class="empty-title">Carregando conversas</div></div></div><div class="composer" style="margin-top:20px;display:flex;gap:12px"><input id="message-text" class="field" maxlength="2000" placeholder="Ex.: Diga que estou pensando nela hoje" style="flex:1"><button class="primary" onclick="sendMessage()">Enviar carinho</button></div></section>`);loadMessages();if(window._chatInterval)clearInterval(window._chatInterval);window._chatInterval=setInterval(loadMessages,5000)}async function sendMessage(){const el=document.querySelector('#message-text'),texto=el.value.trim();if(!texto)return toast('Escreva uma mensagem antes de enviar.');try{await req(`/chat/${IDOSO_ID}/mensagem`,{method:'POST',body:JSON.stringify({texto})});el.value='';toast('O Libero recebeu seu carinho.');loadMessages()}catch(e){toast(e.message)}}
async function memorias(){shell('memorias.html',`<div class="hero"><div><div class="eyebrow">Museu vivo</div><h1>Histórias que continuam perto.</h1><p>O Libero guarda lembranças compartilhadas em conversas para a família revisitar quando quiser.</p></div></div><section id="memory-list" class="grid"><div class="empty">Carregando memórias.</div></section>`);try{const {memorias=[]}=await req(`/chat/${IDOSO_ID}/memorias`);document.querySelector('#memory-list').innerHTML=memorias.length?[...memorias].reverse().map(m=>`<article class="card memory-card"><span class="eyebrow">${date(m.timestamp)}</span><h3>${esc(m.metadata?.titulo||'Uma história lembrada')}</h3><p>${esc(m.texto)}</p><p class="muted">${esc(m.metadata?.emocao||'Memória registrada durante uma conversa')}</p></article>`).join(''):'<div class="empty">As histórias mais marcantes aparecerão aqui.</div>'}catch(e){toast(e.message)}}
async function alertas(){shell('alertas.html',`<div class="hero"><div><div class="eyebrow">Central de alertas</div><h1>O que precisou de atenção.</h1><p>Alertas explicados com clareza: o que aconteceu, o que o Libero fez e o que ainda precisa de você.</p></div><div class="filter"><button class="active">Todos</button><button>Atenção</button><button>Resolvidos</button></div></div><section id="alert-list" class="grid"><div class="empty">Carregando alertas.</div></section>`);try{const {emergencias=[]}=await req(`/chat/${IDOSO_ID}/emergencias`);document.querySelector('#alert-list').innerHTML=emergencias.length?[...emergencias].reverse().map(e=>`<article class="card"><div class="list-row"><div><span class="tag alert">Atenção</span><strong>${esc(e.metadata?.titulo||'Evento de segurança registrado')}</strong><small>${date(e.timestamp)} · Evento registrado; as ações externas sugeridas não são executadas por esta tela.</small></div><a class="quiet" href="ambiente.html">Ver ambiente</a></div><p class="muted">${esc(e.texto)}</p></article>`).join(''):'<div class="card"><div class="notice"><strong>Nenhum alerta registrado.</strong><br>A ausência de registros não confirma que os sensores estejam ativos ou que nenhum evento tenha ocorrido.</div></div>'}catch(e){toast(e.message)}}
async function ambiente(){shell('ambiente.html',`<div class="hero"><div><div class="eyebrow">Ambiente e privacidade</div><h1>Cuidado atento, com limites claros.</h1><p>Você controla quando a visualização é aberta. A câmera da interface é acionada manualmente; ela não se conecta ao detector edge nesta tela.</p></div></div><div class="grid split"><section><div class="camera" id="camera-frame"><div class="camera-message"><strong>Visualização protegida</strong><p>A imagem aparece somente quando você abre esta visualização. O fluxo de emergência não a abre automaticamente.</p></div></div><div class="camera-controls"><button class="primary" onclick="startCamera()">Abrir visualização</button><button class="quiet" onclick="stopCamera()">Encerrar</button></div><div class="camera-controls" style="margin-top:12px"><button class="primary" id="mic-cuidador-btn" onclick="toggleMicrofone()">Falar com o idoso</button></div></section><section class="card"><h2>Estado do ambiente</h2><div class="list"><div class="list-row"><span>Monitoramento de áudio</span><span id="audio-state" class="tag ok">Verificando</span></div><div class="list-row"><span>Processamento de imagem</span><span class="tag warn">Sob demanda</span></div><div class="list-row"><span>Retenção de vídeo</span><span class="muted">O dashboard não grava o stream</span></div></div><div class="notice" style="margin-top:16px"><strong>Sua privacidade é parte do cuidado.</strong><br>O Libero não transforma a casa em vigilância; ele busca segurança com o mínimo necessário.</div></section></div>`);try{const s=await req('/audio/status');document.querySelector('#audio-state').textContent=s.rodando?'Ativo':'Pausado';document.querySelector('#audio-state').className=`tag ${s.rodando?'ok':'warn'}`}catch(e){toast(e.message)}}async function startCamera(){
  try{
    const EDGE_URL = `http://${window.location.hostname||'localhost'}:8081`;
    document.querySelector('#camera-frame').innerHTML=`<img src="${EDGE_URL}/stream" alt="Visualização do ambiente" style="width:100%;height:100%;object-fit:cover;border-radius:12px" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'camera-message',innerHTML:'<strong>Câmera não conectada</strong><p>Rode:<br><code>LIBERO_CAMERA_CONSENT=true python edge/main.py</code></p>'}))">`;
    toast('Visualização aberta.');
  }catch(e){toast(e.message)}
}
async function stopCamera(){try{await req('/camera/stop',{method:'POST'});document.querySelector('#camera-frame').innerHTML='<div class="camera-message"><strong>Visualização encerrada</strong><p>Nenhuma imagem está sendo exibida.</p></div>';toast('Visualização encerrada.')}catch(e){toast(e.message)}}
function rede(){shell('rede.html',`<div class="hero"><div><div class="eyebrow">Rede de cuidado</div><h1>Todo mundo que cuida, alinhado.</h1><p>Defina quem recebe cada tipo de aviso e deixe claro quem pode ajudar em cada situação.</p></div><button class="primary" onclick="addPerson()">Adicionar pessoa</button></div><section class="card"><h2>Pessoas da rede</h2><div id="people" class="people"></div></section><section class="card" style="margin-top:16px"><h2>Escala de resposta</h2><p class="muted">Esta escala é uma demonstração local. Convites, envio de alertas e escalonamento ainda não estão conectados.</p><div class="notice">1. Ana, filha · 2. Carlos, cuidador · 3. Helena, vizinha de confiança</div></section>`);renderPeople()}function people(){return JSON.parse(localStorage.getItem('libero-care-network')||'[{"name":"Ana Ribeiro","role":"Filha e contato principal","initial":"A","enabled":true},{"name":"Carlos Souza","role":"Cuidador","initial":"C","enabled":true},{"name":"Dra. Helena Lima","role":"Médica","initial":"H","enabled":false}]')}function renderPeople(){const list=people();document.querySelector('#people').innerHTML=list.map((p,i)=>`<div class="person"><div class="avatar">${esc(p.initial)}</div><div class="grow"><strong>${esc(p.name)}</strong><div class="muted">${esc(p.role)}</div></div><span class="muted">Recebe alertas</span><button class="switch ${p.enabled?'on':''}" aria-label="Alternar alertas para ${esc(p.name)}" onclick="togglePerson(${i})"></button></div>`).join('')}function togglePerson(i){const l=people();l[i].enabled=!l[i].enabled;localStorage.setItem('libero-care-network',JSON.stringify(l));renderPeople()}function addPerson(){toast('Em uma próxima etapa, este botão poderá convidar alguém por e-mail ou WhatsApp.');}
function perfil(){shell('perfil.html',`<div class="hero"><div><div class="eyebrow">Perfil de cuidado</div><h1>O que faz ela se sentir em casa.</h1><p>Preferências e referências que ajudam o Libero a acolher, orientar e conversar com respeito.</p></div><button class="primary" onclick="saveProfile()">Salvar preferências</button></div><section class="card"><div class="grid profile-grid"><label>Como prefere ser chamada<input id="preferred-name" class="field" value="Dona Maria"></label><label>Rotina que traz conforto<input class="field" value="Café com música pela manhã"></label><label>Pessoas importantes<input class="field" value="Ana, Carlos, netos"></label><label>Músicas e temas queridos<input class="field" value="Samba, histórias da juventude"></label><label>O que costuma acalmar<textarea class="field" rows="3">Falar devagar, validar o sentimento e oferecer uma lembrança boa.</textarea></label><label>Plano em uma crise<textarea class="field" rows="3">Acolher, afastar riscos e avisar Ana se a agitação permanecer.</textarea></label></div></section><section class="card" style="margin-top:16px"><h2>Como o Libero usa essas informações</h2><p class="muted">Elas orientam a conversa e os lembretes; não substituem avaliação ou orientação médica.</p></section>`)}function saveProfile(){localStorage.setItem('libero-preferred-name',document.querySelector('#preferred-name').value);toast('Somente o nome preferido é salvo neste dispositivo; os demais campos ainda não são persistidos.');}
function elder(){document.body.innerHTML=`<div class="elder-page"><header class="elder-head"><img src="assets/libero-logo.jpeg" alt="Logo Libero"><div class="eyebrow">LIBERO</div><h1>Olá, Dona Maria.</h1><p class="muted">Estou aqui com você.</p></header><p class="notice">Demonstração: os botões abaixo mostram respostas simuladas. Eles não iniciam música, exibem fotos ou enviam notificações.</p><section class="elder-actions"><button onclick="elderReply('Vamos conversar. Estou aqui para ouvir você.')">Falar com Libero</button><button onclick="elderReply('Vou colocar uma música tranquila para você.')">Ouvir música</button><button onclick="elderReply('Vamos ver lembranças bonitas da sua família.')">Ver fotos da família</button><button onclick="elderReply('Vou avisar alguém da sua família agora.')">Pedir ajuda</button></section><p id="elder-response" class="notice" hidden></p></div>`}function elderReply(text){const e=document.querySelector('#elder-response');e.hidden=false;e.textContent=text}
window.addEventListener('DOMContentLoaded',()=>document.body.dataset.public==='elder'?elder():boot());


// ============================================================
// MICROFONE DO CUIDADOR (toggle)
// ============================================================

let micCuidadorAtivo = false;

async function toggleMicrofone() {
  const btn = document.getElementById('mic-cuidador-btn');
  const status = document.getElementById('mic-cuidador-status');
  
  if (!micCuidadorAtivo) {
    const texto = prompt("O que você quer falar para o idoso?");
    if (!texto) return;
    
    try {
      await req('/audio/cuidador/enviar', {
        method: 'POST',
        body: JSON.stringify({
          texto: texto,
          idoso_id: IDOSO_ID
        })
      });
      
      btn.textContent = '🔴 Falando...';
      btn.classList.add('gravando');
      status.textContent = 'Mensagem enviada';
      status.className = 'tag ok';
      
      setTimeout(() => {
        btn.textContent = '🎤 Falar com o idoso';
        btn.classList.remove('gravando');
        status.textContent = 'Pronto para falar';
        status.className = 'tag warn';
      }, 3000);
    } catch (e) {
      toast('Erro: ' + e.message);
    }
  }
}


// ============================================================
// BADGE DE MICROFONE
// ============================================================

async function atualizarBadgeMic() {
  try {
    const s = await req('/audio/status');
    const badge = document.getElementById('mic-badge');
    if (!badge) return;
    
    if (s.rodando) {
      badge.className = 'tag ok';
      badge.title = `Microfone ativo · ${s.frases_processadas || 0} frases`;
    } else {
      badge.className = 'tag warn';
      badge.title = 'Microfone pausado';
    }
  } catch (e) {
    // Silencioso
  }
}

// Atualizar a cada 5s
setInterval(atualizarBadgeMic, 5000);

// ============================================================
// NOTIFICAÇÕES EM TEMPO REAL (WebSocket)
// ============================================================

let wsNotif = null;

function conectarWebSocket() {
  if (wsNotif && wsNotif.readyState === WebSocket.OPEN) return;
  
  const WS_URL = API_URL.replace(/^http/, 'ws') + '/ws';
  
  try {
    wsNotif = new WebSocket(WS_URL);
    
    wsNotif.onopen = () => {
      console.log('[Libero WS] Conectado');
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
      console.log('[Libero WS] Erro:', e);
    };
  } catch (err) {
    console.log('[Libero WS] Erro ao conectar:', err);
  }
}

function mostrarEmergencia(msg) {
  // Som de alerta (opcional)
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
  
  // Notificação nativa do navegador
  if (Notification.permission === 'granted') {
    new Notification('EMERGÊNCIA - Libero', {
      body: `${msg.evento} detectada em ${msg.local}`,
      icon: '/assets/logo.svg',
      tag: 'emergencia'
    });
  }
  
  // Overlay visual
  const agora = new Date(msg.timestamp || Date.now()).toLocaleTimeString('pt-BR');
  const overlay = document.createElement('div');
  overlay.className = 'emergency-overlay';
  overlay.innerHTML = `
    <div class="em-icon">⚠️</div>
    <h1>EMERGÊNCIA</h1>
    <p><strong>${(msg.evento || 'evento').toUpperCase()}</strong> detectada em ${msg.local || 'casa'}</p>
    <p class="em-time">${agora} · Confiança ${((msg.confianca || 0) * 100).toFixed(0)}%</p>
    <button onclick="this.parentElement.remove()">Entendi, ver detalhes</button>
  `;
  document.body.appendChild(overlay);
}

// Solicitar permissão de notificação
function pedirPermissaoNotificacao() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

// Iniciar WebSocket quando o dashboard carregar
window.addEventListener('load', () => {
  pedirPermissaoNotificacao();
  conectarWebSocket();
});


// ============================================================
// CONVERSAS (nova função com bubbles)
// ============================================================


async function loadMessages(){
  try{
    const r = await req('/chat/' + IDOSO_ID + '/mensagens?limite=100');
    const mensagens = r.mensagens || [];
    const container = document.querySelector('#chat-messages');
    if(!container) return;
    
    const ordered = [...mensagens].reverse();
    
    if(!ordered.length){
      container.innerHTML = '<div class="empty-state"><div class="empty-icon">&#128172;</div><div class="empty-title">Nenhuma conversa registrada</div><div class="empty-text">As conversas entre Dona Maria e o Libero aparecerao aqui.</div></div>';
      return;
    }
    
    let ultimoDia = '';
    container.innerHTML = ordered.map(function(m){
      const data = new Date(m.timestamp);
      const dia = data.toLocaleDateString('pt-BR', {day:'2-digit', month:'long'});
      const hora = data.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'});
      
      let divisor = '';
      if(dia !== ultimoDia){ divisor = '<div class="chat-day">' + dia + '</div>'; ultimoDia = dia; }
      
      const tipo = m.tipo || 'normal';
      const autor = m.autor || 'libero';
      
      let classe = 'eh-libero';
      let nome = 'Libero';
      let av = 'L';
      
      if(autor === 'idoso'){ classe = 'eh-idoso'; nome = 'Dona Maria'; av = 'M'; }
      else if(autor === 'sistema' || autor === 'familia'){ classe = 'eh-sistema'; nome = 'Monitoramento'; av = '!'; }
      else if(autor === 'cuidador'){ nome = 'Voce (cuidador)'; av = 'C'; }
      
      return divisor
        + '<div class="chat-bubble ' + classe + ' tipo-' + tipo + '">'
        + '<div class="chat-avatar">' + av + '</div>'
        + '<div class="chat-content">'
        + '<div class="chat-name">' + nome + '</div>'
        + '<div class="chat-text">' + esc(m.texto || '') + '</div>'
        + '<div class="chat-time">' + hora + '</div>'
        + '</div>'
        + '</div>';
    }).join('');
    
    container.scrollTop = container.scrollHeight;
  }catch(e){
    toast(e.message);
  }
}
