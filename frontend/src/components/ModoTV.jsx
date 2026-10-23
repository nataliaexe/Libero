import { useState } from 'react';
import LiberoAvatar from './LiberoAvatar.jsx';
import DevicePairing from './DevicePairing.jsx';

// Visão do idoso: tela limpa, avatar grande no centro.
export default function ModoTV({ estado, onVoltar, idosoId, setEstado }) {
  const [mostrarPareamento, setMostrarPareamento] = useState(false);

  return (
    <div className="modo-tv">
      <LiberoAvatar estado={estado} grande />
      <div className="modo-tv-controls">
        <button className="voltar" onClick={onVoltar}>Voltar</button>
        <button className="modo-tv-pair" onClick={() => setMostrarPareamento(true)}>
          Emparelhar TV
        </button>
      </div>
      {mostrarPareamento && (
        <DevicePairing
          idosoId={idosoId}
          onClose={() => setMostrarPareamento(false)}
        />
      )}
    </div>
  );
}
