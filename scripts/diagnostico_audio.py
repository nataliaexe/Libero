"""Compara microfones com uma captura curta de silêncio seguida de fala."""

import math
import io
import json
import subprocess
import sys
import time

import numpy as np

sd = None


def _sounddevice():
    global sd
    if sd is None:
        import sounddevice
        sd = sounddevice
    return sd


DURACAO_TESTE = 3
DURACAO_SILENCIO = 1
DURACAO_MAX_CONSULTA_DISPOSITIVOS = 8


def _capturar_microfone(device_id, sample_rate):
    amostras = []

    def callback(indata, frames, time_info, status):
        amostras.append(indata[:, 0].copy())

    with _sounddevice().InputStream(
        device=device_id,
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        time.sleep(DURACAO_TESTE)

    if not amostras:
        raise RuntimeError("nenhuma amostra recebida")
    return np.concatenate(amostras)


def _capturar_isolado(device_id, sample_rate):
    processo = subprocess.run(
        [sys.executable, __file__, "--capture", str(device_id), str(sample_rate)],
        capture_output=True,
        timeout=DURACAO_TESTE + 10,
    )
    if processo.returncode:
        detalhe = processo.stderr.decode(errors="replace").strip()
        raise RuntimeError(detalhe or f"processo de captura terminou com código {processo.returncode}")
    return np.load(io.BytesIO(processo.stdout))


def _consultar_dispositivos_isolado():
    """Query PortAudio in a child process so a broken backend cannot hang this CLI."""
    try:
        processo = subprocess.run(
            [sys.executable, __file__, "--devices"],
            capture_output=True,
            timeout=DURACAO_MAX_CONSULTA_DISPOSITIVOS,
            check=False,
        )
    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(
            f"PortAudio não respondeu em {DURACAO_MAX_CONSULTA_DISPOSITIVOS}s; "
            "verifique se o sistema expõe um dispositivo de áudio."
        ) from erro
    if processo.returncode:
        detalhe = processo.stderr.decode(errors="replace").strip()
        raise RuntimeError(detalhe or "Falha ao consultar o PortAudio.")
    try:
        dispositivos = json.loads(processo.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise RuntimeError("A resposta da consulta de áudio não é JSON válido.") from erro
    if not isinstance(dispositivos, list):
        raise RuntimeError("A lista de dispositivos de áudio retornou formato inválido.")
    return dispositivos


def calcular_snr(amostras, sample_rate):
    """Estima SNR usando o primeiro segundo silencioso como piso de ruído."""
    corte = int(sample_rate * DURACAO_SILENCIO)
    if corte <= 0 or len(amostras) <= corte:
        raise ValueError("captura curta demais para estimar a SNR")

    ruido = float(np.sqrt(np.mean(np.square(amostras[:corte]))))
    sinal = float(np.sqrt(np.mean(np.square(amostras[corte:]))))
    if sinal <= 0:
        return None
    if ruido <= 0:
        return math.inf
    return 20 * math.log10(sinal / ruido)


def main():
    try:
        dispositivos = _consultar_dispositivos_isolado()
    except Exception as erro:
        print(f"Não foi possível consultar os dispositivos de áudio: {erro}")
        return 1
    microfones = [
        (indice, dispositivo)
        for indice, dispositivo in enumerate(dispositivos)
        if dispositivo["max_input_channels"] > 0
    ]

    if not microfones:
        print("Nenhum dispositivo de entrada de áudio disponível.")
        return 1

    print("Dispositivos de áudio disponíveis:")
    for indice, dispositivo in enumerate(dispositivos):
        direcoes = []
        if dispositivo["max_input_channels"]:
            direcoes.append("entrada")
        if dispositivo["max_output_channels"]:
            direcoes.append("saída")
        tipo = "/".join(direcoes) or "sem canais"
        print(f"  [{indice}] {dispositivo['name']} ({tipo})")

    print(
        f"\nTeste de {DURACAO_TESTE}s por microfone: fique em silêncio no primeiro "
        "segundo e fale continuamente nos dois seguintes."
    )
    resultados = []
    for device_id, dispositivo in microfones:
        sample_rate = round(dispositivo["default_samplerate"])
        print(f"\nTestando [{device_id}] {dispositivo['name']}...")
        try:
            amostras = _capturar_isolado(device_id, sample_rate)
            snr = calcular_snr(amostras, sample_rate)
            if snr is None:
                print("  Sem sinal de voz detectável na janela de fala.")
                continue
            resultados.append((snr, device_id, dispositivo["name"]))
            snr_texto = "infinita" if math.isinf(snr) else f"{snr:.1f} dB"
            print(f"  SNR estimada: {snr_texto}")
        except Exception as erro:
            print(f"  Falha ao testar: {erro}")

    if not resultados:
        print("\nNão foi possível recomendar um microfone; repita o teste falando durante a captura.")
        return 1

    melhor = max(resultados)
    snr_texto = "infinita" if math.isinf(melhor[0]) else f"{melhor[0]:.1f} dB"
    print(f"\nRecomendação: [{melhor[1]}] {melhor[2]} (SNR estimada: {snr_texto}).")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--devices":
        try:
            dispositivos = [dict(dispositivo) for dispositivo in _sounddevice().query_devices()]
            print(json.dumps(dispositivos, ensure_ascii=False))
        except Exception as erro:
            print(f"Falha na consulta de dispositivos: {erro}", file=sys.stderr)
            raise SystemExit(1)
        raise SystemExit(0)
    if len(sys.argv) == 4 and sys.argv[1] == "--capture":
        try:
            audio_capturado = _capturar_microfone(int(sys.argv[2]), int(sys.argv[3]))
            buffer = io.BytesIO()
            np.save(buffer, audio_capturado)
            sys.stdout.buffer.write(buffer.getvalue())
        except Exception as erro:
            print(f"Falha na captura: {erro}", file=sys.stderr)
            raise SystemExit(1)
        raise SystemExit(0)
    raise SystemExit(main())
