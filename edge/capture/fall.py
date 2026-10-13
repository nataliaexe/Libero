"""
Libero - Detecção de Queda
Detecta queda usando pose estimation (MediaPipe).
"""

import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime, timezone


class DetectorQueda:
    """Detecta queda usando pose estimation."""
    
    # Índices dos landmarks do MediaPipe Pose
    NARIZ = 0
    OMBRO_ESQ = 11
    OMBRO_DIR = 12
    QUADRIL_ESQ = 23
    QUADRIL_DIR = 24
    JOELHO_ESQ = 25
    JOELHO_DIR = 26
    TORNOZELO_ESQ = 27
    TORNOZELO_DIR = 28
    
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Histórico para detectar transição
        self.historico = []
        self.max_historico = 30  # ~1 segundo a 30fps
    
    def iniciar(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.camera_id}")
        print(f"[Libero] Detector de queda iniciado.")
    
    def parar(self):
        if self.cap:
            self.cap.release()
        self.pose.close()
        cv2.destroyAllWindows()
    
    def calcular_inclinacao(self, landmarks, largura, altura):
        """
        Calcula a inclinação do corpo.
        
        Retorna o ângulo entre o vetor ombro→quadril e a vertical.
        0° = em pé, 90° = deitado.
        """
        ombro_esq = landmarks[self.OMBRO_ESQ]
        ombro_dir = landmarks[self.OMBRO_DIR]
        quadril_esq = landmarks[self.QUADRIL_ESQ]
        quadril_dir = landmarks[self.QUADRIL_DIR]
        
        # Centro dos ombros e quadris
        ombro_x = (ombro_esq.x + ombro_dir.x) / 2 * largura
        ombro_y = (ombro_esq.y + ombro_dir.y) / 2 * altura
        quadril_x = (quadril_esq.x + quadril_dir.x) / 2 * largura
        quadril_y = (quadril_esq.y + quadril_dir.y) / 2 * altura
        
        # Vetor ombro→quadril
        dx = quadril_x - ombro_x
        dy = quadril_y - ombro_y
        
        # Ângulo com a vertical
        angulo = abs(np.degrees(np.arctan2(dx, dy)))
        
        return angulo, (ombro_x, ombro_y, quadril_x, quadril_y)
    
    def detectar_queda(self, frame):
        """
        Detecta queda em um frame.
        
        Returns:
            dict com:
            - queda: bool
            - confianca: float
            - pose: landmarks detectados
        """
        altura, largura = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.pose.process(rgb)
        
        if not resultado.pose_landmarks:
            return {"queda": False, "confianca": 0.0, "pose": None}
        
        landmarks = resultado.pose_landmarks.landmark
        
        # Verificar visibilidade dos landmarks
        visibilidade = min(
            landmarks[self.OMBRO_ESQ].visibility,
            landmarks[self.OMBRO_DIR].visibility,
            landmarks[self.QUADRIL_ESQ].visibility,
            landmarks[self.QUADRIL_DIR].visibility
        )
        
        if visibilidade < 0.5:
            return {"queda": False, "confianca": 0.0, "pose": landmarks}
        
        # Calcular inclinação
        angulo, centros = self.calcular_inclinacao(landmarks, largura, altura)
        
        # Adicionar ao histórico
        self.historico.append(angulo)
        if len(self.historico) > self.max_historico:
            self.historico.pop(0)
        
        # Detectar queda:
        # 1. Inclinação > 60° (corpo deitado)
        # 2. Transição rápida (mudança > 40° em < 1s)
        
        queda = False
        confianca = 0.0
        
        if len(self.historico) >= 5:
            angulo_atual = self.historico[-1]
            angulo_anterior = self.historico[0]
            variacao = angulo_atual - angulo_anterior
            
            # Queda: inclinação alta + variação rápida
            if angulo_atual > 60:
                confianca = min(angulo_atual / 90, 1.0)
                if variacao > 30:
                    queda = True
                    confianca = min(confianca + 0.2, 1.0)
        
        return {
            "queda": queda,
            "confianca": confianca,
            "angulo": angulo,
            "pose": landmarks
        }
    
    def monitorar(self, duracao=None, callback=None, mostrar=True):
        """Monitora queda continuamente."""
        self.iniciar()
        inicio = datetime.now(timezone.utc)
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                resultado = self.detectar_queda(frame)
                
                # Desenhar pose
                if resultado["pose"] and mostrar:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        resultado["pose"],
                        self.mp_pose.POSE_CONNECTIONS
                    )
                    
                    # Mostrar ângulo
                    if "angulo" in resultado:
                        cv2.putText(
                            frame,
                            f"Angulo: {resultado['angulo']:.1f}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0) if not resultado["queda"] else (0, 0, 255),
                            2
                        )
                
                if resultado["queda"]:
                    print(f"[Libero] QUEDA DETECTADA! Confiança: {resultado['confianca']:.2f}")
                    if callback:
                        callback(resultado)
                
                if mostrar:
                    cv2.imshow("Libero - Queda", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if duracao:
                    elapsed = (datetime.now(timezone.utc) - inicio).total_seconds()
                    if elapsed >= duracao:
                        break
        
        finally:
            self.parar()


if __name__ == "__main__":
    detector = DetectorQueda()
    detector.monitorar(duracao=30)
