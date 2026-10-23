import { useState } from 'react';
import { API_URL, req } from '../api.js';

// A câmera usa o endpoint do servidor (/camera/stream) com ticket de uso único,
// que expira em 30 segundos. O ticket é necessário porque <img> não envia cabeçalhos.
export default function Ambiente() {
  const [src, setSrc] = useState(null);
  const [erro, setErro] = useState('');

  async function abrir() {
    setErro('');
    try {
      await req('/camera/start', { method: 'POST' });
      const { ticket } = await req('/camera/stream-ticket', { method: 'POST' });
      setSrc(`${API_URL}/camera/stream?ticket=${encodeURIComponent(ticket)}`);
    } catch (e) {
      setErro(e.message);
    }
  }

  async function fechar() {
    setErro('');
    try {
      await req('/camera/stop', { method: 'POST' });
    } catch (e) {
      setErro(e.message);
    }
    setSrc(null);
  }

  return (
    <section className="cartao">
      <h2>Ambiente</h2>
      {src ? (
        <img
          className="camera"
          src={src}
          alt="Visualização do ambiente de cuidado"
          onError={() => setErro('Câmera indisponível. Verifique o dispositivo.')}
        />
      ) : (
        <p className="vazio">A câmera fica fechada até você abri-la.</p>
      )}
      {erro && <p className="erro">{erro}</p>}
      <div className="linha">
        <button className="primario" onClick={abrir}>Abrir visualização</button>
        <button onClick={fechar}>Encerrar</button>
      </div>
    </section>
  );
}
