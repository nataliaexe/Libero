import React from 'react';
import { createRoot } from 'react-dom/client';
import LiberoAvatar from './components/LiberoAvatar.jsx';
import Chat from './components/Chat.jsx';

let currentState = 'idle';
const roots = new Map();

export function mount(container, initialState = 'idle') {
  if (!container) return;
  currentState = initialState;
  roots.get('avatar')?.unmount();
  const root = createRoot(container);
  roots.set('avatar', root);
  root.render(<LiberoAvatar estado={currentState} />);
}

export function setState(estado) {
  currentState = estado;
  roots.get('avatar')?.render(<LiberoAvatar estado={currentState} />);
}

export function mountChat(container, idosoId, onStateChange) {
  if (!container) return;
  roots.get('chat')?.unmount();
  const root = createRoot(container);
  roots.set('chat', root);
  root.render(<Chat idosoId={idosoId} setEstado={onStateChange} />);
}

export function unmount() {
  for (const root of roots.values()) root.unmount();
  roots.clear();
}
