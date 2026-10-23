import { useState } from 'react';

export default function LiberoAvatar({ estado = 'idle', grande = false, setEstado }) {
  const [falhaFala, setFalhaFala] = useState(false);

  function cumprimentar() {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) {
      setFalhaFala(true);
      return;
    }
    const fala = new SpeechSynthesisUtterance('Oi, que bom ter você aqui. Quer conversar comigo?');
    fala.lang = 'pt-BR';
    fala.onstart = () => setEstado?.('falando');
    fala.onend = () => setEstado?.('idle');
    fala.onerror = () => setEstado?.('idle');
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(fala);
  }

  return (
    <div className={`libero-companion${grande ? ' grande' : ''}`}>
      <button
        type="button"
        className="libero-companion-personagem"
        data-state={estado}
        onClick={cumprimentar}
        aria-label="Toque para ouvir uma mensagem do Libero"
      >
        <span className="libero-companion-aura" aria-hidden="true" />
        <img src="/assets/companion-avatar.svg" alt="" />
        <span className="libero-companion-ondas" aria-hidden="true"><i /><i /><i /></span>
      </button>
      {grande && <p className="libero-companion-dica">Toque no Libero para conversar</p>}
      {falhaFala && <span className="sr-only" role="status">A fala não está disponível neste navegador.</span>}
    </div>
  );
}
