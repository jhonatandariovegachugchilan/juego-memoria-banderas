import random
import time
from storage import FLAGS_DATA

# Estados de la máquina de estados
STATE_MEMORIZE = "STATE_MEMORIZE"
STATE_WAITING_INPUT = "STATE_WAITING_INPUT"
STATE_ANIMATING = "STATE_ANIMATING"
STATE_EVALUATING = "STATE_EVALUATING"
STATE_SHUFFLING = "STATE_SHUFFLING"
STATE_PEEKING = "STATE_PEEKING"
STATE_GAME_OVER = "STATE_GAME_OVER"

DIFFICULTIES = {
    "Fácil (4x4)": {"rows": 4, "cols": 4, "pairs": 8, "flags_pool": FLAGS_DATA[:18], "memo_time": 3.0},
    "Normal (6x6)": {"rows": 6, "cols": 6, "pairs": 18, "flags_pool": FLAGS_DATA[:18], "memo_time": 4.0},
    "Difícil (8x8)": {"rows": 8, "cols": 8, "pairs": 32, "flags_pool": FLAGS_DATA, "memo_time": 5.0},
}

class Card:
    def __init__(self, card_id, flag_data):
        self.card_id = card_id
        self.flag = flag_data
        self.revealed = False   # Si está boca arriba
        self.matched = False    # Si ya fue emparejada
        # Para animación de volteo (flip ratio: 1.0 = normal, 0.0 = colapsado en X)
        self.flip_progress = 1.0
        self.is_flipping = False
        self.target_revealed = False

class MemoryGameLogic:
    def __init__(self, difficulty_name="Fácil (4x4)", shuffle_on_error=True, time_penalty_seconds=5):
        self.difficulty_name = difficulty_name
        self.config = DIFFICULTIES[difficulty_name]
        self.shuffle_on_error = shuffle_on_error
        self.time_penalty_ms = time_penalty_seconds * 1000

        self.cards = []
        self.first_selected = None
        self.second_selected = None
        
        self.errors = 0
        self.matches_count = 0
        self.total_pairs = self.config["pairs"]

        self.state = STATE_MEMORIZE
        self.memo_start_time = 0.0
        self.memo_duration = self.config["memo_time"]

        self.game_start_time = 0.0
        self.elapsed_time_ms = 0
        self.timer_running = False

        self.eval_start_time = 0.0
        self.eval_duration = 1.2  # Segundos antes de voltear cartas erróneas

        self._setup_board()

    def _setup_board(self):
        """Genera y baraja las cartas según la dificultad seleccionada."""
        pool = list(self.config["flags_pool"])
        selected_flags = random.sample(pool, self.config["pairs"])
        
        cards_list = []
        for i, flag in enumerate(selected_flags):
            # Dos cartas por cada bandera (par)
            cards_list.append(Card(i * 2, flag))
            cards_list.append(Card(i * 2 + 1, flag))

        random.shuffle(cards_list)
        self.cards = cards_list

        # En la fase de memorización, todas comienzan boca arriba
        for card in self.cards:
            card.revealed = True
            card.matched = False

        self.state = STATE_MEMORIZE
        self.memo_start_time = time.time()
        self.timer_running = False
        self.elapsed_time_ms = 0

    def start_gameplay_phase(self):
        """Oculta las cartas tras la memorización e inicia el reloj."""
        for card in self.cards:
            card.revealed = False
        self.state = STATE_WAITING_INPUT
        self.game_start_time = time.time()
        self.timer_running = True

    def get_current_time_ms(self):
        if not self.timer_running:
            return self.elapsed_time_ms
        current_now = time.time()
        return self.elapsed_time_ms + int((current_now - self.game_start_time) * 1000)

    def select_card(self, index):
        """Gestiona el clic en una carta bajo estricto control de estados."""
        if self.state != STATE_WAITING_INPUT:
            return None  # Bloquear spam de clics

        if index < 0 or index >= len(self.cards):
            return None

        card = self.cards[index]
        if card.matched or card.revealed:
            return None

        card.revealed = True

        if self.first_selected is None:
            self.first_selected = index
            return "first_flipped"
        else:
            self.second_selected = index
            self.state = STATE_EVALUATING
            self.eval_start_time = time.time()
            return "evaluating"

    def evaluate_pair(self):
        """Evalúa si el par descubierto coincide o es un error."""
        if self.first_selected is None or self.second_selected is None:
            return None

        c1 = self.cards[self.first_selected]
        c2 = self.cards[self.second_selected]

        if c1.flag["id"] == c2.flag["id"]:
            # Acierto (Match)
            c1.matched = True
            c2.matched = True
            self.matches_count += 1
            self.first_selected = None
            self.second_selected = None

            if self.matches_count >= self.total_pairs:
                self.state = STATE_GAME_OVER
                self.timer_running = False
                self.elapsed_time_ms = self.get_current_time_ms()
                return "win"
            else:
                self.state = STATE_WAITING_INPUT
                return "match"
        else:
            # Error (Mismatch)
            self.errors += 1
            self.elapsed_time_ms += self.time_penalty_ms  # Penalización opcional aplicada
            
            c1.revealed = False
            c2.revealed = False
            first_idx = self.first_selected
            second_idx = self.second_selected
            self.first_selected = None
            self.second_selected = None

            if self.shuffle_on_error:
                # El shuffle y la animación se coordinan en ui_manager
                self.state = STATE_SHUFFLING
                return "mismatch_shuffle"
            else:
                self.state = STATE_WAITING_INPUT
                return "mismatch"

    def do_shuffle_unmatched(self):
        """Ejecuta el barajado de cartas no emparejadas y devuelve mapeo (origen -> destino)."""
        unmatched_indices = [i for i, card in enumerate(self.cards) if not card.matched]
        if len(unmatched_indices) <= 1:
            return {}

        original_cards = [self.cards[i] for i in unmatched_indices]
        shuffled_cards = list(original_cards)
        
        # Asegurar que al menos algunas posiciones cambien si hay suficientes cartas
        for _ in range(5):
            random.shuffle(shuffled_cards)
            if shuffled_cards != original_cards:
                break

        for i, new_card in zip(unmatched_indices, shuffled_cards):
            self.cards[i] = new_card

        return unmatched_indices
