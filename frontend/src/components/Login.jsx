import { useState } from 'react';
import { req } from '../api.js';

export default function Login({ onEntrar }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function entrar(evento) {
    evento.preventDefault();
    if (!email || !senha) {
      setErro('Preencha seu e-mail e sua senha.');
      return;
    }
    setEnviando(true);
    setErro('');
    try {
      const dados = await req('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, senha }),
      });
      onEntrar(dados);
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao login" onSubmit={entrar}>
      <p className="eyebrow">CUIDADO QUE PERMANECE</p>
      <h1>Bem-vinda à rede de cuidado.</h1>
      <label>
        E-mail
        <input
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </label>
      <label>
        Senha
        <input
          type="password"
          autoComplete="current-password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
        />
      </label>
      {erro && <p className="erro">{erro}</p>}
      <button className="primario" disabled={enviando}>
        {enviando ? 'Entrando…' : 'Entrar no Libero'}
      </button>
    </form>
  );
}
