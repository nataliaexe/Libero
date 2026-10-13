"""
Libero - Captura de Movimento
Detecta movimento usando a câmera do dispositivo.
Usa frame differencing (subtração de fundo).
"""

import cv2
import numpy as np
from datetime import datetime, timezone
import os


class DetectorMovimento:
    """Detecta movimento em tempo real usando a câmera."""
    
    def __init__(self, camera_id=0, threshold=500, area_minima=1000):
        """
        Args:
            camera_id: ID da câmera (0 = padrão)
            threshold: sensibilidade (menor = mais sensível)
            area_minima: área mínima em pixels para considerar movimento
        """
        self.camera_id = camera_id
        self.threshold = threshold
        self.area_minima = area_minima
        self.cap = None
        self.fundo = None
    
    def iniciar(self):
        """Inicia a câmera."""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.camera_id}")
        print(f"[Libero] Câmera {self.camera_id} iniciada.")
    
    def parar(self):
        """Para a câmera."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[Libero] Câmera parada.")
    
    def detectar_frame(self, frame):
        """
        Detecta movimento em um frame.
        
        Returns:
            dict com:
            - movimento: bool
            - area: área do movimento em pixels
            - regioes: lista de (x, y, w, h) das regiões com movimento
        """
        # Converter para escala de cinza e aplicar blur
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cinza = cv2.GaussianBlur(cinza, (21, 21), 0)
        
        # Inicializar fundo
        if self.fundo is None:
            self.fundo = cinza.copy()
            return {"movimento": False, "area": 0, "regioes": []}
        
        # Calcular diferença com o fundo
        diff = cv2.absdiff(self.fundo, cinza)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Encontrar contornos
        contornos, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        regioes = []
        area_total = 0
        
        for contorno in contornos:
            area = cv2.contourArea(contorno)
            if area < self.area_minima:
                continue
            
            (x, y, w, h) = cv2.boundingRect(contorno)
            regioes.append((x, y, w, h))
            area_total += area
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Atualizar fundo lentamente
        cv2.accumulateWeighted(cinza, self.fundo, 0.01)
        
        return {
            "movimento": len(regioes) > 0,
            "area": int(area_total),
            "regioes": regioes
        }
    
    def monitorar(self, duracao=None, callback=None, mostrar=True):
        """
        Monitora movimento continuamente.
        
        Args:
            duracao: tempo em segundos (None = infinito)
            callback: função chamada quando há movimento
            mostrar: se True, mostra janela com vídeo
        """
        self.iniciar()
        inicio = datetime.now(timezone.utc)
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                resultado = self.detectar_frame(frame)
                
                if resultado["movimento"]:
                    if callback:
                        callback(resultado)
                    else:
                        print(f"[Libero] Movimento detectado! Área: {resultado['area']}px")
                
                if mostrar:
                    cv2.imshow("Libero - Movimento", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Verificar duração
                if duracao:
                    elapsed = (datetime.now(timezone.utc) - inicio).total_seconds()
                    if elapsed >= duracao:
                        break
        
        finally:
            self.parar()


if __name__ == "__main__":
    detector = DetectorMovimento()
    detector.monitorar(duracao=30)
