"""
seletor.py
Tela de seleção de região cobrindo todos os monitores.
"""

import tkinter as tk
import mss

COR_SELECAO = "#7b2fff"


class Seletor:

    def __init__(self, root_ref):
        self._root    = root_ref
        self._regiao  = None
        self._sx = self._sy = 0
        self._rect_id = None
        self._win     = None
        self._canvas  = None
        self._offset_x = 0
        self._offset_y = 0

    def selecionar(self) -> dict | None:
        self._regiao = None

        # ── Pega bounding box de todos os monitores ──
        with mss.mss() as sct:
            todos = sct.monitors[0]   # índice 0 = virtual screen (todos juntos)
            vx  = todos["left"]
            vy  = todos["top"]
            vlarg = todos["width"]
            valt  = todos["height"]

        # Offset para converter coords do canvas → coords absolutas
        self._offset_x = vx
        self._offset_y = vy

        self._win = tk.Toplevel(self._root)
        win = self._win

        win.geometry(f"{vlarg}x{valt}+{vx}+{vy}")
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.35)
        win.configure(bg="#000000")
        win.overrideredirect(True)
        win.config(cursor="crosshair")

        self._canvas = tk.Canvas(win, bg="#000000", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._canvas.create_text(
            vlarg // 2, valt // 2,
            text="Clique e arraste para selecionar a região  •  ESC para cancelar",
            fill="white",
            font=("Segoe UI", 16),
            tags="instrucao"
        )

        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        win.bind("<Escape>", self._on_esc)

        self._root.wait_window(win)
        return self._regiao

    def _on_press(self, e):
        self._sx, self._sy = e.x, e.y
        self._canvas.delete("instrucao")
        if self._rect_id:
            self._canvas.delete(self._rect_id)

    def _on_drag(self, e):
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            self._sx, self._sy, e.x, e.y,
            outline=COR_SELECAO,
            width=2,
            fill=COR_SELECAO,
            stipple="gray25",
            tags="selecao"
        )

    def _on_release(self, e):
        x1 = min(self._sx, e.x) + self._offset_x
        y1 = min(self._sy, e.y) + self._offset_y
        x2 = max(self._sx, e.x) + self._offset_x
        y2 = max(self._sy, e.y) + self._offset_y
        w, h = x2 - x1, y2 - y1

        if w > 20 and h > 20:
            self._regiao = {"top": y1, "left": x1, "width": w, "height": h}

        self._win.destroy()

    def _on_esc(self, e):
        self._win.destroy()