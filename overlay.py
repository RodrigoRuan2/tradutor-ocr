"""
overlay.py
Cada balão é um Toplevel independente com alpha real (0.85).
Arrastável individualmente, funciona em qualquer monitor.
"""

import tkinter as tk

COR_BALAO_BG   = "#000000"
COR_BALAO_BORD = "#a78bfa"
COR_BALAO_TEXT = "#ffffff"
COR_FECHAR     = "#ff5555"
COR_RESIZE     = "#a78bfa"
COR_TRANS      = "#010101"
COR_REGIAO     = "#a78bfa"
FONTE_BASE     = ("Segoe UI", 11, "bold")
PAD            = 12
RAIO           = 10
ALPHA_BALAO    = 0.85


class Balao:
    """Janela Toplevel independente representando um balão de tradução."""

    def __init__(self, root_ref, texto: str, x: int, y: int,
                 largura_max: int, font_size: int = 11):
        self._root_ref   = root_ref
        self.texto       = texto
        self.font_size   = font_size
        self.largura_max = largura_max
        self.destruido   = False

        self._win    = None
        self._canvas = None
        self._tid    = None
        self._bg     = None
        self._brd    = None
        self._btn_fechar = None
        self._btn_resize = None

        self._dx = self._dy = 0
        self._resize_y  = 0
        self._resize_fs = font_size

        self._criar(x, y)

    def _criar(self, x: int, y: int):
        self._win = tk.Toplevel(self._root_ref)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.attributes("-alpha", ALPHA_BALAO)
        self._win.configure(bg=COR_BALAO_BG)

        # Canvas preto para desenhar o conteúdo
        self._canvas = tk.Canvas(
            self._win, bg=COR_BALAO_BG,
            highlightthickness=2,
            highlightbackground=COR_BALAO_BORD
        )
        self._canvas.pack(fill="both", expand=True)

        self._desenhar_conteudo()
        self._ajustar_tamanho(x, y)

    def _desenhar_conteudo(self):
        self._canvas.delete("all")
        fonte = (FONTE_BASE[0], self.font_size, FONTE_BASE[2])

        # Texto
        self._tid = self._canvas.create_text(
            PAD, PAD,
            text=self.texto,
            anchor="nw",
            font=fonte,
            fill=COR_BALAO_TEXT,
            width=self.largura_max - (PAD * 2),
            justify="left"
        )

        bbox = self._canvas.bbox(self._tid)
        if not bbox:
            return

        _, _, tx2, ty2 = bbox

        # Botão fechar
        self._btn_fechar = self._canvas.create_text(
            tx2 + PAD - 4, 6,
            text="✕", anchor="ne",
            font=("Segoe UI", 9, "bold"),
            fill=COR_FECHAR
        )

        # Botão resize
        self._btn_resize = self._canvas.create_text(
            tx2 + PAD - 4, ty2 + PAD - 4,
            text="⤡", anchor="se",
            font=("Segoe UI", 9, "bold"),
            fill=COR_RESIZE
        )

        self._bind_eventos()

    def _ajustar_tamanho(self, x: int = None, y: int = None):
        """Redimensiona a janela para caber o conteúdo."""
        self._canvas.update_idletasks()
        bbox = self._canvas.bbox("all")
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        w = x2 - x1 + PAD * 2
        h = y2 - y1 + PAD * 2

        if x is None:
            x = self._win.winfo_x()
        if y is None:
            y = self._win.winfo_y()

        self._win.geometry(f"{w}x{h}+{x}+{y}")

    def _bind_eventos(self):
        # Drag — fundo do canvas
        self._canvas.bind("<ButtonPress-1>",   self._drag_start)
        self._canvas.bind("<B1-Motion>",       self._drag_move)

        # Fechar
        self._canvas.tag_bind(self._btn_fechar, "<Button-1>",
                               lambda e: self.destruir())

        # Editar texto (duplo clique)
        self._canvas.tag_bind(self._tid, "<Double-Button-1>",
                               lambda e: self._editar_texto())
        self._canvas.bind("<Double-Button-1>",
                          lambda e: self._editar_texto())

        # Resize
        self._canvas.tag_bind(self._btn_resize, "<ButtonPress-1>",
                               self._resize_start)
        self._canvas.tag_bind(self._btn_resize, "<B1-Motion>",
                               self._resize_move)

    # ─────────────── DRAG ───────────────

    def _drag_start(self, e):
        self._dx = e.x_root - self._win.winfo_x()
        self._dy = e.y_root - self._win.winfo_y()

    def _drag_move(self, e):
        x = e.x_root - self._dx
        y = e.y_root - self._dy
        self._win.geometry(f"+{x}+{y}")

    # ─────────────── FECHAR ───────────────

    def destruir(self):
        if not self.destruido and self._win:
            self.destruido = True
            self._win.destroy()
            self._win = None

    # ─────────────── EDITAR TEXTO ───────────────

    def _editar_texto(self):
        if self.destruido:
            return

        bbox = self._canvas.bbox(self._tid)
        if not bbox:
            return
        x1, y1, x2, _ = bbox

        entry = tk.Entry(
            self._win,
            font=(FONTE_BASE[0], self.font_size, FONTE_BASE[2]),
            bg="#1a0a3a", fg=COR_BALAO_TEXT,
            insertbackground=COR_BALAO_TEXT,
            relief="flat", bd=4,
            width=max(20, (x2 - x1) // 8)
        )
        entry.insert(0, self.texto)
        entry.place(x=x1, y=y1)
        entry.focus_set()
        entry.select_range(0, "end")

        def confirmar(e=None):
            novo = entry.get().strip()
            entry.destroy()
            if novo and novo != self.texto:
                self.texto = novo
                self._canvas.itemconfig(self._tid, text=novo)
                self._ajustar_tamanho()

        entry.bind("<Return>",   confirmar)
        entry.bind("<Escape>",   lambda e: entry.destroy())
        entry.bind("<FocusOut>", confirmar)

    # ─────────────── RESIZE FONTE ───────────────

    def _resize_start(self, e):
        self._resize_y  = e.y_root
        self._resize_fs = self.font_size

    def _resize_move(self, e):
        dy = e.y_root - self._resize_y
        novo_fs = max(8, min(28, self._resize_fs + int(dy / 6)))
        if novo_fs == self.font_size:
            return
        self.font_size = novo_fs
        self._canvas.itemconfig(
            self._tid,
            font=(FONTE_BASE[0], novo_fs, FONTE_BASE[2])
        )
        self._ajustar_tamanho()


class Overlay:
    """Gerencia todos os balões ativos."""

    def __init__(self):
        self._baloes: list[Balao] = []
        self._root_ref = None

    def criar(self):
        """Chamado antes de desenhar — limpa balões anteriores."""
        self.limpar()

    def mostrar(self):
        pass   # balões já ficam visíveis ao serem criados

    def destruir(self):
        self.limpar()

    def limpar(self):
        for b in self._baloes:
            b.destruir()
        self._baloes.clear()

    def _get_root(self):
        """Pega referência ao root via balão existente ou cria um Toplevel base."""
        if not self._root_ref or not self._root_ref.winfo_exists():
            # Cria janela invisível como pai dos Toplevels
            self._root_ref = tk.Tk()
            self._root_ref.withdraw()
        return self._root_ref

    def set_root(self, root: tk.Tk):
        """Recebe o root da JanelaControle para usar como pai dos Toplevels."""
        self._root_ref = root

    def desenhar_multiplos(self, resultados: list):
        """
        resultados: lista de (blocos_traduzidos, regiao)
        Cada bloco válido vira um Balao independente.
        """
        self.limpar()

        for blocos, regiao in resultados:
            blocos_validos = [
                b for b in blocos
                if b.get("traducao") and
                   b.get("traducao", "").lower() != b.get("texto", "").lower()
            ]
            if not blocos_validos:
                continue

            largura_max = min(regiao["width"], 500)
            x = regiao["left"]
            y = regiao["top"]

            for bloco in blocos_validos:
                trad  = bloco.get("traducao", "")
                balao = Balao(
                    self._root_ref, trad,
                    x, y, largura_max
                )
                self._baloes.append(balao)
                # Próximo balão abaixo do anterior
                y += balao._win.winfo_reqheight() + 8 if balao._win else 40