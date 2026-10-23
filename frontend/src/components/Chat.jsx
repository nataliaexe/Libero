import { Fragment, useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { req } from '../api.js';

const PAGE_SIZE = 50;
const CACHE_LIMIT = 100;
const ROTULOS = { idoso: 'Maria', libero: 'Libero' };

function chaveCache(idosoId) {
  return `libero:chat:v1:${idosoId}`;
}

function lerCache(idosoId) {
  const salvo = window.sessionStorage.getItem(chaveCache(idosoId));
  if (!salvo) return [];
  const mensagens = JSON.parse(salvo);
  if (!Array.isArray(mensagens)) throw new Error('The saved conversation has an invalid format.');
  return mensagens.filter((mensagem) =>
    mensagem && typeof mensagem.id === 'string' &&
    typeof mensagem.autor === 'string' && typeof mensagem.texto === 'string',
  );
}

function salvarCache(idosoId, mensagens) {
  window.sessionStorage.setItem(
    chaveCache(idosoId),
    JSON.stringify(mensagens.slice(-CACHE_LIMIT)),
  );
}

function chaveMensagem(mensagem) {
  return mensagem.id || `${mensagem.timestamp}-${mensagem.autor}-${mensagem.texto}`;
}

function ordenarMensagens(mensagens) {
  return [...mensagens].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
}

function rotuloData(timestamp) {
  const data = new Date(timestamp);
  if (Number.isNaN(data.getTime())) return 'Earlier';
  const hoje = new Date();
  const ontem = new Date();
  ontem.setDate(hoje.getDate() - 1);
  if (data.toDateString() === hoje.toDateString()) return 'Today';
  if (data.toDateString() === ontem.toDateString()) return 'Yesterday';
  return data.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function mesclarMensagens(atuais, novas) {
  const unicas = new Map(atuais.map((mensagem) => [chaveMensagem(mensagem), mensagem]));
  let alterou = false;
  novas.forEach((mensagem) => {
    const chave = chaveMensagem(mensagem);
    if (!unicas.has(chave)) {
      unicas.set(chave, mensagem);
      alterou = true;
    }
  });
  return alterou ? ordenarMensagens([...unicas.values()]) : atuais;
}

function idiomaDaMensagem(texto) {
  if (/[ãõáàâéêíóôúç]/i.test(texto) || /\b(oi|olá|você|obrigado|obrigada|bom dia|boa noite|tudo|não|quero|estou)\b/i.test(texto)) {
    return 'pt-BR';
  }
  if (/\b(hello|thank you|good morning|good evening)\b/i.test(texto)) return 'en-US';
  return navigator.language || 'pt-BR';
}

function falar(texto, setEstado, idioma) {
  setEstado('idle');
  if (!texto || !('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) return;
  const fala = new SpeechSynthesisUtterance(texto);
  fala.lang = idioma || 'pt-BR';
  fala.onstart = () => setEstado('falando');
  fala.onend = () => setEstado('idle');
  fala.onerror = () => setEstado('idle');
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(fala);
}

export default function Chat({ idosoId, usuario, setEstado }) {
  const [mensagens, setMensagens] = useState([]);
  const [texto, setTexto] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [carregandoAnteriores, setCarregandoAnteriores] = useState(false);
  const [temAnteriores, setTemAnteriores] = useState(false);
  const [erro, setErro] = useState('');
  const mensagensRef = useRef(mensagens);
  mensagensRef.current = mensagens;
  const listaRef = useRef(null);
  const offsetAnterioresRef = useRef(PAGE_SIZE);
  const idsConhecidosRef = useRef(new Set());
  const requisicaoAtivaRef = useRef(false);
  const carregouHistoricoRef = useRef(false);
  const montadoRef = useRef(false);
  const idosoAtualRef = useRef(idosoId);
  idosoAtualRef.current = idosoId;
  const posicaoAnteriorRef = useRef(null);
  const fixarNoFimRef = useRef(true);
  const nomeIdoso = localStorage.getItem('libero-preferred-name') || ROTULOS.idoso;
  const nomeCuidador = usuario?.nome || 'You';

  const carregar = useCallback(async ({ silencioso = false } = {}) => {
    if (requisicaoAtivaRef.current || document.hidden) return;
    requisicaoAtivaRef.current = true;
    if (!silencioso) setCarregando(true);

    try {
      const dados = await req(`/chat/${idosoId}/mensagens?limite=${PAGE_SIZE}`);
      if (!montadoRef.current || idosoAtualRef.current !== idosoId) return;
      const novas = Array.isArray(dados.mensagens) ? [...dados.mensagens].reverse() : [];
      const lista = listaRef.current;
      fixarNoFimRef.current = !lista || lista.scrollHeight - lista.scrollTop - lista.clientHeight < 80;

      let entradasNovas = 0;
      novas.forEach((mensagem) => {
        const chave = chaveMensagem(mensagem);
        if (!idsConhecidosRef.current.has(chave)) {
          idsConhecidosRef.current.add(chave);
          entradasNovas += 1;
        }
      });
      if (carregouHistoricoRef.current) offsetAnterioresRef.current += entradasNovas;
      else carregouHistoricoRef.current = true;

      const mescladas = mesclarMensagens(mensagensRef.current, novas);
      mensagensRef.current = mescladas;
      setMensagens(mescladas);
      setTemAnteriores(novas.length === PAGE_SIZE);
      setErro('');
      try {
        salvarCache(idosoId, mescladas);
      } catch (e) {
        setErro(`Conversation loaded, but session cache could not be saved: ${e.message}`);
      }
    } catch (e) {
      if (montadoRef.current && idosoAtualRef.current === idosoId) setErro(e.message);
    } finally {
      requisicaoAtivaRef.current = false;
      if (montadoRef.current && idosoAtualRef.current === idosoId) setCarregando(false);
    }
  }, [idosoId]);

  useEffect(() => {
    montadoRef.current = true;
    requisicaoAtivaRef.current = false;
    idsConhecidosRef.current.clear();
    offsetAnterioresRef.current = PAGE_SIZE;
    carregouHistoricoRef.current = false;
    mensagensRef.current = [];
    setMensagens([]);
    setTexto('');
    setCarregando(true);
    setCarregandoAnteriores(false);
    setErro('');
    try {
      const cache = lerCache(idosoId);
      if (cache.length) {
        mensagensRef.current = ordenarMensagens(cache);
        setMensagens(mensagensRef.current);
        idsConhecidosRef.current = new Set(cache.map(chaveMensagem));
        offsetAnterioresRef.current = Math.max(PAGE_SIZE, cache.length);
        carregouHistoricoRef.current = true;
        setCarregando(false);
      }
    } catch (e) {
      setErro(`Saved conversation cache could not be read: ${e.message}`);
    }
    carregar();

    const intervalo = setInterval(() => {
      if (!document.hidden) carregar({ silencioso: true });
    }, 15000);
    const aoVoltar = () => {
      if (!document.hidden) carregar({ silencioso: true });
    };
    document.addEventListener('visibilitychange', aoVoltar);
    return () => {
      montadoRef.current = false;
      clearInterval(intervalo);
      document.removeEventListener('visibilitychange', aoVoltar);
    };
  }, [carregar]);

  useLayoutEffect(() => {
    const lista = listaRef.current;
    if (!lista) return;
    if (posicaoAnteriorRef.current !== null) {
      lista.scrollTop = posicaoAnteriorRef.current + lista.scrollHeight - lista.dataset.alturaAnterior;
      posicaoAnteriorRef.current = null;
    } else if (fixarNoFimRef.current) {
      lista.scrollTop = lista.scrollHeight;
      fixarNoFimRef.current = false;
    }
  }, [mensagens]);

  async function carregarAnteriores() {
    if (carregandoAnteriores || requisicaoAtivaRef.current || !temAnteriores) return;
    requisicaoAtivaRef.current = true;
    const lista = listaRef.current;
    if (lista) {
      posicaoAnteriorRef.current = lista.scrollTop;
      lista.dataset.alturaAnterior = lista.scrollHeight;
    }
    setCarregandoAnteriores(true);
    try {
      const dados = await req(
        `/chat/${idosoId}/mensagens?limite=${PAGE_SIZE}&offset=${offsetAnterioresRef.current}`,
      );
      if (!montadoRef.current || idosoAtualRef.current !== idosoId) return;
      const anteriores = Array.isArray(dados.mensagens) ? [...dados.mensagens].reverse() : [];
      anteriores.forEach((mensagem) => idsConhecidosRef.current.add(chaveMensagem(mensagem)));
      offsetAnterioresRef.current += anteriores.length;
      const mescladas = mesclarMensagens(mensagensRef.current, anteriores);
      mensagensRef.current = mescladas;
      setMensagens(mescladas);
      setTemAnteriores(anteriores.length === PAGE_SIZE);
      setErro('');
      try {
        salvarCache(idosoId, mescladas);
      } catch (e) {
        setErro(`Older messages loaded, but session cache could not be saved: ${e.message}`);
      }
    } catch (e) {
      posicaoAnteriorRef.current = null;
      if (montadoRef.current && idosoAtualRef.current === idosoId) setErro(e.message);
    } finally {
      requisicaoAtivaRef.current = false;
      if (montadoRef.current && idosoAtualRef.current === idosoId) setCarregandoAnteriores(false);
    }
  }

  async function enviar(evento) {
    evento.preventDefault();
    const msg = texto.trim();
    if (!msg || enviando) return;

    setEnviando(true);
    setErro('');
    setEstado('pensando');
    try {
      const resposta = await req(`/chat/${idosoId}/mensagem`, {
        method: 'POST',
        body: JSON.stringify({ texto: msg }),
      });
      if (!montadoRef.current || idosoAtualRef.current !== idosoId) return;
      setTexto('');
      await carregar();
      falar(resposta.resposta, setEstado, resposta.idioma || idiomaDaMensagem(msg));
    } catch (e) {
      if (montadoRef.current && idosoAtualRef.current === idosoId) {
        setErro(e.message);
        setEstado('idle');
      }
    } finally {
      if (montadoRef.current && idosoAtualRef.current === idosoId) setEnviando(false);
    }
  }

  return (
    <section className="card react-chat">
      <h2>Conversations</h2>
      {erro && (
        <div className="chat-error" role="alert">
          <span>{erro}</span>
          <button type="button" onClick={() => carregar()} disabled={carregando}>Try again</button>
        </div>
      )}

      <div className="chat-container" ref={listaRef} aria-live="polite" aria-busy={carregando}>
        {temAnteriores && (
          <button
            className="chat-load-older"
            type="button"
            onClick={carregarAnteriores}
            disabled={carregandoAnteriores}
          >
            {carregandoAnteriores ? 'Loading…' : 'Load older messages'}
          </button>
        )}
        {carregando && mensagens.length === 0 && <p className="empty-state">Loading conversations…</p>}
        {!carregando && mensagens.length === 0 && <p className="empty-state">No conversations yet.</p>}
        {mensagens.map((m, index) => {
          const ehIdoso = m.autor === 'idoso';
          const ehLibero = m.autor === 'libero';
          const classe = ehIdoso ? 'eh-idoso' : ehLibero ? 'eh-libero' : 'eh-sistema';
          const rotulo = ehIdoso ? nomeIdoso : ehLibero ? ROTULOS.libero : nomeCuidador;
          const dia = rotuloData(m.timestamp);
          const mudouDia = index === 0 || dia !== rotuloData(mensagens[index - 1].timestamp);
          return (
            <Fragment key={chaveMensagem(m)}>
              {mudouDia && <div className="chat-day-divider">{dia}</div>}
              <div className={`chat-bubble ${classe}`}>
                <div className="chat-avatar" aria-hidden="true">{rotulo.slice(0, 1).toUpperCase()}</div>
                <div className="chat-content">
                  <div className="chat-name">{rotulo}</div>
                  <div className="chat-text">{m.texto}</div>
                </div>
              </div>
            </Fragment>
          );
        })}
      </div>

      <form className="react-chat-composer" onSubmit={enviar}>
        <input
          className="field"
          value={texto}
          maxLength={2000}
          placeholder="Write a message to Libero..."
          onChange={(e) => setTexto(e.target.value)}
          onFocus={() => !enviando && setEstado('ouvindo')}
          onBlur={() => !enviando && setEstado('idle')}
        />
        <button className="primary" disabled={enviando || !texto.trim()}>
          {enviando ? 'Sending…' : 'Send'}
        </button>
      </form>
    </section>
  );
}
