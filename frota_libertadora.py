import pygame
import sys
import random
import pyttsx3
import json
import os
import subprocess
import cv2

pygame.init()

WIDTH, HEIGHT = 1200, 800
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Frota Libertadora!")

engine = pyttsx3.init()
engine.setProperty("rate", 300)
engine.setProperty("volume", 1.0)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 100, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

font = pygame.font.SysFont(None, 24)

ASSETS_DIR = "assets"
IMAGES_DIR = os.path.join(os.getcwd(), "assets", "images")
SOUNDS_DIR = os.path.join(os.getcwd(), "assets", "sounds")

game_instance = None

AMMO_REQUEST_LIMIT = 3
AMMO_DRAW_COUNTS = [3, 2, 1]

# Probabilidades e outras constantes de evento
RAREAMENTO_PROB = 0.10
TEMPESTADE_PROB = 0.10
AURORA_PROB = 0.10

SPECIAL_DRAW_PROB = 0.08

# Marcos de aeronaves
MARCOS_AERONAVES = {
    10: {"aircraft_bonus": 3, "card_bonus": 2},
    15: {"aircraft_bonus": 3, "card_bonus": 2},
    20: {"aircraft_bonus": 3, "card_bonus": 0},
    30: {"aircraft_bonus": 0, "card_bonus": 3},
}
MAX_AERONAVES_TO_WIN = 50

POINTS_EXCHANGE_TABLE = {15: (2, 2), 25: (3, 2), 35: (4, 3), 45: (5, 4), 55: (6, 5)}

missing_images = set()
missing_sounds = set()

###############################################################################
#                                   CARD                                      #
###############################################################################
class Card:
    def __init__(self, name, potencia, carta_bonus, card_type, quantity):
        self.name = name
        self.potencia = potencia
        self.carta_bonus = carta_bonus
        self.type = card_type
        self.quantity = quantity
        self.image = self.load_image()
        self.sound = self.load_sound()

    def load_image(self):
        global missing_images
        sanitized_name = (
            self.name.replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("ú", "u")
            .replace(" ", "_")
        )
        image_filename = f"{sanitized_name}.png"
        image_path = os.path.join(IMAGES_DIR, image_filename)

        if os.path.exists(image_path):
            try:
                return pygame.image.load(image_path).convert_alpha()
            except pygame.error:
                print(f"Erro ao carregar a imagem: {image_filename}")
                return None

    def load_sound(self):
        global missing_sounds
        sanitized_name = (
            self.name.replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("ú", "u")
            .replace(" ", "_")
        )
        sound_filename = f"{sanitized_name}.wav"
        sound_path = os.path.join(SOUNDS_DIR, sound_filename)

        if os.path.exists(sound_path):
            try:
                return pygame.mixer.Sound(sound_path)
            except pygame.error:
                print(f"Erro ao carregar o som: {sound_filename}")
                return None

    def get_info(self):
        return f"{self.name} - Potência: {self.potencia}, Bônus: {self.carta_bonus}, Tipo: {self.type}"

    def to_dict(self):
        return {
            "name": self.name,
            "potencia": self.potencia,
            "carta_bonus": self.carta_bonus,
            "type": self.type,
            "quantity": self.quantity,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            potencia=data["potencia"],
            carta_bonus=data["carta_bonus"],
            card_type=data["type"],
            quantity=data["quantity"],
        )


###############################################################################
#                                   DECK                                      #
###############################################################################
class Deck:
    def __init__(self):
        self.arzenal = []
        self.paiol_attack_deck = []
        self.paiol_counter_deck = []
        self.retreat_cards = []
        self.falouqganhoudragonians = False
        self.falouqganhouratonians = False
        self.cartas_especiais_player = []
        self.cartas_especiais_ai = []

        # 1) Adicionando 12 cartas de recuo
        self.add_cards("Retirada Imediata", 0, 3, "Recuo", 12, self.retreat_cards)

        # 2) Cartas Especiais (24 no total: 12 p/ player, 12 p/ IA)
        self.add_cards_to_split(
            "Ataque Surpresa Total",
            10,
            3,
            "Especial",
            12,
            self.cartas_especiais_player,
            self.cartas_especiais_ai,
            6,
        )
        self.add_cards_to_split(
            "bateria Antiaérea Super Imobilizante",
            8,
            0,
            "Especial",
            12,
            self.cartas_especiais_player,
            self.cartas_especiais_ai,
            6,
        )

        # Conjunto de cartas de ataque e contra-ataque
        ATT_CONTRA_SETS = [
            ("Manobra de ataque pelo flanco-direito", 7, 2, 2),
            ("Manobra de evasão pelo flanco_direito", 7, 2, 2),
            ("Manobra de ataque pelo flanco-esquerdo", 7, 2, 2),
            ("Manobra de evasão pelo flanco-esquerdo", 7, 2, 2),
            ("Canhão double cracker", 5, 2, 2),
            ("Canhão double shield defense", 5, 2, 2),
            ("Canhão de jato de ácido corrosivo", 5, 1, 2),
            ("Canhão de jato antiácido corrosivo", 5, 1, 2),
            ("Canhão de jato de magma meteórico", 5, 1, 2),
            ("Canhão de Jato antimagma meteórico", 5, 1, 2),
            ("Bomba megatômica", 3, 1, 2),
            ("Canhão gigatômico", 5, 1, 2),
            ("Bomba Fotônica", 3, 1, 2),
            ("Canhão antifotônico", 3, 1, 2),
            ("bomba criogênica", 3, 1, 2),
            ("Canhão de hidrogênio super-derretedor", 5, 1, 2),
            ("Torpedo de explosão superatômico", 4, 2, 4),
            ("Torpedo anti-explosão superatômica", 4, 2, 4),
            ("Torpedo de fusão total", 4, 2, 4),
            ("Torpedo antifusão total", 4, 2, 4),
            ("Bomba de impacto titânico", 3, 2, 4),
            ("Raio desintegrador de bomba de titânio", 4, 2, 4),
            ("Raio de destruição supersônica", 2, 1, 3),
            ("Raio antidestruição supersônica", 2, 1, 3),
            ("Raio desmolecularizador", 2, 1, 3),
            ("Raio antidesmolecularizador", 2, 1, 3),
            ("Raio desintegrador", 2,1,3,),
            ("Raio antidesintegração",2,1,3,),
            ("Raio de supervibração fendente", 2, 1, 3),
            ("Raio anti-supervibração fendente", 2, 1, 3),
            ("Metralhadora de alta destruição", 2, 1, 4),
            ("Raio de invisibilidade para metralhadora de alta destruição", 2, 1, 4),
            ("Metralhadora supersônica de longo alcance", 2, 1, 4),
            ("Raio de hiper supressão supersônica", 2, 1, 4),
            ("Metralhadora superatômica de destruição Térmica", 3, 1, 4),
            ("Raio antimetralhadora superatômica", 2, 1, 4),
        ]

        # Loop ajustado para lidar com pares de ataque e contra-ataque
        all_attack_cards = []
        all_contra_cards = []

        # Processa os pares de ataque e contra-ataque
        for i in range(0, len(ATT_CONTRA_SETS), 2):
            # Carta de ataque
            att_name, pot, bonus, att_qty = ATT_CONTRA_SETS[i]
            # Carta de contra-ataque
            contra_name, _, _, contra_qty = ATT_CONTRA_SETS[i + 1]

            # Criar as cartas de ataque
            for _ in range(att_qty):
                all_attack_cards.append(Card(att_name, pot, bonus, "Ataque", att_qty))

            # Criar as cartas de contra-ataque
            for _ in range(contra_qty):
                all_contra_cards.append(
                    Card(contra_name, pot, bonus, "Contra-Ataque", contra_qty)
                )

        random.shuffle(all_attack_cards)
        random.shuffle(all_contra_cards)

        # 12 de ataque => paiol ataque
        paiol_attack_selected = all_attack_cards[:12]
        self.paiol_attack_deck.extend(paiol_attack_selected)

        # 12 de contra => paiol contra-ataque
        paiol_contra_selected = all_contra_cards[:12]
        self.paiol_counter_deck.extend(paiol_contra_selected)

        # Resto => arzenal
        remaining_attack_cards = all_attack_cards[12:]
        remaining_contra_cards = all_contra_cards[12:]
        self.arzenal.extend(remaining_attack_cards)
        self.arzenal.extend(remaining_contra_cards)

        self.shuffle_decks()

    def add_cards(self, name, potencia, carta_bonus, card_type, quantity, deck):
        for _ in range(quantity):
            deck.append(Card(name, potencia, carta_bonus, card_type, quantity))

    def add_cards_to_split(
        self,
        name,
        potencia,
        carta_bonus,
        card_type,
        quantity,
        deck_p,
        deck_ai,
        split_count,
    ):
        for i in range(quantity):
            card = Card(name, potencia, carta_bonus, card_type, quantity)
            if i < split_count:
                deck_p.append(card)
            else:
                deck_ai.append(card)

    def shuffle_decks(self):
        random.shuffle(self.arzenal)
        random.shuffle(self.paiol_attack_deck)
        random.shuffle(self.paiol_counter_deck)
        random.shuffle(self.retreat_cards)
        random.shuffle(self.cartas_especiais_player)
        random.shuffle(self.cartas_especiais_ai)

    def draw_arzenal_card(self, player=None):
        if not self.arzenal:
            return None
        return self.arzenal.pop()

    def draw_paiol_attack_card(self):
        if self.paiol_attack_deck:
            return self.paiol_attack_deck.pop()
        return None

    def draw_paiol_counter_card(self):
        if self.paiol_counter_deck:
            return self.paiol_counter_deck.pop()
        return None

    def draw_retreat_card(self):
        if self.retreat_cards:
            return self.retreat_cards.pop()
        return None

    def draw_player_special_card(self):
        if self.cartas_especiais_player:
            return self.cartas_especiais_player.pop()
        return None

    def draw_ai_special_card(self):
        if self.cartas_especiais_ai:
            return self.cartas_especiais_ai.pop()
        return None

    # [AJUSTE 1] Melhoria do try_distribute_cards para 3-3, 2-2, 1-1, senão fim de jogo
    def try_distribute_cards(self, player, ai, already_announced=False):
        """
        Tenta distribuir cartas do arsenal para os jogadores.
        Se o arsenal não tiver cartas suficientes para a distribuição esperada, o jogo termina.
        """
        p_no_cards = len(player.hand) == 0
        ai_no_cards = len(ai.hand) == 0
        if not (p_no_cards or ai_no_cards):
            return already_announced

        total = len(self.arzenal)

        # Verifica se há cartas suficientes no arsenal para continuar
        if total < 2:
            if already_announced:
                return True  # Já foi anunciado, não faz nada

            if player.aircrafts > ai.aircrafts:
                game_instance.announce("Dragonians têm mais aeronaves e vencem!")
            elif ai.aircrafts > player.aircrafts:
                game_instance.announce("Ratonians têm mais aeronaves e vencem!")
            else:
                game_instance.announce("Empate total em aeronaves!")

            # Marca o fim do jogo
            player.lost = True
            ai.lost = True
            game_instance.end_game()
            return True  # Sinaliza que já foi anunciado

        # Distribuição de cartas se houver cartas suficientes
        if total >= 6:
            self._draw_n_from_arzenal(3, player)
            self._draw_n_from_arzenal(3, ai)
        elif total >= 4:
            self._draw_n_from_arzenal(2, player)
            self._draw_n_from_arzenal(2, ai)
        elif total >= 2:
            self._draw_n_from_arzenal(1, player)
            self._draw_n_from_arzenal(1, ai)

        return already_announced

    def _draw_n_from_arzenal(self, n, who):
        cards_drawn = 0
        for _ in range(n):
            if self.arzenal:
                c = self.arzenal.pop()
                if c:
                    who.hand.append(c)
                    cards_drawn += 1
        if cards_drawn > 0:
            if who.is_human:
                game_instance.announce(
                    f"Dragonians recebem {cards_drawn} cartas do arsenal."
                )
            else:
                game_instance.announce(
                    f"Ratonians recebem {cards_drawn} cartas do arsenal."
                )

    def to_dict(self):
        return {
            "arzenal": [c.to_dict() for c in self.arzenal],
            "paiol_attack_deck": [c.to_dict() for c in self.paiol_attack_deck],
            "paiol_counter_deck": [c.to_dict() for c in self.paiol_counter_deck],
            "retreat_cards": [c.to_dict() for c in self.retreat_cards],
            "cartas_especiais_player": [
                c.to_dict() for c in self.cartas_especiais_player
            ],
            "cartas_especiais_ai": [c.to_dict() for c in self.cartas_especiais_ai],
        }

    def to_dict(self):
        return {
            "arzenal": [c.to_dict() for c in self.arzenal],
            "paiol_attack_deck": [c.to_dict() for c in self.paiol_attack_deck],
            "paiol_counter_deck": [c.to_dict() for c in self.paiol_counter_deck],
            "retreat_cards": [c.to_dict() for c in self.retreat_cards],
            "cartas_especiais_player": [
                c.to_dict() for c in self.cartas_especiais_player
            ],
            "cartas_especiais_ai": [c.to_dict() for c in self.cartas_especiais_ai],
        }

    @classmethod
    def from_dict(cls, data):
        deck = cls()
        deck.arzenal = [Card.from_dict(c) for c in data["arzenal"]]
        deck.paiol_attack_deck = [Card.from_dict(c) for c in data["paiol_attack_deck"]]
        deck.paiol_counter_deck = [
            Card.from_dict(c) for c in data["paiol_counter_deck"]
        ]
        deck.retreat_cards = [Card.from_dict(c) for c in data["retreat_cards"]]
        deck.cartas_especiais_player = [
            Card.from_dict(c) for c in data.get("cartas_especiais_player", [])
        ]
        deck.cartas_especiais_ai = [
            Card.from_dict(c) for c in data.get("cartas_especiais_ai", [])
        ]
        return deck


