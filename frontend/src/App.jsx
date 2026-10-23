import { useEffect, useState } from 'react';
import { req } from './api.js';
import Login from './components/Login.jsx';
import Painel from './components/Painel.jsx';

export default function App() {
  const [usuario, setUsuario] = useState(null);
  const [pronto, setPronto] = useState(false);

  // Ao abrir a página, pergunta ao servidor se o cookie de sessão ainda vale.
  useEffect(() => {
    req('/auth/me')
      .then(setUsuario)
      .catch(() => setUsuario(null))
      .finally(() => setPronto(true));
  }, []);

  if (!pronto) return <p className="centro">Carregando…</p>;
  if (!usuario) return <Login onEntrar={setUsuario} />;

  async function sair() {
    try {
      await req('/auth/logout', { method: 'POST' });
    } catch {
      // Mesmo que o logout falhe, encerramos a sessão local.
    }
    setUsuario(null);
  }

  return <Painel usuario={usuario} onSair={sair} />;
}
