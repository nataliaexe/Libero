import { useState } from 'react';
import { API_URL, IDOSO_PADRAO, req } from '../api.js';
import Chat from './Chat.jsx';
import Ambiente from './Ambiente.jsx';
import LiberoAvatar from './LiberoAvatar.jsx';
import AlertaEmergencia from './AlertaEmergencia.jsx';
import ModoTV from './ModoTV.jsx';

export default function Painel({ usuario, onSair }) {
  const [aba, setAba] = useState('conversa');
  const [estado, setEstado] = useState('idle'); // idle | ouvindo | pensando | falando
  const [modoTV, setModoTV] = useState(false);
  const [cameraSrc, setCameraSrc] = useState(null);
  const [cameraErro, setCameraErro] = useState('');

  // Usuários vinculados a um idoso usam o próprio idoso_id; admin usa o padrão.
  const idosoId =
    usuario.idoso_id && usuario.idoso_id !== '*' ? usuario.idoso_id : IDOSO_PADRAO;

  async function abrirCamera() {
    setCameraErro('');
    try {
      await req('/camera/start', { method: 'POST' });
      const { ticket } = await req('/camera/stream-ticket', { method: 'POST' });
      setCameraSrc(`${API_URL}/camera/stream?ticket=${encodeURIComponent(ticket)}`);
    } catch (erro) {
      setCameraErro(erro.message);
    }
  }

  async function fecharCamera() {
    setCameraErro('');
    try {
      await req('/camera/stop', { method: 'POST' });
    } catch (erro) {
      setCameraErro(erro.message);
    }
    setCameraSrc(null);
  }

  return (
    <main className="shell">
      <header className="topo">
        <strong>LIBERO</strong>
        <span>{usuario.nome}</span>
        <button onClick={() => setModoTV(true)}>Modo TV</button>
        <button onClick={onSair}>Sair</button>
      </header>

      <nav className="abas">
        <button className={aba === 'conversa' ? 'ativa' : ''} onClick={() => setAba('conversa')}>
          Conversas
        </button>
        <button className={aba === 'ambiente' ? 'ativa' : ''} onClick={() => setAba('ambiente')}>
          Ambiente
        </button>
      </nav>

      <div className="conteudo-principal">
        {aba === 'conversa' ? (
          <Chat idosoId={idosoId} usuario={usuario} setEstado={setEstado} />
        ) : (
          <Ambiente
            cameraAtiva={Boolean(cameraSrc)}
            erro={cameraErro}
            onAbrir={abrirCamera}
            onFechar={fecharCamera}
          />
        )}
        <aside className="avatar-lateral">
          <LiberoAvatar estado={estado} setEstado={setEstado} />
        </aside>
      </div>

      <AlertaEmergencia idosoId={idosoId} />
      {(cameraSrc || cameraErro) && (
        <aside className="camera-flutuante" aria-label="Visualização ao vivo da câmera">
          <div className="camera-flutuante-topo">
            <strong>Câmera ao vivo</strong>
            <button onClick={fecharCamera} aria-label="Encerrar visualização da câmera">
              Encerrar
            </button>
          </div>
          {cameraSrc ? (
            <img
              src={cameraSrc}
              alt="Visualização ao vivo do ambiente"
              onError={() => {
                setCameraErro('Câmera indisponível. Verifique o dispositivo.');
                setCameraSrc(null);
              }}
            />
          ) : (
            <p className="erro">{cameraErro}</p>
          )}
        </aside>
      )}
      {modoTV && <ModoTV estado={estado} onVoltar={() => setModoTV(false)} idosoId={idosoId} setEstado={setEstado} />}
    </main>
  );
}