###############################################################################
#                                  PLAYER                                     #
###############################################################################
class Player:
    def __init__(self, name, is_human=True):
        self.name = name
        self.hand = []
        self.bank = []
        self.score = 0
        self.is_human = is_human
        self.requested_ammo = 0
        self.retreat_cards_used = 0
        self.retreat_cards_total = 6
        self.ai_memory = {}
        self.aircrafts = 4
        self.hands_won = 0  # Análogo a "j"
        self.total_hands_played = 0  # Análogo a "i"
        self.cards_played = 0
        self.special_cards_used = 0
        self.double_awarded = False
        self.triple_awarded = False
        self.quad_awarded = False
        self.lost = False
        self.special_requests_made = 0
        self.special_cards_details = {}

        # Contador de kamikazes realizados ao longo do jogo
        self.kamikaze_count = 0

    def draw_cards(self, deck, num=1, card_type=None):
        for _ in range(num):
            if card_type == "Ataque":
                c = deck.draw_paiol_attack_card()
            elif card_type == "Contra-Ataque":
                c = deck.draw_paiol_counter_card()
            else:
                c = deck.draw_arzenal_card(self)
            if c:
                self.hand.append(c)
                if game_instance:
                    game_instance.enable_shortcut(len(self.hand) - 1)

    def play_card(self, card_index):
        if 0 <= card_index < len(self.hand):
            self.cards_played += 1
            card = self.hand.pop(card_index)
            if card.type == "Especial":
                self.special_cards_used += 1
                self.special_cards_details[card.name] = (
                    self.special_cards_details.get(card.name, 0) + 1
                )
            if self.is_human and game_instance:
                game_instance.remember_player_card(card.name)
            return card
        return None

    def request_ammo(self, deck):
        if self.requested_ammo >= AMMO_REQUEST_LIMIT:
            return 0
        index = min(self.requested_ammo, len(AMMO_DRAW_COUNTS) - 1)
        num_to_draw = AMMO_DRAW_COUNTS[index]
        self.requested_ammo += 1
        for _ in range(num_to_draw):
            a_card = deck.draw_paiol_attack_card()
            if a_card:
                self.hand.append(a_card)
                if game_instance:
                    game_instance.enable_shortcut(len(self.hand) - 1)
            d_card = deck.draw_paiol_counter_card()
            if d_card:
                self.hand.append(d_card)
                if game_instance:
                    game_instance.enable_shortcut(len(self.hand) - 1)

        if self.is_human:
            msg = f"Os Dragonians receberam {num_to_draw * 2} cartas do paiol."
        else:
            msg = f"Ratonians receberam munição do paiol."
        if game_instance:
            game_instance.announce(msg)

        return self.get_ammo_points_awarded()

    def get_ammo_points_awarded(self):
        if self.requested_ammo == 1:
            return 1
        elif self.requested_ammo == 2:
            return 2
        elif self.requested_ammo == 3:
            return 3
        return 0

    def to_dict(self):
        return {
            "name": self.name,
            "hand": [c.to_dict() for c in self.hand],
            "bank": [c.to_dict() for c in self.bank],
            "score": self.score,
            "is_human": self.is_human,
            "requested_ammo": self.requested_ammo,
            "retreat_cards_used": self.retreat_cards_used,
            "retreat_cards_total": self.retreat_cards_total,
            "ai_memory": self.ai_memory,
            "aircrafts": self.aircrafts,
            "hands_won": self.hands_won,
            "total_hands_played": self.total_hands_played,
            "cards_played": self.cards_played,
            "special_cards_used": self.special_cards_used,
            "double_awarded": self.double_awarded,
            "triple_awarded": self.triple_awarded,
            "quad_awarded": self.quad_awarded,
            "lost": self.lost,
            "special_requests_made": self.special_requests_made,
            "special_cards_details": self.special_cards_details,
            "kamikaze_count": self.kamikaze_count,
        }

    @classmethod
    def from_dict(cls, data):
        p = cls(name=data["name"], is_human=data["is_human"])
        p.hand = [Card.from_dict(c) for c in data["hand"]]
        p.bank = [Card.from_dict(c) for c in data.get("bank", [])]
        p.score = data["score"]
        p.requested_ammo = data["requested_ammo"]
        p.retreat_cards_used = data["retreat_cards_used"]
        p.retreat_cards_total = data["retreat_cards_total"]
        p.ai_memory = data.get("ai_memory", {})
        p.aircrafts = data.get("aircrafts", 4)
        p.hands_won = data.get("hands_won", 0)
        p.total_hands_played = data.get("total_hands_played", 0)
        p.cards_played = data.get("cards_played", 0)
        p.special_cards_used = data.get("special_cards_used", 0)
        p.double_awarded = data.get("double_awarded", False)
        p.triple_awarded = data.get("triple_awarded", False)
        p.quad_awarded = data.get("quad_awarded", False)
        p.lost = data.get("lost", False)
        p.special_requests_made = data.get("special_requests_made", 0)
        p.special_cards_details = data.get("special_cards_details", {})
        p.kamikaze_count = data.get("kamikaze_count", 0)
        return p


