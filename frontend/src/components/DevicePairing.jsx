import React, { useState, useEffect } from 'react';
import { req } from '../api.js';

export default function DevicePairing({ idosoId, onClose }) {
  const [codigoPareamento, setCodigoPareamento] = useState('');
  const [status, setStatus] = useState('idle'); // idle | gerando | conectado | erro
  const [dispositivos, setDispositivos] = useState([]);
  const [nomeDispositivo, setNomeDispositivo] = useState('');

  async function gerarCodigo() {
    setStatus('gerando');
    try {
      const dados = await req(`/dispositivos/${idosoId}/parear`, {
        method: 'POST',
      });
      setCodigoPareamento(dados.codigo);
      setStatus('idle');
    } catch (e) {
      setStatus('erro');
      alert('Erro ao gerar código: ' + e.message);
    }
  }

  async function conectarComCodigo() {
    if (!nomeDispositivo.trim()) {
      alert('Digite o nome do dispositivo');
      return;
    }
    try {
      const dados = await req(`/dispositivos/${idosoId}/conectar`, {
        method: 'POST',
        body: JSON.stringify({ codigo: codigoPareamento, nome: nomeDispositivo }),
      });
      setStatus('conectado');
      setDispositivos([...dispositivos, dados.dispositivo]);
      setCodigoPareamento('');
      setNomeDispositivo('');
      carregarDispositivos();
    } catch (e) {
      setStatus('erro');
      alert('Erro ao conectar: ' + e.message);
    }
  }

  async function carregarDispositivos() {
    try {
      const dados = await req(`/dispositivos/${idosoId}`);
      setDispositivos(dados.dispositivos || []);
    } catch (e) {
      console.error('Erro ao carregar dispositivos:', e);
    }
  }

  // Carregar dispositivos ao montar
  useEffect(() => {
    carregarDispositivos();
  }, [idosoId]);

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Emparelhar Dispositivo</h2>
        <p>Conecte uma TV ou outro dispositivo para exibir o avatar em tela cheia.</p>

        <div className="pairing-section">
          <h3>Dispositivos Conectados</h3>
          {dispositivos.length === 0 ? (
            <p className="muted">Nenhum dispositivo conectado.</p>
          ) : (
            <ul className="device-list">
              {dispositivos.map((d) => (
                <li key={d.id} className="device-item">
                  <span>{d.nome}</span>
                  <span className={`status ${d.ativo ? 'online' : 'offline'}`}>
                    {d.ativo ? 'Online' : 'Offline'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="pairing-section">
          <h3>Novo Pareamento</h3>
          <div className="pairing-controls">
            <label>Nome do Dispositivo:</label>
            <input
              type="text"
              value={nomeDispositivo}
              onChange={(e) => setNomeDispositivo(e.target.value)}
              placeholder="Ex: TV da Sala"
            />
            <button onClick={gerarCodigo} disabled={status === 'gerando'}>
              {status === 'gerando' ? 'Gerando...' : 'Gerar Código'}
            </button>
            {codigoPareamento && (
              <div className="pairing-code">
                <label>Código de Pareamento:</label>
                <input
                  type="text"
                  value={codigoPareamento}
                  readOnly
                  className="code-display"
                />
                <p className="muted">
                  Digite este código no dispositivo que deseja emparelhar.
                </p>
                <button onClick={conectarComCodigo} className="primary">
                  Conectar Dispositivo
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Fechar</button>
        </div>
      </div>
    </div>
  );
}
