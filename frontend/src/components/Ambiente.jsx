export default function Ambiente({ cameraAtiva, erro, onAbrir, onFechar }) {
  return (
    <section className="cartao">
      <h2>Ambiente</h2>
      <p className="vazio">
        {cameraAtiva
          ? 'A visualização ao vivo continua em uma janela fixa enquanto você navega pelo Libero.'
          : 'A câmera fica fechada até você abri-la.'}
      </p>
      {erro && <p className="erro">{erro}</p>}
      <div className="linha">
        {!cameraAtiva && <button className="primario" onClick={onAbrir}>Abrir visualização</button>}
        {cameraAtiva && <button onClick={onFechar}>Encerrar visualização</button>}
      </div>
    </section>
  );
}
