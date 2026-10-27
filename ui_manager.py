import tkinter as tk
from tkinter import ttk, messagebox
import time
import math
from game_logic import (
    MemoryGameLogic,
    STATE_MEMORIZE,
    STATE_WAITING_INPUT,
    STATE_ANIMATING,
    STATE_EVALUATING,
    STATE_GAME_OVER
)
from storage import load_leaderboard, save_score, is_top_score, format_time

# Paleta de colores para la interfaz
PALETTE = {
    "bg": "#0f172a",          # Azul pizarra oscuro
    "hud_bg": "#1e293b",      # HUD oscuro
    "card_back": "#334155",   # Dorso de carta
    "card_back_hover": "#475569",
    "card_border": "#64748b",
    "card_matched": "#10b981",# Borde verde al acertar
    "accent": "#38bdf8",      # Azul cielo moderno
    "text": "#f8fafc",
    "text_muted": "#94a3b8",
    "btn_primary": "#0284c7",
    "btn_danger": "#e11d48",
    "btn_success": "#059669",
}

class FlagMemoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Juego de Memoria de Banderas")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)
        self.root.configure(bg=PALETTE["bg"])

        self.difficulty_var = tk.StringVar(value="Fácil (4x4)")
        self.shuffle_var = tk.BooleanVar(value=True)
        self.penalty_var = tk.BooleanVar(value=True)

        self.logic = None
        self.card_widgets = []
        self.is_running = True

        # Animación de flip en progreso: {card_idx: {"progress": float, "direction": int, "target": bool}}
        self.animating_cards = {}

        self.current_view = "MENU"
        self.setup_menu_view()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ==========================================
    # 1. VISTA: MENÚ PRINCIPAL
    # ==========================================
    def setup_menu_view(self):
        self.current_view = "MENU"
        self.clear_root()

        container = tk.Frame(self.root, bg=PALETTE["bg"])
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Título
        title_lbl = tk.Label(
            container,
            text="JUEGO DE MEMORIA\nBANDERAS DEL MUNDO",
            font=("Segoe UI", 26, "bold"),
            fg=PALETTE["accent"],
            bg=PALETTE["bg"],
            justify=tk.CENTER
        )
        title_lbl.pack(pady=(0, 30))

        # Cuadro de Opciones
        opts_frame = tk.Frame(container, bg=PALETTE["hud_bg"], padx=25, pady=20, highlightbackground=PALETTE["card_border"], highlightthickness=1)
        opts_frame.pack(fill=tk.X, pady=(0, 25))

        tk.Label(opts_frame, text="Dificultad:", font=("Segoe UI", 12, "bold"), fg=PALETTE["text"], bg=PALETTE["hud_bg"]).pack(anchor=tk.W, pady=(0, 5))
        
        diff_combo = ttk.Combobox(
            opts_frame,
            textvariable=self.difficulty_var,
            values=["Fácil (4x4)", "Normal (6x6)", "Difícil (8x8)"],
            state="readonly",
            font=("Segoe UI", 11)
        )
        diff_combo.pack(fill=tk.X, pady=(0, 15))

        # Checkbox Mecánica Especial
        chk_shuffle = tk.Checkbutton(
            opts_frame,
            text="Barajar al fallar (Mecánica Dinámica)",
            variable=self.shuffle_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["hud_bg"],
            selectcolor=PALETTE["bg"],
            activebackground=PALETTE["hud_bg"],
            activeforeground=PALETTE["text"]
        )
        chk_shuffle.pack(anchor=tk.W, pady=(0, 8))

        # Checkbox Penalización
        chk_penalty = tk.Checkbutton(
            opts_frame,
            text="Penalización de +5s por cada fallo",
            variable=self.penalty_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["hud_bg"],
            selectcolor=PALETTE["bg"],
            activebackground=PALETTE["hud_bg"],
            activeforeground=PALETTE["text"]
        )
        chk_penalty.pack(anchor=tk.W)

        # Botones de Acción
        btn_play = tk.Button(
            container,
            text="▶ JUGAR",
            font=("Segoe UI", 14, "bold"),
            bg=PALETTE["btn_primary"],
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            bd=0,
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.start_game
        )
        btn_play.pack(fill=tk.X, pady=(0, 10))

        btn_leaderboard = tk.Button(
            container,
            text="🏆 MEJORES TIEMPOS",
            font=("Segoe UI", 11, "bold"),
            bg=PALETTE["hud_bg"],
            fg=PALETTE["text"],
            activebackground=PALETTE["card_back"],
            activeforeground=PALETTE["text"],
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.setup_leaderboard_view
        )
        btn_leaderboard.pack(fill=tk.X, pady=(0, 10))

        btn_exit = tk.Button(
            container,
            text="SALIR",
            font=("Segoe UI", 11),
            bg=PALETTE["bg"],
            fg=PALETTE["text_muted"],
            activebackground=PALETTE["bg"],
            activeforeground=PALETTE["text"],
            bd=0,
            pady=6,
            cursor="hand2",
            command=self.root.quit
        )
        btn_exit.pack(fill=tk.X)

    # ==========================================
    # 2. VISTA: TABLERO DE JUEGO (GAME BOARD)
    # ==========================================
    def start_game(self):
        self.current_view = "GAME"
        self.clear_root()

        penalty_sec = 5 if self.penalty_var.get() else 0
        self.logic = MemoryGameLogic(
            difficulty_name=self.difficulty_var.get(),
            shuffle_on_error=self.shuffle_var.get(),
            time_penalty_seconds=penalty_sec
        )

        # 1. Header / HUD
        hud = tk.Frame(self.root, bg=PALETTE["hud_bg"], height=70, padx=20, pady=10)
        hud.pack(fill=tk.X, side=tk.TOP)

        self.lbl_timer = tk.Label(
            hud, text="Memoriza: 3.0s", font=("Segoe UI", 15, "bold"),
            fg=PALETTE["accent"], bg=PALETTE["hud_bg"]
        )
        self.lbl_timer.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_errors = tk.Label(
            hud, text="Errores: 0", font=("Segoe UI", 13),
            fg=PALETTE["text"], bg=PALETTE["hud_bg"]
        )
        self.lbl_errors.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_pairs = tk.Label(
            hud, text=f"Pares: 0 / {self.logic.total_pairs}", font=("Segoe UI", 13),
            fg=PALETTE["text_muted"], bg=PALETTE["hud_bg"]
        )
        self.lbl_pairs.pack(side=tk.LEFT)

        btn_menu = tk.Button(
            hud, text="Menú Principal", font=("Segoe UI", 10),
            bg=PALETTE["card_back"], fg=PALETTE["text"], bd=0, padx=12, pady=5,
            cursor="hand2", command=self.setup_menu_view
        )
        btn_menu.pack(side=tk.RIGHT, padx=(10, 0))

        btn_restart = tk.Button(
            hud, text="Reiniciar", font=("Segoe UI", 10, "bold"),
            bg=PALETTE["btn_danger"], fg="#ffffff", bd=0, padx=12, pady=5,
            cursor="hand2", command=self.start_game
        )
        btn_restart.pack(side=tk.RIGHT)

        # 2. Área del Tablero
        self.board_frame = tk.Frame(self.root, bg=PALETTE["bg"], padx=15, pady=15)
        self.board_frame.pack(fill=tk.BOTH, expand=True)

        self.build_board()
        self.run_game_loop()

    def build_board(self):
        """Construye los widgets de las cartas adaptándose a la cuadrícula."""
        for widget in self.board_frame.winfo_children():
            widget.destroy()

        self.card_widgets = []
        rows = self.logic.config["rows"]
        cols = self.logic.config["cols"]

        for r in range(rows):
            self.board_frame.rowconfigure(r, weight=1)
        for c in range(cols):
            self.board_frame.columnconfigure(c, weight=1)

        for i in range(len(self.logic.cards)):
            r = i // cols
            c = i % cols

            # Canvas para dibujar cada carta y renderizar animaciones suaves
            canvas = tk.Canvas(
                self.board_frame,
                bg=PALETTE["bg"],
                highlightthickness=0,
                cursor="hand2"
            )
            canvas.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            canvas.bind("<Button-1>", lambda e, idx=i: self.on_card_click(idx))
            self.card_widgets.append(canvas)

        self.root.update_idletasks()
        self.redraw_all_cards()

    def on_card_click(self, index):
        """Maneja el evento de clic con bloqueo de inputs mientras se anima o evalúa."""
        if self.logic.state != STATE_WAITING_INPUT:
            return

        card = self.logic.cards[index]
        if card.revealed or card.matched:
            return

        # Iniciar animación de flip
        self.start_flip_animation(index, target_revealed=True)
        res = self.logic.select_card(index)

    def start_flip_animation(self, index, target_revealed):
        """Inicia el efecto de compresión y expansión en el eje X (3D falso)."""
        self.animating_cards[index] = {
            "scale_x": 1.0,
            "phase": "collapsing",  # collapsing -> expanding
            "target_revealed": target_revealed
        }

    def update_card_animations(self):
        """Avanza los fotogramas de animación de volteo."""
        to_delete = []
        for idx, anim in self.animating_cards.items():
            if anim["phase"] == "collapsing":
                anim["scale_x"] -= 0.18
                if anim["scale_x"] <= 0.05:
                    anim["scale_x"] = 0.05
                    anim["phase"] = "expanding"
                    # Se cambia el estado visual de la carta en el punto medio
                    self.logic.cards[idx].revealed = anim["target_revealed"]
            elif anim["phase"] == "expanding":
                anim["scale_x"] += 0.18
                if anim["scale_x"] >= 1.0:
                    anim["scale_x"] = 1.0
                    to_delete.append(idx)

            self.draw_single_card(idx, scale_x=anim["scale_x"])

        for idx in to_delete:
            del self.animating_cards[idx]

    def draw_single_card(self, index, scale_x=1.0):
        """Dibuja una carta en su respectivo canvas con soporte para escala X."""
        canvas = self.card_widgets[index]
        card = self.logic.cards[index]

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10 or h < 10:
            return

        canvas.delete("all")

        # Ancho efectivo tras compresión en eje X
        card_w = max(4, int(w * scale_x))
        offset_x = (w - card_w) // 2

        # Borde y estado
        border_color = PALETTE["card_matched"] if card.matched else PALETTE["card_border"]
        border_width = 3 if card.matched else 1

        if card.revealed or card.matched:
            # Fondo de la carta boca arriba
            canvas.create_rectangle(
                offset_x, 0, offset_x + card_w, h,
                fill="#ffffff", outline=border_color, width=border_width
            )
            # Dibujar la bandera dentro de la carta
            self.draw_flag(canvas, card.flag, offset_x + 6, 6, max(4, card_w - 12), max(4, h - 30))
            
            # Nombre de la bandera
            if card_w > 50 and h > 50:
                font_size = 9 if self.logic.config["rows"] <= 6 else 7
                canvas.create_text(
                    w // 2, h - 14,
                    text=card.flag["name"],
                    font=("Segoe UI", font_size, "bold"),
                    fill="#1e293b"
                )
        else:
            # Dorso de la carta boca abajo
            canvas.create_rectangle(
                offset_x, 0, offset_x + card_w, h,
                fill=PALETTE["card_back"], outline=border_color, width=border_width
            )
            # Ícono sutil en el dorso
            if card_w > 20 and h > 20:
                canvas.create_oval(
                    w // 2 - 8 * scale_x, h // 2 - 8,
                    w // 2 + 8 * scale_x, h // 2 + 8,
                    fill=PALETTE["card_border"], outline=""
                )

    def draw_flag(self, canvas, flag, x, y, w, h):
        """Dibuja de forma procedural la bandera correspondiente."""
        ftype = flag["type"]
        colors = flag["colors"]

        if ftype == "horizontal":
            # 3 franjas horizontales
            h_slice = h / 3
            for i, c in enumerate(colors[:3]):
                canvas.create_rectangle(x, y + i * h_slice, x + w, y + (i + 1) * h_slice, fill=c, outline="")

        elif ftype == "horizontal_two":
            # 2 franjas horizontales
            h_slice = h / 2
            canvas.create_rectangle(x, y, x + w, y + h_slice, fill=colors[0], outline="")
            canvas.create_rectangle(x, y + h_slice, x + w, y + h, fill=colors[1], outline="")

        elif ftype == "vertical":
            # 3 franjas verticales
            w_slice = w / 3
            for i, c in enumerate(colors[:3]):
                canvas.create_rectangle(x + i * w_slice, y, x + (i + 1) * w_slice, y + h, fill=c, outline="")

        elif ftype == "vertical_split":
            # Portugal (2 franjas: 2/5 verde, 3/5 rojo)
            canvas.create_rectangle(x, y, x + w * 0.4, y + h, fill=colors[0], outline="")
            canvas.create_rectangle(x + w * 0.4, y, x + w, y + h, fill=colors[1], outline="")

        elif ftype == "nordic":
            # Suecia (fondo azul, cruz amarilla)
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            # Cruz
            canvas.create_rectangle(x, y + h * 0.38, x + w, y + h * 0.62, fill=colors[1], outline="")
            canvas.create_rectangle(x + w * 0.28, y, x + w * 0.45, y + h, fill=colors[1], outline="")

        elif ftype == "nordic_red" or ftype == "nordic_white":
            # Dinamarca o Finlandia
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            canvas.create_rectangle(x, y + h * 0.38, x + w, y + h * 0.62, fill=colors[1], outline="")
            canvas.create_rectangle(x + w * 0.28, y, x + w * 0.45, y + h, fill=colors[1], outline="")

        elif ftype == "nordic_norway":
            # Noruega
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            # Cruz blanca
            canvas.create_rectangle(x, y + h * 0.33, x + w, y + h * 0.67, fill=colors[2], outline="")
            canvas.create_rectangle(x + w * 0.23, y, x + w * 0.48, y + h, fill=colors[2], outline="")
            # Cruz azul interior
            canvas.create_rectangle(x, y + h * 0.40, x + w, y + h * 0.60, fill=colors[1], outline="")
            canvas.create_rectangle(x + w * 0.28, y, x + w * 0.43, y + h, fill=colors[1], outline="")

        elif ftype == "swiss_cross":
            # Suiza (rojo con cruz blanca)
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            cx, cy = x + w / 2, y + h / 2
            cw, ch = w * 0.55, h * 0.22
            canvas.create_rectangle(cx - cw/2, cy - ch/2, cx + cw/2, cy + ch/2, fill=colors[1], outline="")
            canvas.create_rectangle(cx - ch/2, cy - cw/2, cx + ch/2, cy + cw/2, fill=colors[1], outline="")

        elif ftype == "circle":
            # Japón (círculo rojo)
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            r = min(w, h) * 0.28
            canvas.create_oval(x + w/2 - r, y + h/2 - r, x + w/2 + r, y + h/2 + r, fill=colors[1], outline="")

        elif ftype == "colombia":
            # Colombia (50% amarillo, 25% azul, 25% rojo)
            canvas.create_rectangle(x, y, x + w, y + h * 0.5, fill=colors[0], outline="")
            canvas.create_rectangle(x, y + h * 0.5, x + w, y + h * 0.75, fill=colors[1], outline="")
            canvas.create_rectangle(x, y + h * 0.75, x + w, y + h, fill=colors[2], outline="")

        elif ftype == "brazil":
            # Brasil (verde, rombo amarillo, círculo azul)
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            canvas.create_polygon(x + w/2, y + 2, x + w - 2, y + h/2, x + w/2, y + h - 2, x + 2, y + h/2, fill=colors[1])
            r = min(w, h) * 0.22
            canvas.create_oval(x + w/2 - r, y + h/2 - r, x + w/2 + r, y + h/2 + r, fill=colors[2], outline="")

        else:
            # Dibujo estándar de franjas
            canvas.create_rectangle(x, y, x + w, y + h, fill=colors[0], outline="")
            if len(colors) > 1:
                canvas.create_rectangle(x, y + h * 0.5, x + w, y + h, fill=colors[1], outline="")

        # Borde exterior de la bandera
        canvas.create_rectangle(x, y, x + w, y + h, outline="#cbd5e1", width=1)

    def redraw_all_cards(self):
        for i in range(len(self.card_widgets)):
            self.draw_single_card(i)

    # ==========================================
    # 3. GAME LOOP PRINCIPAL
    # ==========================================
    def run_game_loop(self):
        if self.current_view != "GAME":
            return

        now = time.time()

        # Fase 1: Memorización inicial
        if self.logic.state == STATE_MEMORIZE:
            elapsed_memo = now - self.logic.memo_start_time
            remaining = max(0.0, self.logic.memo_duration - elapsed_memo)
            self.lbl_timer.config(text=f"Memoriza: {remaining:.1f}s")

            if remaining <= 0:
                self.logic.start_gameplay_phase()
                self.redraw_all_cards()

        # Fase 2 y 3: Jugando
        elif self.logic.state in (STATE_WAITING_INPUT, STATE_EVALUATING):
            ms = self.logic.get_current_time_ms()
            self.lbl_timer.config(text=f"Tiempo: {format_time(ms)}")
            self.lbl_errors.config(text=f"Errores: {self.logic.errors}")
            self.lbl_pairs.config(text=f"Pares: {self.logic.matches_count} / {self.logic.total_pairs}")

            # Evaluación tras mostrar cartas erróneas
            if self.logic.state == STATE_EVALUATING:
                if (now - self.logic.eval_start_time) >= self.logic.eval_duration:
                    c1_idx = self.logic.first_selected
                    c2_idx = self.logic.second_selected
                    result = self.logic.evaluate_pair()

                    if result == "win":
                        self.on_game_won()
                        return
                    elif result == "mismatch":
                        # Iniciar animación de regreso
                        self.start_flip_animation(c1_idx, target_revealed=False)
                        self.start_flip_animation(c2_idx, target_revealed=False)
                    elif result == "match":
                        self.redraw_all_cards()

        # Actualizar animaciones de volteo
        if self.animating_cards:
            self.update_card_animations()

        # Ciclo a ~60 FPS (16ms)
        self.root.after(16, self.run_game_loop)

    def on_game_won(self):
        """Muestra los resultados finales y gestiona el Leaderboard."""
        self.current_view = "GAMEOVER"
        self.redraw_all_cards()
        final_time_ms = self.logic.elapsed_time_ms
        errors = self.logic.errors
        diff = self.logic.difficulty_name

        qualifies = is_top_score(diff, final_time_ms, errors)

        self.setup_game_over_view(final_time_ms, errors, diff, qualifies)

    # ==========================================
    # 4. VISTA: RESULTADOS Y LEADERBOARD
    # ==========================================
    def setup_game_over_view(self, time_ms, errors, diff, qualifies):
        self.clear_root()

        container = tk.Frame(self.root, bg=PALETTE["bg"])
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            container, text="¡VICTORIA!", font=("Segoe UI", 28, "bold"),
            fg=PALETTE["card_matched"], bg=PALETTE["bg"]
        ).pack(pady=(0, 10))

        info_frame = tk.Frame(container, bg=PALETTE["hud_bg"], padx=30, pady=20, highlightbackground=PALETTE["card_border"], highlightthickness=1)
        info_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            info_frame, text=f"Dificultad: {diff}", font=("Segoe UI", 12),
            fg=PALETTE["text_muted"], bg=PALETTE["hud_bg"]
        ).pack(pady=2)

        tk.Label(
            info_frame, text=f"Tiempo Final: {format_time(time_ms)}", font=("Segoe UI", 18, "bold"),
            fg=PALETTE["accent"], bg=PALETTE["hud_bg"]
        ).pack(pady=5)

        tk.Label(
            info_frame, text=f"Errores cometidos: {errors}", font=("Segoe UI", 12),
            fg=PALETTE["text"], bg=PALETTE["hud_bg"]
        ).pack(pady=2)

        if qualifies:
            tk.Label(
                info_frame, text="🎉 ¡Nuevo récord! Entraste en el Top 10",
                font=("Segoe UI", 11, "bold"), fg="#fbbf24", bg=PALETTE["hud_bg"]
            ).pack(pady=(10, 5))

            name_frame = tk.Frame(info_frame, bg=PALETTE["hud_bg"])
            name_frame.pack(fill=tk.X, pady=(5, 0))

            tk.Label(name_frame, text="Tu Nombre:", font=("Segoe UI", 10), fg=PALETTE["text"], bg=PALETTE["hud_bg"]).pack(side=tk.LEFT)
            entry_name = tk.Entry(name_frame, font=("Segoe UI", 11), bg=PALETTE["bg"], fg=PALETTE["text"], insertbackground=PALETTE["text"])
            entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
            entry_name.focus_set()

            def submit_record():
                player_name = entry_name.get() or "Jugador"
                save_score(diff, player_name, time_ms, errors)
                self.setup_leaderboard_view()

            btn_save = tk.Button(
                container, text="Guardar Récord", font=("Segoe UI", 12, "bold"),
                bg=PALETTE["btn_success"], fg="#ffffff", bd=0, pady=8, cursor="hand2",
                command=submit_record
            )
            btn_save.pack(fill=tk.X, pady=(0, 10))

        btn_again = tk.Button(
            container, text="Jugar de Nuevo", font=("Segoe UI", 12, "bold"),
            bg=PALETTE["btn_primary"], fg="#ffffff", bd=0, pady=8, cursor="hand2",
            command=self.start_game
        )
        btn_again.pack(fill=tk.X, pady=(0, 10))

        btn_menu = tk.Button(
            container, text="Volver al Menú", font=("Segoe UI", 11),
            bg=PALETTE["hud_bg"], fg=PALETTE["text"], bd=0, pady=6, cursor="hand2",
            command=self.setup_menu_view
        )
        btn_menu.pack(fill=tk.X)

    def setup_leaderboard_view(self):
        self.current_view = "LEADERBOARD"
        self.clear_root()

        container = tk.Frame(self.root, bg=PALETTE["bg"], padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(container, bg=PALETTE["bg"])
        header.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            header, text="🏆 MEJORES TIEMPOS (TOP 10)", font=("Segoe UI", 20, "bold"),
            fg=PALETTE["accent"], bg=PALETTE["bg"]
        ).pack(side=tk.LEFT)

        btn_back = tk.Button(
            header, text="← Volver al Menú", font=("Segoe UI", 10),
            bg=PALETTE["hud_bg"], fg=PALETTE["text"], bd=0, padx=12, pady=6,
            cursor="hand2", command=self.setup_menu_view
        )
        btn_back.pack(side=tk.RIGHT)

        # Selector de Dificultad para filtrar
        filter_frame = tk.Frame(container, bg=PALETTE["bg"])
        filter_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(filter_frame, text="Ver dificultad:", font=("Segoe UI", 11), fg=PALETTE["text_muted"], bg=PALETTE["bg"]).pack(side=tk.LEFT, padx=(0, 10))
        
        diff_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.difficulty_var,
            values=["Fácil (4x4)", "Normal (6x6)", "Difícil (8x8)"],
            state="readonly",
            font=("Segoe UI", 10)
        )
        diff_combo.pack(side=tk.LEFT)

        # Tabla de puntuaciones
        table_frame = tk.Frame(container, bg=PALETTE["hud_bg"], highlightbackground=PALETTE["card_border"], highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True)

        def refresh_table(event=None):
            for w in table_frame.winfo_children():
                w.destroy()

            # Cabecera
            h_row = tk.Frame(table_frame, bg=PALETTE["card_back"], pady=8, padx=15)
            h_row.pack(fill=tk.X)
            tk.Label(h_row, text="#", font=("Segoe UI", 10, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_back"], width=5, anchor="w").pack(side=tk.LEFT)
            tk.Label(h_row, text="Jugador", font=("Segoe UI", 10, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_back"], width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(h_row, text="Tiempo", font=("Segoe UI", 10, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_back"], width=15, anchor="w").pack(side=tk.LEFT)
            tk.Label(h_row, text="Errores", font=("Segoe UI", 10, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_back"], width=10, anchor="w").pack(side=tk.LEFT)

            data = load_leaderboard()
            scores = data.get(self.difficulty_var.get(), [])

            if not scores:
                tk.Label(
                    table_frame, text="No hay récords registrados en esta dificultad aún.",
                    font=("Segoe UI", 12), fg=PALETTE["text_muted"], bg=PALETTE["hud_bg"], pady=40
                ).pack()
                return

            for i, score in enumerate(scores):
                row_bg = PALETTE["hud_bg"] if i % 2 == 0 else "#243248"
                r = tk.Frame(table_frame, bg=row_bg, pady=6, padx=15)
                r.pack(fill=tk.X)

                medal = "🥇 " if i == 0 else "🥈 " if i == 1 else "🥉 " if i == 2 else f"{i+1}. "
                tk.Label(r, text=medal, font=("Segoe UI", 10, "bold"), fg="#fbbf24" if i < 3 else PALETTE["text"], bg=row_bg, width=5, anchor="w").pack(side=tk.LEFT)
                tk.Label(r, text=score["name"], font=("Segoe UI", 10), fg=PALETTE["text"], bg=row_bg, width=20, anchor="w").pack(side=tk.LEFT)
                tk.Label(r, text=score["time_formatted"], font=("Segoe UI", 10, "bold"), fg=PALETTE["accent"], bg=row_bg, width=15, anchor="w").pack(side=tk.LEFT)
                tk.Label(r, text=str(score["errors"]), font=("Segoe UI", 10), fg=PALETTE["text_muted"], bg=row_bg, width=10, anchor="w").pack(side=tk.LEFT)

        diff_combo.bind("<<ComboboxSelected>>", refresh_table)
        refresh_table()

def main():
    root = tk.Tk()
    app = FlagMemoryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
