import { useState } from 'react';
import { IDOSO_PADRAO } from '../api.js';
import Chat from './Chat.jsx';
import Ambiente from './Ambiente.jsx';
import LiberoAvatar from './LiberoAvatar.jsx';
import AlertaEmergencia from './AlertaEmergencia.jsx';
import ModoTV from './ModoTV.jsx';

export default function Painel({ usuario, onSair }) {
  const [aba, setAba] = useState('conversa');
  const [estado, setEstado] = useState('idle'); // idle | ouvindo | pensando | falando
  const [modoTV, setModoTV] = useState(false);

  // Usuários vinculados a um idoso usam o próprio idoso_id; admin usa o padrão.
  const idosoId =
    usuario.idoso_id && usuario.idoso_id !== '*' ? usuario.idoso_id : IDOSO_PADRAO;

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
          <Ambiente />
        )}
        <aside className="avatar-lateral">
          <LiberoAvatar estado={estado} setEstado={setEstado} />
        </aside>
      </div>

      <AlertaEmergencia idosoId={idosoId} />
      {modoTV && <ModoTV estado={estado} onVoltar={() => setModoTV(false)} idosoId={idosoId} setEstado={setEstado} />}
    </main>
  );
}
