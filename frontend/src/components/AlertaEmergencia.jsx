import { useEffect, useRef, useState } from 'react';
import { req } from '../api.js';

// Consulta /chat/<id>/emergencias. Só mostra o overlay para registros NOVOS
// (a contagem inicial é guardada sem alertar, para não assustar ao abrir a tela).
export default function AlertaEmergencia({ idosoId }) {
  const [novo, setNovo] = useState(null);
  const vistos = useRef(null);

  useEffect(() => {
    let ativo = true;

    async function checar() {
      try {
        const dados = await req(`/chat/${idosoId}/emergencias`);
        const lista = dados.emergencias || [];
        if (!ativo) return;
        if (vistos.current === null) {
          vistos.current = lista.length;
          return;
        }
        if (lista.length > vistos.current) {
          setNovo(lista[lista.length - 1]);
        }
        vistos.current = lista.length;
      } catch {
        // Falha de rede não deve derrubar a tela; tentamos de novo no próximo ciclo.
      }
    }

    checar();
    const intervalo = setInterval(checar, 5000);
    return () => {
      ativo = false;
      clearInterval(intervalo);
    };
  }, [idosoId]);

  if (!novo) return null;

  return (
    <div className="alerta-emergencia" role="alert">
      <strong>Possível emergência registrada</strong>
      <p>{novo.texto}</p>
      <small>Evento registrado. Nenhuma ação externa foi executada por este aplicativo.</small>
      <button onClick={() => setNovo(null)}>Entendi</button>
    </div>
  );
}
