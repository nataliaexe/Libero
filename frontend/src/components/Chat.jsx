import { useCallback, useEffect, useRef, useState } from 'react';
import { req } from '../api.js';

const ROTULOS = { idoso: 'Maria', libero: 'Libero', cuidador: 'You' };

// Fala a resposta do Libero e devolve o avatar aos estados corretos.
function falar(texto, setEstado) {
  setEstado('idle');
  if (!texto || !('speechSynthesis' in window)) return;
  const fala = new SpeechSynthesisUtterance(texto);
  fala.lang = 'en-US';
  fala.onstart = () => setEstado('falando');
  fala.onend = () => setEstado('idle');
  fala.onerror = () => setEstado('idle');
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(fala);
}

export default function Chat({ idosoId, setEstado }) {
  const [mensagens, setMensagens] = useState([]);
  const [texto, setTexto] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState('');
  const fimRef = useRef(null);

  const carregar = useCallback(async () => {
    try {
      const dados = await req(`/chat/${idosoId}/mensagens?limite=50`);
      // A API devolve do mais recente para o mais antigo; exibimos em ordem cronológica.
      setMensagens([...(dados.mensagens || [])].reverse());
      setErro('');
    } catch (e) {
      setErro(e.message);
    }
  }, [idosoId]);

  useEffect(() => {
    carregar();
    const intervalo = setInterval(carregar, 5000);
    return () => clearInterval(intervalo);
  }, [carregar]);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens]);

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
      setTexto('');
      await carregar();
      falar(resposta.resposta, setEstado);
    } catch (e) {
      setErro(e.message);
      setEstado('idle');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="card react-chat">
      <h2>Conversations</h2>
      {erro && <p className="chat-error" role="alert">{erro}</p>}

      <div className="chat-container">
        {mensagens.length === 0 && <p className="empty-state">No conversations yet.</p>}
        {mensagens.map((m) => (
          <div key={m.id} className={`chat-bubble ${m.autor === 'idoso' ? 'eh-idoso' : m.autor === 'libero' ? 'eh-libero' : 'eh-sistema'}`}>
            <div className="chat-avatar">{m.autor === 'idoso' ? 'M' : m.autor === 'libero' ? 'L' : 'Y'}</div>
            <div className="chat-content">
              <div className="chat-name">{ROTULOS[m.autor] || m.autor}</div>
              <div className="chat-text">{m.texto}</div>
            </div>
          </div>
        ))}
        <div ref={fimRef} />
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
