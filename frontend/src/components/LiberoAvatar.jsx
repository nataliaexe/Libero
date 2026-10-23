import React from 'react';
import '@google/model-viewer';
import { motion } from 'framer-motion';

const ESTADOS = {
  idle: {
    rotulo: 'Estou aqui',
    cor: 'rgba(124, 92, 191, 0.42)',
    pulso: 3.2,
    escala: [1, 1.025, 1],
  },
  ouvindo: {
    rotulo: 'Ouvindo você',
    cor: 'rgba(63, 185, 80, 0.55)',
    pulso: 1.5,
    escala: [1, 1.045, 1],
  },
  falando: {
    rotulo: 'Falando',
    cor: 'rgba(88, 166, 255, 0.58)',
    pulso: 0.8,
    escala: [1, 1.035, 1],
  },
  pensando: {
    rotulo: 'Pensando',
    cor: 'rgba(233, 69, 96, 0.5)',
    pulso: 1.2,
    escala: [1, 1.06, 1],
  },
};

export default function LiberoAvatar({ estado = 'idle' }) {
  const atual = ESTADOS[estado] || ESTADOS.idle;

  return (
    <div className="avatar-3d" aria-live="polite">
      <motion.div
        className="avatar-3d-brilho"
        animate={{ backgroundColor: atual.cor, scale: atual.escala, opacity: [0.55, 0.9, 0.55] }}
        transition={{ duration: atual.pulso, repeat: Infinity, ease: 'easeInOut' }}
        aria-hidden="true"
      />
      <motion.div
        className="avatar-3d-modelo"
        animate={{ y: estado === 'ouvindo' ? [0, -5, 0] : estado === 'pensando' ? [0, -3, 0] : 0 }}
        transition={{ duration: estado === 'ouvindo' ? 1.4 : 2.4, repeat: Infinity, ease: 'easeInOut' }}
      >
        <model-viewer
          src="/woman.glb"
          alt="Avatar 3D acolhedor do Libero"
          autoplay
          animation-name="mixamo.com"
          auto-rotate
          rotation-per-second="8deg"
          disable-zoom
          interaction-prompt="none"
          shadow-intensity="0.35"
          exposure="1"
          style={{ width: '100%', height: '100%', backgroundColor: 'transparent', outline: 'none' }}
        />
      </motion.div>
      <p className="avatar-3d-rotulo">{atual.rotulo}</p>
    </div>
  );
}
