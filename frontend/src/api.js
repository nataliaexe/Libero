// Cliente HTTP do Libero. A sessão fica no cookie HttpOnly emitido pelo servidor:
// nunca guardamos o token no localStorage.
const hostname = window.location.hostname;
const frontendDevPort = ['3000', '5500'].includes(window.location.port);
const localApi = frontendDevPort
  ? `${window.location.protocol}//${hostname}:8080`
  : window.location.origin;

export const API_URL = import.meta.env.VITE_API_URL || localApi;
export const IDOSO_PADRAO = import.meta.env.VITE_IDOSO_ID || 'dona-maria';

export async function req(path, options = {}) {
  const resposta = await fetch(API_URL + path, {
    credentials: 'include',
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });

  let dados = {};
  try {
    dados = await resposta.json();
  } catch {
    dados = {};
  }

  if (!resposta.ok) {
    if (resposta.status === 401) {
      window.dispatchEvent(new CustomEvent('libero:unauthorized'));
    }
    const erro = new Error(dados.error || 'Não foi possível concluir esta ação.');
    erro.status = resposta.status;
    throw erro;
  }
  return dados;
}