###############################################################################
#                                   GAME                                      #
###############################################################################
class Game:

    def __init__(self, player_name):
        self.carregar_video_em_loop()
        # Inicialização dos jogadores e contadores de trocas
        self.player_name = player_name
        self.players = []
        self.human_trade_count = 0
        self.ai_trade_count = 0
        self.max_trades = 3  # Máximo de 3 trocas permitidas para a IA
        self.humano_fez_troca = {}
        self.ia_fez_troca = {}  # Inicializa o rastreador de trocas da IA

        # Instância global do jogo
        global game_instance
        game_instance = self

        # Configurações de fala
        self.speech_on = True
        self.player_name = ""

        # Estado do jogo
        self.current_attacker_index = 0
        self.running = True
        self.selected_card_index = 0
        self.current_phase = "Ataque"
        self.battle_cards = []
        self.turn_counter = 0
        self.in_main_menu = False
        self.save_file = ""
        self.disabled_shortcuts = set()
        self.last_ai_card = None
        self.plays_this_hand = 0

        # Histórico do jogo
        self.player_card_history = []
        self.hands_history = []
        self.game_ended = False
        # Inicialização do baralho
        self.deck = Deck()

        # Opções do menu principal

        self.zero_pressed = False

        # Botões da interface
        self.retreat_button_rect = pygame.Rect(10, 10, 200, 30)
        self.ammo_button_rect = pygame.Rect(220, 10, 200, 30)
        self.info_button_rect = pygame.Rect(430, 10, 200, 30)
        self.hand_button_rect = pygame.Rect(640, 10, 200, 30)
        self.save_button_rect = pygame.Rect(850, 10, 200, 30)

        # Imagem de fundo das cartas
        self.card_back_image = None
        back_image_path = os.path.join(IMAGES_DIR, "card_back.png")
        if os.path.exists(back_image_path):
            try:
                self.card_back_image = pygame.image.load(
                    back_image_path
                ).convert_alpha()
            except pygame.error:
                self.card_back_image = None

        self.get_player_name()

        # Monitoramento de trocas da IA na mão atual
        self.ai_traded_this_hand = False  # Flag para troca na mão atual

        # Variáveis adicionais para a função ai_should_trade_cards
        self.ai_obtained_cards = []  # Cartas obtidas pela IA
        self.player_obtained_cards = []  # Cartas obtidas pelo jogador
        self.player_draws_from_defense = (
            []
        )  # Cartas retiradas pelo jogador do banco de defesa
        self.player_draws_from_counter_attack = (
            []
        )  # Cartas retiradas pelo jogador do banco de contra-ataque
        self.player_attack_cards = []  # Cartas de ataque do jogador
        self.player_counter_attack_cards = []  # Cartas de contra-ataque do jogador
        self.player_special_cards = []  # Cartas especiais do jogador
        self.total_possible_cards = 140  # Total de cartas possíveis no jogo
        self.remaining_arsenal_cards = 1  # Cartas restantes no arsenal
        self.remaining_attack_deck_cards = 0  # Cartas restantes no paiol de ataque
        self.remaining_defense_deck_cards = 0  # Cartas restantes no paiol de defesa
        self.handle_menu_selection()


    def carregar_video_em_loop(self):
        """
        Exibe um vídeo em loop enquanto uma barra de progresso avança, com som.
        """
        # Configurações de tela
        WIDTH, HEIGHT = 1200, 800
        window = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Carregamento com Vídeo e Som")

        # Cores
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        progress_color = (255, 0, 0)  # Cor da barra de progresso

        # Caminho do vídeo e som
        video_path = "assets/images/video.mp4"
        sound_path = "assets/sounds/Raio_antimetralhadora_superatomica.wav"  # Arquivo de som (MP3 ou OGG)

        # Inicia pygame
        pygame.font.init()
        pygame.mixer.init()  # Inicializa o mixer de áudio
        font = pygame.font.Font(None, 36)

        # Carregar e tocar o som
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.set_volume(0.5)  # Define o volume (0.0 a 1.0)
        pygame.mixer.music.play(-1)  # -1 significa "em loop"

        # Abre o vídeo
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Não foi possível abrir o vídeo: {video_path}")

        

        # Loop principal do carregamento
        for i in range(1, 101):
            # Ler um frame do vídeo
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reinicia o vídeo se terminar
                continue

            # Converte o frame do OpenCV para o formato do pygame
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

            # Desenha o vídeo como plano de fundo
            window.blit(frame_surface, (0, 0))

            
            

            # Mensagem de carregamento
            loading_message = font.render("Transportando para zona de guerra", True, WHITE)
            loading_rect = loading_message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            window.blit(loading_message, loading_rect)

            # Atualiza a tela
            pygame.display.flip()
            pygame.time.wait(30)  # Pausa para simular carregamento

        # Finaliza o som quando o carregamento terminar

        cap.release()

    def toggle_speech(self):
        """Alterna a fala do jogo entre ativada e silenciada."""
        self.speech_on = not self.speech_on
        if self.speech_on:
            print("Fala ativada.")
            self.announce("Fala ativada. Pressione F para silenciar.")
        else:
            print("Fala silenciada.")
            self.announce("Fala silenciada. Pressione F novamente para falar.")

    def enable_shortcut(self, index):
        """Habilita um atalho específico removendo-o do conjunto de atalhos desabilitados."""
        if index in self.disabled_shortcuts:
            self.disabled_shortcuts.remove(index)

    def reset_shortcuts(self):
        """Reinicia todos os atalhos, limpando o conjunto de atalhos desabilitados."""
        self.disabled_shortcuts.clear()

    def remember_player_card(self, card_name):
        self.player_card_history.append(card_name)

    def get_player_name(self):
        pygame.mixer.music.stop()
        self.announce("Acessando sua aeronave")
        self.announce("Digite seu nome ou pressione Enter para pilotá-la como comandante Anônimo.")
        name_input = ""
        input_active = True
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.player_name = (
                            name_input.strip() if name_input.strip() else "Dragonians"
                        )
                        greeting = (
                            f"Olá, Comandante {self.player_name}."
                            if self.player_name != "Dragonians"
                            else "Olá, Comandante Dragonian,"
                        )
                        self.announce(greeting)
                        self.check_saved_games()
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        name_input = name_input[:-1]
                    else:
                        if event.unicode.isalnum() or event.unicode.isspace():
                            name_input += event.unicode
            window.fill(BLACK)
            prompt_surface = font.render("Digite seu nome: " + name_input, True, WHITE)
            window.blit(prompt_surface, (50, HEIGHT // 2))
            pygame.display.flip()

    def check_saved_games(self):
        sanitized_player_name = (
            self.player_name.lower()
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("ú", "u")
            .replace(" ", "_")
        )
        self.save_file = (
            f"{sanitized_player_name}.json" if self.player_name != "Dragonians" else ""
        )
        if (
            self.player_name != "Dragonians"
            and self.save_file
            and os.path.exists(self.save_file)
        ):
            self.announce(
                "Jogo salvo encontrado. Pressione S para continuar ou N para iniciar um novo jogo."
            )
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            self.load_game()
                            self.in_main_menu = False
                            waiting = False
                            self.handle_menu_selection()
                        elif event.key == pygame.K_n:
                            try:
                                os.remove(self.save_file)
                                self.announce(
                                    "Partida anterior apagada. Iniciando nova partida."
                                )
                            except OSError:
                                self.announce("Erro ao apagar a partida anterior.")
                            self.in_main_menu = True
                            waiting = False
                            self.handle_menu_selection()
                    elif event.type == pygame.QUIT:
                        self.exit_game()
        else:
            self.handle_menu_selection()

    def handle_menu_selection(self):
        """Inicia o jogo sem passar por um menu de opções."""
        self.announce("Você está na cabine de sua poderosa aeronave Destroyer D34 Dragonian.")

        self.announce(
            "Quando estiver pronto, pressione T, para as Ratonians iniciarem a guerra, ou qualquer outra tecla, para os Dragonians a iniciarem."
        )

        waiting_for_t = True
        user_pressed_t = False

        while waiting_for_t:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        user_pressed_t = True
                    else:
                        self.announce(f"Agora, comandante!")
                        
                    waiting_for_t = False
                elif event.type == pygame.QUIT:
                    self.exit_game()

        self.in_main_menu = False  # Garante que o menu seja ignorado
        self.current_attacker_index = (
            1 if user_pressed_t else 0
        )  # Define quem começa atacando
        self.start_new_game(from_save=False)

    def draw_main_menu(self):
        window.fill(BLACK)
        for idx, option in enumerate(self.menu_options):
            color = WHITE if idx == self.menu_selected else GRAY
            text_surface = font.render(option, True, color)
            option_rect = text_surface.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 120 + idx * 40)
            )
            window.blit(text_surface, option_rect)
        pygame.display.flip()

    def show_controls_info(self):
        self.announce("Teclas do Jogo:")
        controls_info = [
            "Setas Esquerda/Direita: navegar pelas armas na mão",
            "Seta Cima: disparar arma selecionada",
            "Seta Baixo: lançar Recuo Estratégico",
            "E: status de Recuo",
            "M: comprar cartas de Ataque do paiol",
            "N: comprar cartas de Defesa do paiol",
            "I: informações dos baralhos",
            "H: informações das suas armas",
            "J: informações detalhadas do jogador (Dragonians)",
            "R: informações detalhadas das Ratonians ou Replay no final",
            "A: aumentar velocidade da voz",
            "D: diminuir velocidade da voz",
            "U: aumentar volume da voz",
            "V: diminuir volume da voz",
            "C: trocar grupos de 5 cartas por 3 pontos",
            "O: trocar pontos por aeronaves ou destruir aeronaves",
            "S: anunciar última carta das Ratonians (ou Ctrl+S para salvar)",
            "Alt+K: ouvir teclas do jogo",
            "Espaço: anunciar arma selecionada",
            "X: fazer troca de cartas entre jogadores",
            "B: solicitar carta especial (oponente ganha +3 pontos)",
            "P: comprar carta especial do banco (oponente ganha +3 pontos)",
            "F: ativar/desativar fala",
            "k: realizar Ataque Kamikaze",
        ]
        for info in controls_info:
            self.announce(info)
        self.announce("Pressione qualquer tecla para voltar.")
        self.wait_key()

    def show_terms_info(self):
        self.announce("Termos e Conceitos:")
        terms_info = [
            "Objetivo: chegar a 50 aeronaves antes do oponente.",
            "Banco do jogador: Banco Dragonians, Banco da IA: Banco Ratonians.",
            "Baralhos Especiais: Esp Dragonians e Esp Ratonians.",
            "Quando alguém fica sem cartas, o jogo distribui 3 (ou 2, ou 1) pra cada se possível.",
            "Se não conseguir distribuir, ganha quem tiver mais aeronaves.",
        ]
        for info in terms_info:
            self.announce(info)
        self.announce("Pressione qualquer tecla para voltar.")
        self.wait_key()

    def show_detailed_rules(self):
        self.announce("Regras Detalhadas (Frota Libertadora):")
        detailed_rules = [
            "Trocar 5 cartas do banco => +3 pontos (tecla C).",
            "Trocar pontos por aeronaves ou destruir aeronaves (tecla O).",
            "Pressione F para ativar/desativar fala a qualquer momento.",
        ]
        for rule in detailed_rules:
            self.announce(rule)
        self.announce("Pressione qualquer tecla para voltar.")
        self.wait_key()

    def adjust_volume_menu(self):
        self.announce("Ajustar Volume (U para aumentar, V para diminuir)")
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u:
                        self.adjust_voice_volume(increase=True)
                        waiting = False
                    elif event.key == pygame.K_v:
                        self.adjust_voice_volume(increase=False)
                        waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.QUIT:
                    waiting = False

    def adjust_voice_volume(self, increase: bool):
        """
        Ajusta o volume da voz ou narração no jogo.
        :param increase: True para aumentar o volume, False para diminuir.
        """
        if not hasattr(self, "voice_volume"):
            self.voice_volume = 1.0  # Volume padrão (de 0.0 a 1.0)

        if increase:
            self.voice_volume = min(
                1.0, self.voice_volume + 0.1
            )  # Aumenta o volume, mas não ultrapassa 1.0
            self.announce(f"Volume aumentado para {self.voice_volume:.1f}")
        else:
            self.voice_volume = max(
                0.0, self.voice_volume - 0.1
            )  # Diminui o volume, mas não fica abaixo de 0.0
            self.announce(f"Volume reduzido para {self.voice_volume:.1f}")

    def adjust_speed_menu(self):
        self.announce("Ajustar Velocidade (A para aumentar, D para diminuir)")
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.adjust_voice_speed(increase=True)
                        waiting = False
                    elif event.key == pygame.K_d:
                        self.adjust_voice_speed(increase=False)
                        waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.QUIT:
                    waiting = False

    def adjust_voice_speed(self, increase: bool):
        """
        Ajusta a velocidade da voz ou narração no jogo.
        :param increase: True para aumentar a velocidade, False para diminuir.
        """
        if not hasattr(self, "voice_speed"):
            self.voice_speed = 1.0  # Velocidade padrão

        if increase:
            self.voice_speed += 0.1  # Aumenta a velocidade
            self.announce(f"Velocidade aumentada para {self.voice_speed:.1f}")
        else:
            self.voice_speed = max(
                0.5, self.voice_speed - 0.1
            )  # Diminui, mas não vai abaixo de 0.5
            self.announce(f"Velocidade reduzida para {self.voice_speed:.1f}")

    def trade_cards_for_points_menu(self):
        player = self.players[0]
        if len(player.bank) < 5:
            self.announce(
                "São necessárias ao menos 5 cartas no banco para trocar por pontos."
            )
            self.announce("Pressione qualquer tecla para retornar.")
            self.wait_key()
            return

        self.announce(
            "Trocar  cada 5 cartas do Banco Dragonians por 3 pontos? Pressione C para confirmar."
        )
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        self.trade_cards_for_points()
                    waiting = False
                elif event.type == pygame.QUIT:
                    self.exit_game()

    def end_game(self):
        """
        Encerra o jogo e redireciona para o menu principal, fechando a janela atual.
        """
        self.game_ended = True
        self.running = False  # Para interromper o loop principal

        self.announce("Voltando ao menu principal...")

        # Fecha o pygame para liberar os recursos antes de redirecionar
        pygame.quit()

        # Executa o menu novamente e encerra o processo atual
        menu_file = "menu.py"  # Substitua pelo nome correto do arquivo de menu
        if os.path.exists(menu_file):
            try:
                subprocess.run(["python", menu_file])
            except Exception as e:
                print(f"Erro ao reexecutar {menu_file}: {e}")
                self.announce("Erro ao voltar para o menu principal.")
                sys.exit()  # Encerra completamente se falhar
        else:
            print(f"Arquivo {menu_file} não encontrado.")
            self.announce(f"Arquivo {menu_file} não encontrado. Encerrando o programa.")
            sys.exit()  # Encerra completamente se o menu não for encontrado

    def trade_cards_for_points(self):
        count_exchanged = 0
        player = self.players[0]
        while len(player.bank) >= 5:
            for _ in range(5):
                player.bank.pop(0)
            player.score += 3
            count_exchanged += 1

        if count_exchanged > 0:
            self.announce(
                f"Os Dragonians trocaram {count_exchanged*5} cartas do banco por {count_exchanged*3} pontos."
            )
            player.total_hands_played += 1
        else:
            self.announce(
                "Não há cartas suficientes no banco para trocar 5 cartas por pontos."
            )

    def trade_points_menu_dropdown(self):
        player = self.players[0]
        costs_list = [15, 25, 35, 45, 55]
        current_idx = 0

        if player.score < 15:
            self.announce("São necessários pelo menos 15 pontos para começar a trocar.")
            self.announce("Pressione qualquer tecla para retornar.")
            self.wait_key()
            return

        def describe_option(cost):
            (a_gain, s_gain) = POINTS_EXCHANGE_TABLE[cost]
            return f"Custo {cost} pontos => +{a_gain} aeronaves OU destruir {s_gain} aeronaves."

        self.announce(
            "Use setas para navegar nas opções e ENTER para confirmar. Precione ESC para cancelar."
        )

        in_dropdown = True
        while in_dropdown:
            self.announce(describe_option(costs_list[current_idx]))
            dropdown_wait = True
            while dropdown_wait:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.exit_game()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.announce("Troca cancelada.")
                            in_dropdown = False
                            dropdown_wait = False
                        elif event.key == pygame.K_UP:
                            current_idx = (current_idx - 1) % len(costs_list)
                            dropdown_wait = False
                        elif event.key == pygame.K_DOWN:
                            current_idx = (current_idx + 1) % len(costs_list)
                            dropdown_wait = False
                        elif event.key == pygame.K_RETURN:
                            cost = costs_list[current_idx]
                            if player.score < cost:
                                self.announce("Pontos insuficientes para essa opção.")
                                in_dropdown = False
                                dropdown_wait = False
                            else:
                                self.announce(
                                    "Pressione A para +aeronaves ou S para destruir aeronaves do o inimigo."
                                )
                                sub_wait = True
                                while sub_wait:
                                    for e2 in pygame.event.get():
                                        if e2.type == pygame.QUIT:
                                            self.exit_game()
                                        elif e2.type == pygame.KEYDOWN:
                                            if e2.key == pygame.K_a:
                                                a_gain, _ = POINTS_EXCHANGE_TABLE[cost]
                                                player.score -= cost
                                                player.aircrafts += a_gain
                                                self.announce(
                                                    f"Os Dragonians trocaram {cost} pontos por +{a_gain} aeronaves."
                                                )
                                                self.check_marcos_aeronaves(player)
                                                sub_wait = False
                                                in_dropdown = False
                                                dropdown_wait = False
                                            elif e2.key == pygame.K_s:
                                                _, s_gain = POINTS_EXCHANGE_TABLE[cost]
                                                opponent = self.players[1]
                                                sabotage = min(
                                                    s_gain, opponent.aircrafts
                                                )
                                                player.score -= cost
                                                opponent.aircrafts -= sabotage
                                                self.announce(
                                                    f"O Dragonians destruíram {sabotage} aeronaves das Ratonians."
                                                )
                                                sub_wait = False
                                                in_dropdown = False
                                                dropdown_wait = False
                                            else:
                                                self.announce("Escolha cancelada.")
                                                sub_wait = False
                                                in_dropdown = False
                                                dropdown_wait = False

    def check_marcos_aeronaves(self, player):
        if player.aircrafts >= MAX_AERONAVES_TO_WIN:
            self.end_game()
            return

        if player.aircrafts in MARCOS_AERONAVES:
            bonus_info = MARCOS_AERONAVES[player.aircrafts]
            a_bonus = bonus_info.get("aircraft_bonus", 0)
            c_bonus = bonus_info.get("card_bonus", 0)

            old_value = player.aircrafts - a_bonus

            if a_bonus > 0:
                player.aircrafts += a_bonus
                self.announce(
                    f"{player.name} chegaram à {old_value} aeronaves e receberam +{a_bonus} aeronaves! Agora tem {player.aircrafts}."
                )

            if c_bonus > 0:
                received = 0
                for _ in range(c_bonus):
                    if not self.deck.arzenal:  # Verifica se o arsenal acabou
                        self.announce(
                            "O arsenal acabou antes que as cartas de bônus pudessem ser distribuídas."
                        )
                        self.handle_end_due_to_empty_arsenal(player)
                        return

                    c = self.deck.draw_arzenal_card(player)
                    if c:
                        player.hand.append(c)
                        self.enable_shortcut(len(player.hand) - 1)
                        received += 1

                if received > 0:
                    self.announce(
                        f"{player.name} receberam {received} cartas do Arsenal como bônus!"
                    )

            if player.aircrafts >= MAX_AERONAVES_TO_WIN:
                self.end_game()

    def handle_end_due_to_empty_arsenal(self, player):
        """
        Finaliza o jogo quando o arsenal acaba durante a distribuição de bônus.
        """
        opponent = self.players[1 - self.players.index(player)]
        self.announce("O arsenal acabou! Fim do jogo.")

        if player.aircrafts > opponent.aircrafts:
            self.announce(f"{player.name} têm mais aeronaves e venceram!")
        elif opponent.aircrafts > player.aircrafts:
            self.announce(f"{opponent.name} têm mais aeronaves e venceram!")
        else:
            self.announce("Empate total em aeronaves!")

        # Marca o fim do jogo
        player.lost = True
        opponent.lost = True
        self.end_game()

    def start_new_game(self, from_save=True):
        dragonians = Player(name=self.player_name, is_human=True)
        ratonias = Player(name="Ratonians", is_human=False)
        self.players = [dragonians, ratonias]
        dragonians.draw_cards(self.deck, num=5)
        ratonias.draw_cards(self.deck, num=5)
        self.plays_this_hand = 0
        self.announce_turn_player()
        if self.current_attacker_index == 1:
            self.handle_ai_action()
        self.main()

    def wait_key(self):
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
                elif event.type == pygame.QUIT:
                    self.exit_game()

    def announce(self, message):
        print(message)
        if self.speech_on:
            try:
                engine.say(message)
                engine.runAndWait()
            except Exception as e:
                print(f"Erro no motor de fala: {e}")

    humano_fez_troca = False
    ia_fez_troca = False

    def ensure_index_initialized(self, index):
        """Garante que o índice atual tenha estado inicializado."""
        if index not in self.humano_fez_troca:
            self.humano_fez_troca[index] = False  # Inicializa como False
        if index not in self.ia_fez_troca:
            self.ia_fez_troca[index] = False  # Inicializa como False

    def handle_events(self):
        if not hasattr(self, "previous_attacker_index"):
            self.previous_attacker_index = self.current_attacker_index

        # Verifica se o índice do atacante mudou
        if self.previous_attacker_index != self.current_attacker_index:
            # Reseta o estado do atacante anterior para o humano
            self.ensure_index_initialized(self.previous_attacker_index)
            self.humano_fez_troca[self.previous_attacker_index] = False

            # Reseta o estado do atacante anterior para a IA
            self.ensure_index_initialized(self.previous_attacker_index)
            self.ia_fez_troca[self.previous_attacker_index] = False

            # Atualiza o índice anterior para o atual
            self.previous_attacker_index = self.current_attacker_index

        # Garante que o índice atual tenha estado inicializado
        self.ensure_index_initialized(self.current_attacker_index)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit_game()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    self.toggle_speech()
                elif (event.mod & pygame.KMOD_ALT) and event.key == pygame.K_k:
                    self.show_controls_info()
                elif event.key == pygame.K_k:
                    dragonians = self.players[0]
                    if self.can_current_entity_play(dragonians):
                        self.perform_kamikaze_attack(0)
                    else:
                        self.announce("Não é a sua vez de realizar kamikaze.")
                elif event.key == pygame.K_c:
                    self.trade_cards_for_points_menu()
                elif event.key == pygame.K_o:
                    self.trade_points_menu_dropdown()
                elif event.key == pygame.K_e:
                    self.announce_retreat_status()
                elif event.key == pygame.K_r:
                    self.announce_ai_info()
                elif event.key == pygame.K_m:
                    self.buy_attack_cards()
                elif event.key == pygame.K_n:
                    self.buy_defense_cards()
                elif event.key == pygame.K_i:
                    self.announce_deck_info()
                elif event.key == pygame.K_h:
                    self.announce_hand()
                elif event.key == pygame.K_j:
                    self.announce_player_info()
                elif event.key == pygame.K_a:
                    self.adjust_voice_speed(increase=True)
                elif event.key == pygame.K_d:
                    self.adjust_voice_speed(increase=False)
                elif event.key == pygame.K_u:
                    self.adjust_voice_volume(increase=True)
                elif event.key == pygame.K_v:
                    self.adjust_voice_volume(increase=False)
                elif event.key == pygame.K_s:
                    if event.mod & pygame.KMOD_CTRL:
                        self.save_game()
                    else:
                        if self.last_ai_card:
                            info = self.last_ai_card.get_info()
                            self.announce(
                                f"Última carta lançada pelas Ratonians: {info}"
                            )
                        else:
                            self.announce("As Ratonians ainda não jogaram uma carta.")
                elif event.key == pygame.K_b:
                    dragonians = self.players[0]
                    self.request_special_card(dragonians)
                elif event.key == pygame.K_p:
                    dragonians = self.players[0]
                    self.buy_special_card(dragonians)
                elif event.key in [
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                    pygame.K_4,
                    pygame.K_5,
                    pygame.K_6,
                    pygame.K_7,
                    pygame.K_8,
                    pygame.K_9,
                ]:
                    dragonians = self.players[0]
                    key_number = event.key - pygame.K_1
                    if key_number in self.disabled_shortcuts:
                        self.announce(f"Atalho {key_number + 1} desabilitado.")
                    elif 0 <= key_number < len(dragonians.hand):
                        self.player_play_card(key_number)
                    else:
                        self.announce("Nenhuma arma para este atalho.")
                elif event.key == pygame.K_q:
                    self.exit_game()
                elif event.key == pygame.K_SPACE:
                    dragonians = self.players[0]
                    if dragonians.hand and self.selected_card_index < len(
                        dragonians.hand
                    ):
                        card = dragonians.hand[self.selected_card_index]
                        info = card.get_info()
                        self.announce(info)
                    else:
                        self.announce("Nenhuma arma selecionada.")
                elif event.key == pygame.K_LEFT:
                    self.select_previous_card()
                elif event.key == pygame.K_RIGHT:
                    self.select_next_card()
                elif event.key == pygame.K_UP:
                    dragonians = self.players[0]
                    if dragonians.hand:
                        self.player_play_card(self.selected_card_index)
                elif event.key == pygame.K_DOWN:
                    dragonians = self.players[0]
                    self.use_retreat_card(dragonians)
                elif event.key == pygame.K_x:
                    # Jogada do jogador humano para trocar cartas com a IA
                    print(f"Start atual: {self.current_attacker_index}")
                    mao_jogada = self.current_attacker_index

                    self.ensure_index_initialized(mao_jogada)

                    if not self.humano_fez_troca[mao_jogada]:
                        dragonians = self.players[0]
                        ratonias = self.players[1]
                        if self.human_trade_count < self.max_trades:
                            self.trade_cards(dragonians, ratonias)
                            self.human_trade_count += 1
                            self.announce("Tomada de armas bem-sucedida.")
                            self.humano_fez_troca[mao_jogada] = True
                        else:
                            self.announce(
                                "Tomada de armas mal-sucedida. Os Dragonians já fizeram 5 trocas"
                            )
                    else:
                        self.announce("Só é possível uma troca de armas por mão")

    # -------------------------------------------------------------------------
    # IA decide trocar cartas
    # -------------------------------------------------------------------------
    def ai_should_trade_cards(self, ai_player, player):
        print(f" 2 ---- Start atual: {self.current_attacker_index}")
        """
        Decide se a IA deve trocar cartas com base em suas cartas
        e informações públicas (nº de cartas do jogador, bancos, mesa).
        """

        mao_jogada = self.current_attacker_index
        self.ensure_index_initialized(mao_jogada)

        # Verifica se a IA já fez uma troca nesta rodada
        if self.ia_fez_troca[mao_jogada]:
            print("IA já realizou uma troca nesta rodada.")
            return False

        # IA só troca cartas se ela tiver pelo menos 3 cartas na mão
        # e ainda puder trocar (max_trades).
        if len(ai_player.hand) < 3 or self.ai_trade_count >= self.max_trades:
            return False

        # seleciona as 3 piores cartas da IA pela própria 'potencia'
        worst_three_ai = sorted(ai_player.hand, key=lambda c: c.potencia)[:3]
        # Força média das 3 piores cartas da IA
        ai_avg = sum(c.potencia for c in worst_three_ai) / 3.0

        # a IA considera que o jogador pode ter cartas melhores do que ela.
        player_cards_count = len(player.hand)
        total_bancos = (
            len(self.deck.paiol_attack_deck)
            + len(self.deck.paiol_counter_deck)
            + len(self.deck.retreat_cards)
            + len(self.deck.cartas_especiais_player)
            + len(self.deck.cartas_especiais_ai)
        )

        # Heurística simplificada:
        # Mais cartas na mão do jogador => maior chance de ele ter cartas fortes
        # Menos cartas disponíveis nos bancos => maior chance de cartas fortes estarem na mão do jogador
        if total_bancos == 0:
            prob_player_better = 0.9
        else:
            ratio = player_cards_count / total_bancos
            # saturar entre 0 e 1
            prob_player_better = min(1.0, max(0.0, ratio))

        # Decide trocar se a IA avaliar sua média muito baixa ou se prob. do jogador estar melhor for alta
        threshold = 0.5  # Limiar de probabilidade
        if ai_avg < 3 or prob_player_better > threshold:
            # Realiza a troca
            self.trade_cards(ai_player, player)
            self.ai_trade_count += 1
            self.ia_fez_troca[mao_jogada] = True
            return True

        # Caso não atenda condições, chance aleatória de 20%
        should_trade_random = random.random() < 0.2
        if should_trade_random:
            self.trade_cards(ai_player, player)
            self.ai_trade_count += 1
            self.ia_fez_troca[mao_jogada] = True
            self.announce("As Ratonians realizaram uma troca de armas bem-sucedida.")
            return True

        return False

    # -------------------------------------------------------------------------

    def trade_cards(self, player1, player2):
        if len(player1.hand) < 3:
            self.announce(
                "A tomada de armas não pode ser realizada porque um dos jogadores não possui cartas suficientes na mão."
            )
            return
        if len(player2.hand) < 3:
            return

        # Retira 3 cartas aleatórias de cada lado
        player1_cards = random.sample(player1.hand, 3)
        player2_cards = random.sample(player2.hand, 3)

        for card in player1_cards:
            player1.hand.remove(card)
        for card in player2_cards:
            player2.hand.remove(card)

        # Troca efetiva
        player1.hand.extend(player2_cards)
        player2.hand.extend(player1_cards)

    # Ajuste para Kamikaze: passamos a mão imediatamente ao oponente e encerramos a rodada
    def perform_kamikaze_attack(self, attacker_index):
        attacker = self.players[attacker_index]
        defender = self.players[1 - attacker_index]

        if attacker.kamikaze_count >= self.max_trades:
            self.announce(f"{attacker.name} atingiu o limite de ataques Kamikaze.")
            return

        if attacker.aircrafts <= 1:
            self.announce(
                f"{attacker.name} não tem aeronaves suficientes para um Kamikaze."
            )
            return

        chance = random.random()
        if chance < 0.50:
            defender.aircrafts = max(0, defender.aircrafts - 1)
            self.announce(
                f"{attacker.name} realizaram um Ataque Kamikaze bem-sucedido! {defender.name} perdem 1 aeronave."
            )
            attacker.hands_won += 1
        else:
            attacker.aircrafts = max(0, attacker.aircrafts - 1)
            self.announce(
                f"Ataque Kamikaze falhou! {attacker.name} perderam 1 aeronave."
            )

        attacker.kamikaze_count += 1
        attacker.total_hands_played += 1

        # Termina imediatamente a “mão” corrente e passa a vez ao outro
        self.battle_cards = []  # limpa mesa
        self.end_hand_and_switch_turns()


    def announce_retreat_status(self):
        d = self.players[0]
        r = self.players[1]
        self.announce(f"Dragonians: {d.retreat_cards_total} recuos.")
        self.announce(f"Ratonians: {r.retreat_cards_total} recuos.")

    def announce_ai_info(self):
        opponent = self.players[1]
        self.announce(f"--- Info Ratonians ---")
        self.announce(f"Pontos: {opponent.score}")
        self.announce(f"Aeronaves: {opponent.aircrafts}")
        self.announce(f"Banco Ratonians: {len(opponent.bank)} cartas")
        self.announce(f"Mão Ratonians: {len(opponent.hand)} cartas (ocultas)")
        self.announce(f"Recuos disponíveis: {opponent.retreat_cards_total}")

    def announce_player_info(self):
        player = self.players[0]
        self.announce(f"--- Info: {player.name} ---")
        self.announce(f"Pontos: {player.score}")
        self.announce(f"Aeronaves: {player.aircrafts}")
        self.announce(f"Banco Dragonians: {len(player.bank)} cartas")
        self.announce(f"Cartas na Mão: {len(player.hand)}")
        self.announce(f"Recuos disponíveis: {player.retreat_cards_total}")
        self.announce(f"Mãos jogadas: {player.total_hands_played}")
        self.announce(f"Mãos vencidas: {player.hands_won}")

    def announce_deck_info(self):
        arzenal_count = len(self.deck.arzenal)
        paiol_attack_count = len(self.deck.paiol_attack_deck)
        paiol_counter_count = len(self.deck.paiol_counter_deck)
        retreat_cards_count = len(self.deck.retreat_cards)
        esp_player_count = len(self.deck.cartas_especiais_player)
        esp_ai_count = len(self.deck.cartas_especiais_ai)

        self.announce(f"Arsenal: {arzenal_count} cartas.")
        self.announce(f"Paiol Ataque: {paiol_attack_count} cartas.")
        self.announce(f"Paiol Defesa: {paiol_counter_count} cartas.")
        self.announce(f"Cartas de Recuo: {retreat_cards_count}")
        self.announce(f"Esp Dragonians: {esp_player_count}")
        self.announce(f"Esp Ratonians: {esp_ai_count}")

    def announce_hand(self):
        player = self.players[0]
        if player.hand:
            self.announce(f"Os Dragonians têm {len(player.hand)} armas à disposição:")
            for idx, card in enumerate(player.hand, start=1):
                self.announce(f'Arma {idx}: {card.name.replace("_", " ")}')
        else:
            self.announce("Os Dragonians não tem mais armas à disposição.")

    def select_previous_card(self):
        player = self.players[0]
        if player.hand:
            self.selected_card_index = (self.selected_card_index - 1) % len(player.hand)
            selected_card = player.hand[self.selected_card_index]
            card_info = (
                selected_card.get_info()
            )  # Obtém informações detalhadas da carta
            self.announce(
                f"Arma {self.selected_card_index + 1} selecionada: {card_info}"
            )

    def select_next_card(self):
        player = self.players[0]
        if player.hand:
            self.selected_card_index = (self.selected_card_index + 1) % len(player.hand)
            selected_card = player.hand[self.selected_card_index]
            card_info = (
                selected_card.get_info()
            )  # Obtém informações detalhadas da carta
            self.announce(
                f"Arma {self.selected_card_index + 1} selecionada: {card_info}"
            )

    def buy_attack_cards(self):
        player = self.players[0]
        opponent = self.players[1]
        if player.requested_ammo >= AMMO_REQUEST_LIMIT:
            self.announce("Limite de solicitações de munição atingido.")
            return
        num_to_draw = AMMO_DRAW_COUNTS[
            min(player.requested_ammo, len(AMMO_DRAW_COUNTS) - 1)
        ]
        if len(self.deck.paiol_attack_deck) < num_to_draw:
            self.announce("Não há cartas de Ataque suficientes no paiol.")
            return
        for _ in range(num_to_draw):
            card = self.deck.draw_paiol_attack_card()
            if card:
                player.hand.append(card)
                self.enable_shortcut(len(player.hand) - 1)
        player.requested_ammo += 1
        self.announce(f"Os Dragonians adquiriram {num_to_draw} armas de Ataque.")
        points_awarded = player.get_ammo_points_awarded()
        opponent.score += points_awarded
        if points_awarded > 0:
            self.announce(f"Ratonians ganham +{points_awarded} pontos.")
        self.check_end_game()

    def buy_defense_cards(self):
        player = self.players[0]
        opponent = self.players[1]
        if player.requested_ammo >= AMMO_REQUEST_LIMIT:
            self.announce("Limite de solicitações de munição atingido.")
            return
        num_to_draw = AMMO_DRAW_COUNTS[
            min(player.requested_ammo, len(AMMO_DRAW_COUNTS) - 1)
        ]
        if len(self.deck.paiol_counter_deck) < num_to_draw:
            self.announce("Não há cartas de Defesa suficientes no paiol.")
            return
        for _ in range(num_to_draw):
            card = self.deck.draw_paiol_counter_card()
            if card:
                player.hand.append(card)
                self.enable_shortcut(len(player.hand) - 1)

        player.requested_ammo += 1
        self.announce(f"Os Dragonians adquiriram {num_to_draw} armas de Defesa.")
        points_awarded = player.get_ammo_points_awarded()
        opponent.score += points_awarded
        if points_awarded > 0:
            self.announce(f"Ratonians ganham +{points_awarded} pontos.")
        self.check_end_game()

    def handle_ai_action(self):
        ai = self.players[1]
        if self.can_current_entity_play(ai):
            self.ai_play_card()

    def ai_play_card(self):
        ai_player = self.players[1]

        # Antes de jogar carta, IA verifica se quer trocar cartas (se ainda pode)
        if self.ai_trade_count < self.max_trades and self.ai_should_trade_cards(
            ai_player, self.players[0]
        ):
            self.trade_cards(ai_player, self.players[0])
            self.ai_trade_count += 1
            self.announce("Ratonians fizeram uma tomada de armas com sucesso.")

        # IA verifica Kamikaze
        if self.ai_should_do_kamikaze(ai_player):
            self.perform_kamikaze_attack(1)
            return

        self.ai_optimize_resources(ai_player)
        if not self.can_current_entity_play(ai_player):
            return

        attacking = self.who_is_attacking_now() == ai_player
        ai_card = self.ai_select_card(ai_player, attacking=attacking)
        if ai_card is None:
            if not self.ai_try_buy(ai_player, attacking=attacking):
                if self.ai_try_buy_special(ai_player):
                    ai_card = self.ai_select_card(ai_player, attacking=attacking)
                    if ai_card is None:
                        self.ai_exchange_aircraft(
                            ai_player, "Ataque" if attacking else "Contra-Ataque"
                        )
                        ai_card = self.ai_select_card(ai_player, attacking=attacking)
                        if ai_card is None:
                            self.announce("Ratonians não conseguem jogar. Perderam.")
                            ai_player.lost = True
                            self.end_game()
                            return
                else:
                    self.ai_exchange_aircraft(
                        ai_player, "Ataque" if attacking else "Contra-Ataque"
                    )
                    ai_card = self.ai_select_card(ai_player, attacking=attacking)
                    if ai_card is None:
                        self.announce("Ratonians não conseguem jogar. Perderam.")
                        ai_player.lost = True
                        self.end_game()
                        return
            else:
                ai_card = self.ai_select_card(ai_player, attacking=attacking)
                if ai_card is None:
                    if self.ai_try_buy_special(ai_player):
                        ai_card = self.ai_select_card(ai_player, attacking=attacking)
                        if ai_card is None:
                            self.ai_exchange_aircraft(
                                ai_player, "Ataque" if attacking else "Contra-Ataque"
                            )
                            ai_card = self.ai_select_card(
                                ai_player, attacking=attacking
                            )
                            if ai_card is None:
                                self.announce(
                                    "Ratonians não conseguem jogar. Perderam."
                                )
                                ai_player.lost = True
                                self.end_game()
                                return
                    else:
                        self.ai_exchange_aircraft(
                            ai_player, "Ataque" if attacking else "Contra-Ataque"
                        )
                        ai_card = self.ai_select_card(ai_player, attacking=attacking)
                        if ai_card is None:
                            self.announce("Ratonians não conseguem jogar. Perderam.")
                            ai_player.lost = True
                            self.end_game()
                            return

        if ai_card:
            ai_player.hand.remove(ai_card)
            if ai_card.type == "Especial":
                ai_player.special_cards_used += 1
                ai_player.special_cards_details[ai_card.name] = (
                    ai_player.special_cards_details.get(ai_card.name, 0) + 1
                )
            if ai_card.sound:
                ai_card.sound.play()
            self.battle_cards.append(ai_card)
            self.last_ai_card = ai_card
            self.announce_card_play(ai_player, ai_card)
            self.plays_this_hand += 1
            self.next_step()

    def ai_should_do_kamikaze(self, ai_player):
        if ai_player.kamikaze_count >= self.max_trades:
            return False
        if ai_player.aircrafts <= 2:
            return False
        # IA com chance maior de 30% se perceber que está em desvantagem
        # ou se aleatoriamente quiser arriscar
        behind_in_aircrafts = ai_player.aircrafts + 3 < self.players[0].aircrafts
        if behind_in_aircrafts and random.random() < 0.7:
            return True
        return random.random() < 0.3

    def ai_optimize_resources(self, ai_player):
        while len(ai_player.bank) >= 5:
            for _ in range(5):
                ai_player.bank.pop(0)
            ai_player.score += 3
            self.announce("Ratonians trocaram 5 cartas do banco por 3 pontos.")

        p = self.players[0]
        if ai_player.score >= 15:
            # IA mais agressiva: se estiver muito atrás em aeronaves, prioriza comprar aeronaves
            if ai_player.aircrafts + 10 < p.aircrafts:
                cost = 15
                if ai_player.score >= cost:
                    a_gain, _ = POINTS_EXCHANGE_TABLE[cost]
                    ai_player.score -= cost
                    ai_player.aircrafts += a_gain
                    self.announce(
                        f"Ratonians trocam {cost} pontos por +{a_gain} aeronaves."
                    )
                    self.check_marcos_aeronaves(ai_player)
            elif ai_player.aircrafts > p.aircrafts + 5:
                # Se estiver muito na frente, sabota o oponente
                cost = 25 if ai_player.score >= 25 else 15
                if ai_player.score >= cost:
                    a_gain, s_gain = POINTS_EXCHANGE_TABLE[cost]
                    sabotage = min(s_gain, p.aircrafts)
                    ai_player.score -= cost
                    p.aircrafts -= sabotage
                    self.announce(
                        f"As Ratonians  derrubaram {sabotage} aeronaves dos Dragonians."
                    )
            else:
                # Caso padrão: faz a troca menor (15 pontos) para ganhar +2 aeronaves
                if ai_player.score >= 15:
                    cost = 15
                    a_gain, s_gain = POINTS_EXCHANGE_TABLE[cost]
                    ai_player.score -= cost
                    ai_player.aircrafts += a_gain
                    self.announce(
                        f"Ratonians trocam {cost} pontos por +{a_gain} aeronaves."
                    )
                    self.check_marcos_aeronaves(ai_player)

    def ai_try_buy_special(self, ai_player):
        if ai_player.special_requests_made < 12:
            card = self.deck.draw_ai_special_card()
            if card:
                ai_player.hand.append(card)
                ai_player.special_requests_made += 1
                self.players[0].score += 3
                self.announce(
                    "As Ratonians  adquiriram uma arma pesada. Os Dragonians ganharam +3 pontos."
                )
                return True
        return False

    def ai_try_buy(self, ai_player, attacking=True):
        if ai_player.requested_ammo >= AMMO_REQUEST_LIMIT:
            return False
        num_to_draw = AMMO_DRAW_COUNTS[
            min(ai_player.requested_ammo, len(AMMO_DRAW_COUNTS) - 1)
        ]
        ai_player.requested_ammo += num_to_draw

        if attacking:
            for _ in range(num_to_draw):
                card = self.deck.draw_paiol_attack_card()
                if card:
                    ai_player.hand.append(card)
            self.announce("Ratonians compraram cartas de Ataque do paiol.")
        else:
            for _ in range(num_to_draw):
                card = self.deck.draw_paiol_counter_card()
                if card:
                    ai_player.hand.append(card)
            self.announce("Ratonians compraram cartas de Defesa do paiol.")
        return True

    def ai_exchange_aircraft(self, ai_player, needed_type):
        if ai_player.aircrafts <= 0:
            ai_player.lost = True
            self.announce("Ratonians não têm mais aeronaves para trocar e perderam.")
            self.end_game()
            return
        fetched_cards = []
        for _ in range(3):
            found_card = None
            temp_arz = []
            while self.deck.arzenal:
                candidate = self.deck.arzenal.pop()
                if (
                    candidate.type == needed_type
                    or candidate.type == "Especial"
                    or candidate.type == "Raio"
                ):
                    found_card = candidate
                    break
                else:
                    temp_arz.append(candidate)
            if found_card:
                fetched_cards.append(found_card)
                self.deck.arzenal.extend(temp_arz)
                random.shuffle(self.deck.arzenal)
            else:
                self.deck.arzenal.extend(temp_arz)
                random.shuffle(self.deck.arzenal)
                ai_player.lost = True
                self.announce(
                    "As Ratonians não encontraram armas necessárias e perderam."
                )
                self.end_game()
                return
        ai_player.aircrafts -= 1
        ai_player.hand.extend(fetched_cards)
        self.announce("Ratonians trocaram 1 aeronave por 3 armas necessárias.")
        self.check_marcos_aeronaves(ai_player)

    def ai_select_card(self, ai_player, attacking=True):
        valid_types = ["Ataque", "Contra-Ataque", "Especial", "Raio"]
        valid_cards = [c for c in ai_player.hand if c.type in valid_types]
        if ai_player.ai_memory.get("prefer_raio", False):
            raio_cards = [c for c in valid_cards if c.type == "Raio"]
            if raio_cards:
                valid_cards = raio_cards

        if not valid_cards:
            return None
        # Ordena do mais forte pro mais fraco
        valid_cards.sort(key=lambda c: (c.potencia, c.carta_bonus), reverse=True)
        chosen_card = valid_cards[0]
        return chosen_card

    def who_is_attacking_now(self):
        start = self.current_attacker_index
        turn = self.plays_this_hand % 4
        if start == 0:
            if turn == 0:
                return self.players[0]
            elif turn == 2:
                return self.players[1]
        else:
            if turn == 0:
                return self.players[1]
            elif turn == 2:
                return self.players[0]
        return None

    def use_retreat_card(self, player):
        opponent = self.players[1 - self.players.index(player)]
        if not self.can_current_entity_play(player):
            self.announce("Não é sua vez de jogar. Não pode usar recuo agora.")
            return
        if player.retreat_cards_total > 0:
            player.retreat_cards_total -= 1
            player.retreat_cards_used += 1
            opponent.score += 3
            self.announce(
                f"{player.name} usou Recuo Estratégico. {opponent.name} ganha +3 pontos."
            )
            self.battle_cards = []
            self.end_hand_and_switch_turns()
        else:
            self.announce(f"{player.name} não tem cartas de Recuo Estratégico.")

    def next_step(self):
        # Se completamos 4 jogadas (2 ataques e 2 defesas), resolvemos a batalha,
        # mas só se tivermos 4 cartas na mesa (senão, evitamos erro).
        if self.plays_this_hand % 4 == 0:
            if len(self.battle_cards) < 4:
                self.announce(
                    "Erro interno: Tentando resolver batalha, mas não há 4 cartas na mesa. Pulando resolução."
                )
                return
            self.resolve_battle_minimal()
        else:
            self.announce_turn_player()
            self.handle_ai_action()

    def announce_turn_player(self):
        turn = self.plays_this_hand % 5
        start = self.current_attacker_index

        turn = turn - 1
        if not self.battle_cards:
            return  # Se não há cartas na batalha, não faça nada

        last_card = self.battle_cards[-1].name.replace("_", " ")

        # Sequência de jogadas para quem começou atacando (start = 0 ou 1)
        if start == 0:  # Dragonians começam atacando

            if turn == 0:  # Dragonians atacam
                self.announce(f"Dragonians atacam com {last_card}.")
            elif turn == 1:  # Ratonians defendem
                self.announce(f"Ratonians defendem com {last_card}.")
            elif turn == 2:  # Ratonians atacam
                self.announce(f"Ratonians atacam com {last_card}.")
                self.announce("Cuidado, comandante!.")
            elif turn == 3:  # Dragonians defendem
                self.announce(f"Dragonians defendem com {last_card}.")
                start = start + 1
        else:  # Ratonians começam atacando
            if turn == 0:  # Ratonians atacam
                self.announce(f"Ratonians atacam com {last_card}.")
                self.announce("Cuidado, comandante!.")
            elif turn == 1:  # Dragonians defendem
                self.announce(f"Dragonians defendem com {last_card}.")
                self.announce(f"Agora, comandante!.")
                
            elif turn == 2:  # Dragonians atacam
                self.announce(f"Dragonians atacam com {last_card}.")
            elif turn == 3:  # Ratonians defendem
                self.announce(f"Ratonians defendem com {last_card}.")
                start = start - 1

        # Habilitar atalhos para a jogada atual
        self.enable_shortcut(turn)

    def end_hand_and_switch_turns(self):
        self.plays_this_hand = 0
        self.current_attacker_index = 1 - self.current_attacker_index
        self.announce_turn_player()
        self.ai_traded_this_hand = False  # Resetar flag ao final da mão
        self.handle_ai_action()

    def replenish_if_needed(self):
        p = self.players[0]
        ai = self.players[1]
        self.deck.try_distribute_cards(p, ai)

    def check_end_game(self):
        # Impede execução repetida após o término do jogo
        if getattr(self, "game_ended", False):
            return

        d = self.players[0]
        r = self.players[1]

        self.replenish_if_needed()

        if d.aircrafts <= 0:
            self.announce("Os Dragonians ficaram sem aeronaves! As Ratonians venceram!")
            self.end_game(lost=True)
            self.game_ended = True
            return
        elif r.aircrafts <= 0:
            self.announce("As Ratonians ficaram sem aeronaves! Os Dragonians venceram!")
            self.end_game(lost=True)
            self.game_ended = True
            return

        if d.aircrafts >= MAX_AERONAVES_TO_WIN:
            self.end_game()
            self.game_ended = True
            return
        if r.aircrafts >= MAX_AERONAVES_TO_WIN:
            self.end_game()
            self.game_ended = True
            return

        if not self.deck.arzenal:
            if d.aircrafts > r.aircrafts:
                self.announce(
                    "O arsenal acabou! Os Dragonians têm mais aeronaves e venceram!"
                )
                self.end_game()
            elif r.aircrafts > d.aircrafts:
                self.announce(
                    "O arsenal acabou! As Ratonians têm mais aeronaves e venceram!"
                )
                self.end_game()
            else:
                if d.score > r.score:
                    self.announce(
                        "O arsenal acabou! Empate em aeronaves, mas os Dragonians têm mais pontos e venceram!"
                    )
                    self.end_game()
                elif r.score > d.score:
                    self.announce(
                        "O arsenal acabou! Empate em aeronaves, mas as Ratonians têm mais pontos e venceram!"
                    )
                    self.end_game()
                else:
                    if len(d.bank) > len(r.bank):
                        self.announce(
                            "O arsenal acabou! Empate em aeronaves e pontos, mas os Dragonians têm mais cartas no banco e venceram!"
                        )
                        self.end_game()
                    elif len(r.bank) > len(d.bank):
                        self.announce(
                            "O arsenal acabou! Empate em aeronaves e pontos, mas as Ratonians têm mais cartas no banco e venceram!"
                        )
                        self.end_game()
                    else:
                        self.announce(
                            "O arsenal acabou! Empate total em aeronaves, pontos e cartas no banco."
                        )
                        self.end_game()
            self.game_ended = True
            return

        if not d.hand and not r.hand:
            self.announce("Ambos os jogadores estão sem cartas na mão. Fim da guerra.")
            self.end_game()
            self.game_ended = True

    def resolve_battle_minimal(self):
        if getattr(self, "game_ended", False):  # Evita ações se o jogo já acabou
            return
        start = self.current_attacker_index
        if start == 0:
            p_att_card = self.battle_cards[0]
            i_def_card = self.battle_cards[1]
            i_att_card = self.battle_cards[2]
            p_def_card = self.battle_cards[3]
        else:
            i_att_card = self.battle_cards[0]
            p_def_card = self.battle_cards[1]
            p_att_card = self.battle_cards[2]
            i_def_card = self.battle_cards[3]

        # Flags para saber quais eventos ocorreram
        rareamento = False
        aurora = False
        tempestade = False

        # --- Rareamento (afeta somente o defensor) ---
        if random.random() < RAREAMENTO_PROB:
            rareamento = True
            self.announce("rareamento espacial! Potência e bônus do defensor aumentados.")
            if start == 0:
                # Jogador ataca, IA defende
                i_def_card.potencia += 2
                i_def_card.carta_bonus += 3
            else:
                # IA ataca, Jogador defende
                p_def_card.potencia += 2
                p_def_card.carta_bonus += 3

        # --- Tempestade (afeta somente o atacante) ---
        if random.random() < TEMPESTADE_PROB:
            tempestade = True
            self.announce("Tempestade Meteórica! O atacante teve sua carta zerada.")
            if start == 0:
                # Jogador é o atacante
                p_att_card.potencia = 0
                p_att_card.carta_bonus = 0
            else:
                # IA é o atacante
                i_att_card.potencia = 0
                i_att_card.carta_bonus = 0

        # --- Aurora Estrelar (afeta somente o atacante se a carta for de "Raio") ---
        if random.random() < AURORA_PROB:
            aurora = True
            if start == 0:
                # Jogador atacando
                if "Raio" in p_att_card.name:
                    self.announce("Aurora Boreal Estelar! Carta de Raio do atacante perdeu 1 ponto de potência e bônus.")
                    p_att_card.potencia = max(0, p_att_card.potencia - 1)
                    p_att_card.carta_bonus = max(0, p_att_card.carta_bonus - 1)
            else:
                # IA atacando
                if "Raio" in i_att_card.name:
                    self.announce("Aurora Boreal Estelar! Carta de Raio do atacante perdeu 1 ponto de potência e bônus.")
                    i_att_card.potencia = max(0, i_att_card.potencia - 1)
                    i_att_card.carta_bonus = max(0, i_att_card.carta_bonus - 1)

        # --- Cálculo dos resultados ---
        res1 = (
            p_att_card.potencia - i_def_card.potencia
            if start == 0
            else i_att_card.potencia - p_def_card.potencia
        )
        res2 = (
            i_att_card.potencia - p_def_card.potencia
            if start == 0
            else p_att_card.potencia - i_def_card.potencia
        )

        total_jogador = 0
        total_ia = 0

        if res1 > 0:
            total_jogador += 1 if start == 0 else 0
            total_ia += 1 if start != 0 else 0
        elif res1 < 0:
            total_ia += 1 if start == 0 else 0
            total_jogador += 1 if start != 0 else 0
        else:
            total_jogador += 0.5
            total_ia += 0.5

        if res2 > 0:
            total_ia += 1 if start == 0 else 0
            total_jogador += 1 if start != 0 else 0
        elif res2 < 0:
            total_jogador += 1 if start == 0 else 0
            total_ia += 1 if start != 0 else 0
        else:
            total_jogador += 0.5
            total_ia += 0.5

        dragonians = self.players[0]
        ratonias = self.players[1]

        winner = None
        if total_jogador > total_ia:
            winner = dragonians
        elif total_ia > total_jogador:
            winner = ratonias

        if winner:
            winner.bank.extend(self.battle_cards)
            self.announce(
                f"{winner.name} ganharam a batalha e {len(self.battle_cards)} cartas da mesa foram para seu banco."
            )
            bonus_sum = 0
            if winner == dragonians:
                bonus_sum = p_att_card.carta_bonus + p_def_card.carta_bonus
            else:
                bonus_sum = i_att_card.carta_bonus + i_def_card.carta_bonus

            if bonus_sum > 0:
                if len(self.deck.arzenal) >= bonus_sum:
                    self.announce(
                        f"{winner.name} recebem {bonus_sum} cartas de bônus do Arsenal!"
                    )
                    for _ in range(bonus_sum):
                        b_card = self.deck.draw_arzenal_card(winner)
                        if b_card:
                            winner.hand.append(b_card)
                            self.enable_shortcut(len(winner.hand) - 1)
                else:
                    self.announce(
                        "O arsenal acabou antes que as cartas de bônus pudessem ser distribuídas."
                    )
                    self.battle_cards = []  # Certifique-se de limpar as cartas na mesa
                    self.check_end_game()  # Verifica imediatamente o estado do jogo após bônus insuficientes
        else:
            self.deck.arzenal.extend(self.battle_cards)
            random.shuffle(self.deck.arzenal)
            self.announce("Empate total na batalha. As cartas retornam ao Arsenal.")

        self.battle_cards = []
        self.end_hand_and_switch_turns()
        self.check_end_game()  # Garante que o jogo é verificado ao final de cada rodada

    def announce_card_play(self, player, card):
        start = self.current_attacker_index
        turn = self.plays_this_hand - 1
        if player.is_human:
            p_name_attack = "O jogador lançou"
            p_name_defend = "O jogador lançou"
        else:
            p_name_attack = "Ratonians lançam"
            p_name_defend = "Ratonians lançam"

        if start == 0:
            if turn == 0 and player == self.players[0]:
                print()
            elif turn == 1 and player == self.players[1]:
                print()
                self.last_ai_card = card
            elif turn == 2 and player == self.players[1]:
                print()
                self.last_ai_card = card
            elif turn == 3 and player == self.players[0]:
                print()
        else:
            if turn == 0 and player == self.players[1]:
                print()
                self.last_ai_card = card
            elif turn == 1 and player == self.players[0]:
                print()
            elif turn == 2 and player == self.players[0]:
                print()
            elif turn == 3 and player == self.players[1]:
                print()
                self.last_ai_card = card

    def can_current_entity_play(self, entity):
        start = self.current_attacker_index
        turn = self.plays_this_hand % 4
        if start == 0:
            if turn == 0 and entity == self.players[0]:
                return True
            if turn == 1 and entity == self.players[1]:
                return True
            if turn == 2 and entity == self.players[1]:
                return True
            if turn == 3 and entity == self.players[0]:
                return True
        else:
            if turn == 0 and entity == self.players[1]:
                return True
            if turn == 1 and entity == self.players[0]:
                return True
            if turn == 2 and entity == self.players[0]:
                return True
            if turn == 3 and entity == self.players[1]:
                return True
        return False

    def player_play_card(self, card_index):
        player = self.players[0]
        if not self.can_current_entity_play(player):
            self.announce("Não é vez dos Dragonians jogarem.")
            return
        if 0 <= card_index < len(player.hand):
            selected_card = player.hand[card_index]
            if not self.can_player_play_card(player, selected_card):
                self.announce("Os Dragonians não podem usar esse tipo de carta agora.")
                return
            if selected_card.sound:
                selected_card.sound.play()
            played_card = player.play_card(card_index)
            self.battle_cards.append(played_card)
            self.announce_card_play(player, played_card)
            self.plays_this_hand += 1
            self.next_step()
        else:
            self.announce("Arma sem munição!")

    def can_player_play_card(self, player, card):
        attacker = self.who_is_attacking_now()
        return card.type in ["Ataque", "Contra-Ataque", "Especial", "Raio"]

    def request_special_card(self, player):
        if player.special_requests_made < 12:
            if player.is_human:
                card = self.deck.draw_player_special_card()
            else:
                card = self.deck.draw_ai_special_card()

            if card:
                player.hand.append(card)
                self.enable_shortcut(len(player.hand) - 1)
                player.special_requests_made += 1
                opponent = self.players[1 - self.players.index(player)]
                opponent.score += 3
                if player.is_human:
                    self.announce(
                        "Os Dragonians retiraram uma arma pesada do baralho especial. As Ratonians  ganham +3 pontos."
                    )
                else:
                    self.announce(
                        "As Ratonians  retiraram uma arma pesada do baralho especial. Os Dragonians ganharam +3 pontos."
                    )
            else:
                self.announce("Não há mais armas pessadas disponíveis.")
        else:
            self.announce("Limite de cartas especiais atingido ou nenhuma disponível.")

    def buy_special_card(self, player):
        if player.special_requests_made < 12:
            if player.is_human:
                card = self.deck.draw_player_special_card()
            else:
                card = self.deck.draw_ai_special_card()

            if card:
                player.hand.append(card)
                self.enable_shortcut(len(player.hand) - 1)
                player.special_requests_made += 1
                opponent = self.players[1 - self.players.index(player)]
                opponent.score += 3
                if player.is_human:
                    self.announce(
                        "Os Dragonians adquiriram uma arma pesada. As Ratonians  ganharam +3 pontos."
                    )
                else:
                    self.announce(
                        "As Ratonians  adquiriram uma arma pesada. Os Dragonians ganharam +3 pontos."
                    )
            else:
                self.announce("Não há mais armas pesadas disponíveis.")
        else:
            self.announce("Limite de cartas especiais atingido ou nenhuma disponível.")

    def main_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            if not self.in_main_menu:
                self.handle_events()
                self.update()
                self.draw()
            pygame.time.wait(100)
            clock.tick(60)

    def update(self):
        if self.game_ended:
            self.running = False
            return
        self.check_end_game()

        # Condição para a IA tomar sua decisão independentemente da jogada do jogador
        self.handle_ai_action()

    def draw(self):
        if self.game_ended:
            return

        window.fill(GREEN)
        dragonians = self.players[0]
        ratonias = self.players[1]

        # Banco Dragonians (inferior esquerdo)
        player_bank_x = 50
        player_bank_y = HEIGHT - 150
        if dragonians.bank:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (player_bank_x, player_bank_y))
            else:
                pygame.draw.rect(window, BLACK, (player_bank_x, player_bank_y, 60, 100))
                pygame.draw.rect(
                    window, RED, (player_bank_x, player_bank_y, 60, 100), 2
                )
            text_b = font.render(
                f"Banco Dragonians: {len(dragonians.bank)}", True, WHITE
            )
            window.blit(text_b, (player_bank_x, player_bank_y + 110))
        else:
            pygame.draw.rect(
                window, (0, 0, 0, 0), (player_bank_x, player_bank_y, 60, 100), 0
            )

        # Mão Dragonians
        for idx, card in enumerate(dragonians.hand):
            x = player_bank_x + 100 * (idx + 1)  # Espaçamento entre as cartas
            y = player_bank_y - 100  # Ajuste vertical das cartas (subindo mais)

            if idx == self.selected_card_index:  # Destacar a carta selecionada
                card_rect = pygame.Rect(
                    x - 10, y - 30, 110, 180
                )  # Dimensão maior para a carta selecionada
                pygame.draw.rect(window, YELLOW, card_rect, 2)  # Adiciona borda amarela

                # Nome da arma acima da carta
                name_surface = font.render(card.name, True, WHITE)
                name_rect = name_surface.get_rect(
                    center=(x + 55, y - 40)
                )  # Centraliza acima da carta
                window.blit(name_surface, name_rect)

                # Potência, Tipo e Bônus em uma única linha abaixo da carta
                stats_text = (
                    f"P: {card.potencia} / B: {card.carta_bonus} / T: {card.type} "
                )
                stats_surface = font.render(stats_text, True, WHITE)
                stats_rect = stats_surface.get_rect(
                    center=(x + 55, y + 190)
                )  # Centraliza abaixo da carta
                window.blit(stats_surface, stats_rect)

                # Desenhar imagem da carta selecionada
                if card.image:
                    scaled_image = pygame.transform.scale(
                        card.image, card_rect.size
                    )  # Redimensiona a imagem
                    window.blit(scaled_image, (card_rect.x, card_rect.y))
                else:
                    pygame.draw.rect(window, WHITE, card_rect)
                    text_surf = font.render(card.name[:10], True, BLACK)
                    window.blit(text_surf, (x + 5, y + 60))
            else:  # Cartas não selecionadas
                card_rect = pygame.Rect(
                    x, y, 90, 150
                )  # Dimensão padrão para as demais cartas
                if card.image:
                    scaled_image = pygame.transform.scale(
                        card.image, card_rect.size
                    )  # Redimensiona a imagem
                    window.blit(scaled_image, (card_rect.x, card_rect.y))
                else:
                    pygame.draw.rect(window, WHITE, card_rect)
                    text_surf = font.render(card.name[:10], True, BLACK)
                    window.blit(text_surf, (x + 5, y + 60))

                pygame.draw.rect(
                    window, RED, card_rect, 2
                )  # Adiciona borda vermelha nas cartas não selecionadas

        # Banco Ratonians (topo direito)
        ai_bank_x = WIDTH - 110
        ai_bank_y = 20
        if ratonias.bank:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (ai_bank_x, ai_bank_y))
            else:
                pygame.draw.rect(window, BLACK, (ai_bank_x, ai_bank_y, 60, 100))
                pygame.draw.rect(window, RED, (ai_bank_x, ai_bank_y, 60, 100), 2)
            text_b_ai = font.render(
                f"Banco Ratonians: {len(ratonias.bank)}", True, WHITE
            )
            window.blit(text_b_ai, (ai_bank_x, ai_bank_y + 110))
        else:
            pygame.draw.rect(window, (0, 0, 0, 0), (ai_bank_x, ai_bank_y, 60, 100), 0)

        # Mão Ratonians (ocultamos a IA)
        for idx, _ in enumerate(ratonias.hand):
            x = ai_bank_x - 70 * (idx + 1)
            y = ai_bank_y
            card_rect = pygame.Rect(x, y, 60, 100)
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (x, y))
            else:
                pygame.draw.rect(window, BLACK, card_rect)
                pygame.draw.rect(window, RED, card_rect, 2)

        # Cartas na mesa
        for idx, card in enumerate(self.battle_cards):
            x = WIDTH // 2 - 30 + idx * 70
            y = HEIGHT // 2 - 50
            card_rect = pygame.Rect(x, y, 60, 100)
            if card.image:
                scaled_image = pygame.transform.scale(card.image, (60, 100))
                window.blit(scaled_image, (x, y))
            else:
                pygame.draw.rect(window, WHITE, card_rect)
                text_surf = font.render(card.name.replace("_", " ")[:10], True, BLACK)
                window.blit(text_surf, (x + 5, y + 40))

        # Arsenal (esquerda)
        arz_x = 50
        arz_y = 50
        if self.deck.arzenal:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (arz_x, arz_y))
            else:
                pygame.draw.rect(window, BLACK, (arz_x, arz_y, 60, 100))
                pygame.draw.rect(window, RED, (arz_x, arz_y, 60, 100), 2)
        text_arz = font.render(f"Arsenal:{len(self.deck.arzenal)}", True, WHITE)
        window.blit(text_arz, (arz_x, arz_y + 110))

        pd_x = arz_x
        pd_y = arz_y + 150
        if self.deck.paiol_counter_deck:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (pd_x, pd_y))
            else:
                pygame.draw.rect(window, BLACK, (pd_x, pd_y, 60, 100))
                pygame.draw.rect(window, RED, (pd_x, pd_y, 60, 100), 2)
        text_pd = font.render(
            f"Defesa:{len(self.deck.paiol_counter_deck)}", True, WHITE
        )
        window.blit(text_pd, (pd_x, pd_y + 110))

        pa_x = pd_x
        pa_y = pd_y + 150
        if self.deck.paiol_attack_deck:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (pa_x, pa_y))
            else:
                pygame.draw.rect(window, BLACK, (pa_x, pa_y, 60, 100))
                pygame.draw.rect(window, RED, (pa_x, pa_y, 60, 100), 2)
        text_pa = font.render(f"Ataque:{len(self.deck.paiol_attack_deck)}", True, WHITE)
        window.blit(text_pa, (pa_x, pa_y + 110))

        # Cartas Especiais / Recuo (direita)
        esp_x_ai = WIDTH - 110
        esp_y_ai = 200
        if self.deck.cartas_especiais_ai:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (esp_x_ai, esp_y_ai))
            else:
                pygame.draw.rect(window, BLACK, (esp_x_ai, esp_y_ai, 60, 100))
                pygame.draw.rect(window, RED, (esp_x_ai, esp_y_ai, 60, 100), 2)
        text_esp_ai = font.render(
            f"Esp Ratonians:{len(self.deck.cartas_especiais_ai)}", True, WHITE
        )
        window.blit(text_esp_ai, (esp_x_ai, esp_y_ai + 110))

        rec_x = esp_x_ai
        rec_y = esp_y_ai + 150
        if self.deck.retreat_cards:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (rec_x, rec_y))
            else:
                pygame.draw.rect(window, BLACK, (rec_x, rec_y, 60, 100))
                pygame.draw.rect(window, RED, (rec_x, rec_y, 60, 100), 2)
        text_rec = font.render(f"Recuo:{len(self.deck.retreat_cards)}", True, WHITE)
        window.blit(text_rec, (rec_x, rec_y + 110))

        esp_x_p = rec_x
        esp_y_p = rec_y + 150
        if self.deck.cartas_especiais_player:
            if self.card_back_image:
                scaled_back = pygame.transform.scale(self.card_back_image, (60, 100))
                window.blit(scaled_back, (esp_x_p, esp_y_p))
            else:
                pygame.draw.rect(window, BLACK, (esp_x_p, esp_y_p, 60, 100))
                pygame.draw.rect(window, RED, (esp_x_p, esp_y_p, 60, 100), 2)
        text_esp_p = font.render(
            f"Esp Dragonians:{len(self.deck.cartas_especiais_player)}", True, WHITE
        )
        window.blit(text_esp_p, (esp_x_p, esp_y_p + 110))

        self.draw_buttons()

        score_text = font.render(
            f"Dragonians Pontos: {dragonians.score} | Aeronaves: {dragonians.aircrafts}",
            True,
            WHITE,
        )
        opponent_text = font.render(
            f"Ratonians Pontos: {ratonias.score} | Aeronaves: {ratonias.aircrafts}",
            True,
            WHITE,
        )

        window.blit(score_text, (50, 50))
        window.blit(opponent_text, (WIDTH - 400, 50))

        pygame.display.flip()

    def draw_buttons(self):
        pygame.draw.rect(window, GRAY, self.retreat_button_rect)
        text = font.render("Recuo (↓)", True, BLACK)
        window.blit(
            text, (self.retreat_button_rect.x + 5, self.retreat_button_rect.y + 5)
        )

        pygame.draw.rect(window, GRAY, self.ammo_button_rect)
        text = font.render("Munição (M/N)", True, BLACK)
        window.blit(text, (self.ammo_button_rect.x + 5, self.ammo_button_rect.y + 5))

        pygame.draw.rect(window, GRAY, self.info_button_rect)
        text = font.render("Info (I)", True, BLACK)
        window.blit(text, (self.info_button_rect.x + 5, self.info_button_rect.y + 5))

        pygame.draw.rect(window, GRAY, self.hand_button_rect)
        text = font.render("Minhas Armas (H)", True, BLACK)
        window.blit(text, (self.hand_button_rect.x + 5, self.hand_button_rect.y + 5))

        pygame.draw.rect(window, GRAY, self.save_button_rect)
        text = font.render("Salvar (S)", True, BLACK)
        window.blit(text, (self.save_button_rect.x + 5, self.save_button_rect.y + 5))

    def main(self):
        self.main_loop()

    def confirm_exit(self):
        if self.player_name != "Dragonians":
            self.announce("Salvar antes de sair? S/N")
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            self.save_game()
                            self.announce("Saindo...")
                            pygame.quit()
                            sys.exit()
                        elif event.key == pygame.K_n:
                            self.announce("Saindo sem salvar...")
                            pygame.quit()
                            sys.exit()
                    elif event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
        else:
            self.announce(
                "Fugindo da guerra, comandante Dragonian? Volte aqui, covarde, que lhe vou dar uma surra!"
            )
            pygame.quit()
            sys.exit()

    def exit_game(self):
        self.confirm_exit()

    def enable_shortcut(self, index):
        if index in self.disabled_shortcuts:
            self.disabled_shortcuts.remove(index)

    def reset_shortcuts(self):
        self.disabled_shortcuts.clear()

    def save_game(self):
        if not self.save_file:
            self.announce("Modo anônimo não salva jogos.")
            return
        game_state = {
            "player_name": self.player_name,
            "deck": self.deck.to_dict(),
            "players": [p.to_dict() for p in self.players],
            "current_attacker_index": self.current_attacker_index,
            "selected_card_index": self.selected_card_index,
            "current_phase": self.current_phase,
            "battle_cards": [c.to_dict() for c in self.battle_cards],
            "turn_counter": self.turn_counter,
            "last_ai_card": self.last_ai_card.to_dict() if self.last_ai_card else None,
            "plays_this_hand": self.plays_this_hand,
            "hands_history": self.hands_history,
            "game_ended": self.game_ended,
        }
        try:
            with open(self.save_file, "w") as f:
                json.dump(game_state, f)
            self.announce("Jogo salvo com sucesso.")
        except IOError:
            self.announce("Erro ao salvar o jogo.")

    def load_game(self):
        if not self.save_file:
            self.announce("Modo anônimo não possui jogo salvo.")
            self.start_new_game(from_save=False)
            return
        try:
            with open(self.save_file, "r") as f:
                game_state = json.load(f)
            self.player_name = game_state["player_name"]
            self.deck = Deck.from_dict(game_state["deck"])
            from_dict_players = [Player.from_dict(p) for p in game_state["players"]]
            self.players = from_dict_players
            self.current_attacker_index = game_state["current_attacker_index"]
            self.selected_card_index = game_state["selected_card_index"]
            self.current_phase = game_state["current_phase"]
            self.battle_cards = [Card.from_dict(c) for c in game_state["battle_cards"]]
            self.turn_counter = game_state["turn_counter"]
            last_ai = game_state.get("last_ai_card")
            if last_ai:
                self.last_ai_card = Card.from_dict(last_ai)
            else:
                self.last_ai_card = None
            self.plays_this_hand = game_state.get("plays_this_hand", 0)
            self.hands_history = game_state.get("hands_history", [])
            self.game_ended = game_state.get("game_ended", False)
            self.reset_shortcuts()
            self.announce("Jogo carregado com sucesso.")
            self.in_main_menu = False
        except (IOError, json.JSONDecodeError):
            self.announce("Erro ao carregar. Novo jogo iniciado.")
            self.start_new_game(from_save=False)

    def replay_hands(self):
        for i, hand_data in enumerate(self.hands_history, start=1):
            self.announce(f"Mão {i}:")
            self.announce(
                f'Quem começou atacando: {"Jogador" if hand_data["start"]==0 else "Ratonians"}'
            )
            for card_info in hand_data["cards"]:
                self.announce(
                    f"{card_info['name']} (Pot: {card_info['potencia']} Bônus: {card_info['carta_bonus']} Tipo: {card_info['type']})"
                )
            self.announce(f'Vencedor da mão: {hand_data["winner"]}')
        self.announce("Fim do replay. Pressione qualquer tecla para sair.")
        self.wait_key()
        self.exit_game()


# Execução
if __name__ == "__main__":
    if len(sys.argv) > 1:
        player_name = sys.argv[1]
    else:
        player_name = "Dragonians"

    def main():
        try:
            global game_instance
            game_instance = Game(player_name)
            game_instance.main()
        except Exception as e:
            print(f"Erro: {e}")
            pygame.quit()
            sys.exit()

    main()
