"""
controle.py — Modo Manual com múltiplas regiões
Atalho: F8 para capturar todas as regiões
"""

import tkinter as tk
from tkinter import ttk
import threading
import traceback

from captura  import extrair_texto_com_coords
from traducao import traduzir_em_lote, set_idioma_alvo, get_idiomas_disponiveis
from overlay  import Overlay
from seletor  import Seletor


class JanelaControle:

    def __init__(self):
        self.root    = tk.Tk()
        self.overlay = Overlay()
        self.overlay.set_root(self.root)
        self.seletor = Seletor(self.root)
        self.regioes = []   # lista de {"regiao": dict, "nome": str}

        self._build_ui()
        self.root.bind("<F8>", lambda e: self._capturar_todas_thread())

    # ───────────────── UI ─────────────────

    def _build_ui(self):
        W, H = 300, 420
        self.root.title("Tradutor de Tela")
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#080810")
        self.root.overrideredirect(True)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{sw-W-16}+{sh-H-50}")
        self.root.protocol("WM_DELETE_WINDOW", self.encerrar)

        # ── Barra superior ──
        barra = tk.Frame(self.root, bg="#0d0d20", height=30)
        barra.pack(fill="x")
        barra.bind("<ButtonPress-1>", self._drag_start)
        barra.bind("<B1-Motion>",     self._drag_move)

        tk.Label(
            barra, text="🌐 Tradutor de Tela",
            bg="#0d0d20", fg="#a78bfa",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=10)

        tk.Button(
            barra, text="✕",
            bg="#0d0d20", fg="#ff5555",
            bd=0, cursor="hand2",
            command=self.encerrar
        ).pack(side="right", padx=10)

        # ── Corpo ──
        corpo = tk.Frame(self.root, bg="#080810")
        corpo.pack(fill="both", expand=True, padx=14, pady=8)

        # ── Seletor de idioma ──
        frm_idioma = tk.Frame(corpo, bg="#080810")
        frm_idioma.pack(fill="x", pady=(0, 6))

        tk.Label(
            frm_idioma, text="Traduzir para:",
            bg="#080810", fg="#a78bfa",
            font=("Segoe UI", 8, "bold")
        ).pack(side="left")

        self._idioma_var = tk.StringVar(value="Português")
        self._idiomas    = get_idiomas_disponiveis()   # dict {nome: codigo}

        self._btn_idioma = tk.Button(
            frm_idioma,
            textvariable=self._idioma_var,
            bg="#1a1a3a", fg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=8, pady=3,
            command=self._abrir_menu_idioma
        )
        self._btn_idioma.pack(side="right")

        # ── Botões principais ──
        self._botao(corpo, "⬚ Adicionar Região", "#1a1a3a", "#a78bfa",
                    self._adicionar_regiao).pack(fill="x", pady=3)

        self.btn_capturar = self._botao(
            corpo, "📸 Capturar Tudo (F8)", "#2a2a5a", "white",
            self._capturar_todas_thread, state="disabled"
        )
        self.btn_capturar.pack(fill="x", pady=3)

        self._botao(corpo, "🧹 Limpar Tela", "#333333", "white",
                    self.overlay.limpar).pack(fill="x", pady=3)

        # ── Lista de regiões ──
        tk.Label(
            corpo, text="Regiões:",
            bg="#080810", fg="#a78bfa",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(8, 2))

        # Frame com scroll para a lista
        frame_scroll = tk.Frame(corpo, bg="#080810")
        frame_scroll.pack(fill="both", expand=True)

        canvas_lista = tk.Canvas(frame_scroll, bg="#080810",
                                 highlightthickness=0, height=160)
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical",
                                 command=canvas_lista.yview)
        canvas_lista.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas_lista.pack(side="left", fill="both", expand=True)

        self.lista_frame = tk.Frame(canvas_lista, bg="#080810")
        self._lista_window = canvas_lista.create_window(
            (0, 0), window=self.lista_frame, anchor="nw"
        )

        self.lista_frame.bind("<Configure>", lambda e: canvas_lista.configure(
            scrollregion=canvas_lista.bbox("all")
        ))
        canvas_lista.bind("<Configure>", lambda e: canvas_lista.itemconfig(
            self._lista_window, width=e.width
        ))

        self._canvas_lista = canvas_lista

        # ── Status ──
        self.lbl_status = tk.Label(
            corpo, text="Aguardando...",
            bg="#080810", fg="#555577",
            font=("Segoe UI", 8)
        )
        self.lbl_status.pack(pady=4)

    def _botao(self, pai, texto, bg, fg, comando, state="normal"):
        return tk.Button(
            pai, text=texto, bg=bg, fg=fg,
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2",
            pady=6, bd=0,
            command=comando,
            state=state
        )

    # ─────────────── DRAG JANELA ───────────────

    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + (e.x - self._dx)
        y = self.root.winfo_y() + (e.y - self._dy)
        self.root.geometry(f"+{x}+{y}")

    # ─────────────── STATUS ───────────────

    def _set_status(self, texto, cor="#555577"):
        self.lbl_status.config(text=texto, fg=cor)

    # ─────────────── MENU DE IDIOMA ───────────────

    def _abrir_menu_idioma(self):
        """Abre janela de busca/seleção de idioma."""
        win = tk.Toplevel(self.root)
        win.title("Selecionar idioma")
        win.geometry("220x320")
        win.configure(bg="#0d0d20")
        win.attributes("-topmost", True)
        win.resizable(False, False)

        tk.Label(
            win, text="Buscar idioma:",
            bg="#0d0d20", fg="#a78bfa",
            font=("Segoe UI", 9, "bold")
        ).pack(padx=10, pady=(10, 4), anchor="w")

        busca_var = tk.StringVar()
        entry = tk.Entry(
            win, textvariable=busca_var,
            bg="#1a1a3a", fg="white",
            insertbackground="white",
            relief="flat", font=("Segoe UI", 9), bd=6
        )
        entry.pack(fill="x", padx=10)
        entry.focus_set()

        listbox = tk.Listbox(
            win,
            bg="#111128", fg="white",
            selectbackground="#7b2fff",
            font=("Segoe UI", 9),
            relief="flat", bd=0,
            activestyle="none"
        )
        listbox.pack(fill="both", expand=True, padx=10, pady=6)

        nomes = sorted(self._idiomas.keys())

        def atualizar_lista(*_):
            filtro = busca_var.get().lower()
            listbox.delete(0, "end")
            for nome in nomes:
                if filtro in nome.lower():
                    listbox.insert("end", nome)

        def selecionar(e=None):
            sel = listbox.curselection()
            if not sel:
                return
            nome   = listbox.get(sel[0])
            codigo = self._idiomas[nome]
            self._idioma_var.set(nome)
            set_idioma_alvo(codigo)
            win.destroy()

        busca_var.trace_add("write", atualizar_lista)
        listbox.bind("<Double-Button-1>", selecionar)
        listbox.bind("<Return>", selecionar)
        entry.bind("<Return>", selecionar)

        atualizar_lista()

    # ─────────────── REGIÕES ───────────────

    def _adicionar_regiao(self):
        self.root.withdraw()
        self.root.after(150, self._abrir_seletor)

    def _abrir_seletor(self):
        regiao = self.seletor.selecionar()
        self.root.deiconify()

        if not regiao:
            return

        idx  = len(self.regioes) + 1
        item = {"regiao": regiao, "nome": f"Região {idx}"}
        self.regioes.append(item)
        self._adicionar_item_lista(item)
        self.btn_capturar.config(state="normal")

    def _adicionar_item_lista(self, item: dict):
        row = tk.Frame(self.lista_frame, bg="#111128", pady=3)
        row.pack(fill="x", pady=2, padx=2)

        # Nome editável
        var = tk.StringVar(value=item["nome"])

        def salvar_nome(*_):
            novo = var.get().strip()
            if novo:
                item["nome"] = novo

        entry = tk.Entry(
            row, textvariable=var,
            bg="#1a1a3a", fg="#a78bfa",
            font=("Segoe UI", 8),
            relief="flat", bd=4,
            insertbackground="#a78bfa",
            width=14
        )
        entry.pack(side="left", padx=(6, 0))
        entry.bind("<FocusOut>", salvar_nome)
        entry.bind("<Return>",   salvar_nome)

        # Botão capturar individual
        btn_cap = tk.Button(
            row, text="📸",
            bg="#2a2a5a", fg="white",
            bd=0, cursor="hand2",
            font=("Segoe UI", 9),
            command=lambda i=item: self._capturar_uma_thread(i)
        )
        btn_cap.pack(side="left", padx=4)

        # Botão remover
        def remover():
            self.regioes.remove(item)
            row.destroy()
            if not self.regioes:
                self.btn_capturar.config(state="disabled")

        tk.Button(
            row, text="✕",
            bg="#111128", fg="#ff5555",
            bd=0, cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            command=remover
        ).pack(side="right", padx=4)

    # ─────────────── CAPTURA ───────────────

    def _capturar_todas_thread(self):
        if not self.regioes:
            return
        self.btn_capturar.config(state="disabled")
        threading.Thread(target=self._capturar_todas, daemon=True).start()

    def _capturar_uma_thread(self, item: dict):
        threading.Thread(
            target=self._capturar_regioes, args=([item],), daemon=True
        ).start()

    def _capturar_todas(self):
        self._capturar_regioes(self.regioes)
        self.btn_capturar.config(state="normal")

    def _capturar_regioes(self, itens: list):
        try:
            self.overlay.criar()
            self.overlay.mostrar()

            todos_blocos = []
            for item in itens:
                self._set_status(f"🔍 {item['nome']}...", "#f0c040")
                blocos = extrair_texto_com_coords(item["regiao"])
                if blocos:
                    todos_blocos.append((blocos, item["regiao"]))

            if not todos_blocos:
                self._set_status("Sem texto detectado", "#555577")
                return

            self._set_status("🌐 Traduzindo...", "#a78bfa")

            resultados = []
            for blocos, regiao in todos_blocos:
                blocos_trad = traduzir_em_lote(blocos)
                resultados.append((blocos_trad, regiao))

            self.overlay.desenhar_multiplos(resultados)

            total = sum(len(b) for b, _ in resultados)
            self._set_status(f"✓ {total} bloco(s) — F8 p/ novo", "#44cc88")

        except Exception as e:
            print(f"[Erro] {e}")
            traceback.print_exc()
            self._set_status("Erro ao processar", "#cc4444")

    # ─────────────── APP ───────────────

    def iniciar(self):
        self.root.mainloop()

    def encerrar(self):
        self.overlay.destruir()
        self.root.destroy()