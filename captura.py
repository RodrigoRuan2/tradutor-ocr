"""
captura.py
Captura uma região específica da tela, pré-processa com OpenCV
e extrai texto com EasyOCR (GPU se disponível, CPU como fallback).
"""

import mss
import cv2
import numpy as np
import easyocr

# ── Reader único: tenta GPU, cai pra CPU se falhar ──
print("[EasyOCR] Carregando modelo...")
try:
    reader = easyocr.Reader(["en"], gpu=True, verbose=False)
    print("[EasyOCR] Usando GPU.")
except Exception:
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    print("[EasyOCR] GPU indisponível, usando CPU.")


def capturar_regiao(regiao: dict) -> np.ndarray:
    with mss.mss() as sct:
        shot = sct.grab(regiao)
        img  = np.array(shot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def extrair_texto_com_coords(regiao: dict) -> list:
    try:
        img       = capturar_regiao(regiao)
        resultados = reader.readtext(img)

        blocos = []
        for bbox, texto, conf in resultados:
            if conf < 0.3 or not texto.strip():
                continue
            blocos.append({
                "texto": texto,
                "x": int(bbox[0][0]) + regiao["left"],
                "y": int(bbox[0][1]) + regiao["top"],
            })

        if not blocos:
            return []

        texto_unico = " ".join(b["texto"] for b in blocos)
        return [{
            "texto": texto_unico,
            "x":     regiao["left"],
            "y":     regiao["top"],
            "w":     regiao["width"],
            "h":     regiao["height"],
        }]

    except Exception as e:
        print(f"[Erro OCR] {e}")
        return []