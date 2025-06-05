"""Blackjack simulator using pygame."""

import random
import sys
import time

import pygame
import matplotlib.pyplot as plt

# Inicializar pygame
pygame.init()

# Dimensiones de la ventana
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blackjack - by Joxarx")

# Colores
BACKGROUND = (7, 99, 36)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GOLD = (212, 175, 55)
CHIP_COLOR = (180, 0, 0)
GREEN = (0, 128, 0)
LIGHT_GREEN = (100, 200, 100)

# Configuración
FPS = 60
DEALER_DELAY = 0.5

# Fuentes
font = pygame.font.SysFont("arial", 24)
title_font = pygame.font.SysFont("arial", 40, bold=True)
button_font = pygame.font.SysFont("arial", 28)


class Card:
    """Simple playing card."""

    def __init__(self, suit: str, value: str) -> None:
        self.suit = suit
        self.value = value
        self.visible = True

    def get_numeric_value(self):
        if self.value in ["J", "Q", "K"]:
            return 10
        elif self.value == "A":
            return 11  # El As se manejará como 1 u 11 según convenga
        else:
            return int(self.value)

    def draw(self, x, y):
        card_width, card_height = 100, 140
        rect = pygame.Rect(x, y, card_width, card_height)

        if self.visible:
            pygame.draw.rect(screen, WHITE, rect, 0, 10)
            pygame.draw.rect(screen, BLACK, rect, 2, 10)

            # Color del palo
            color = RED if self.suit in ["♥", "♦"] else BLACK

            # Valor
            value_text = font.render(self.value, True, color)
            screen.blit(value_text, (x + 10, y + 10))

            # Palo
            suit_text = font.render(self.suit, True, color)
            screen.blit(suit_text, (x + 80, y + 120))

            # Palo grande en el centro
            big_suit = pygame.font.SysFont("arial", 50).render(
                self.suit, True, color
            )
            screen.blit(big_suit, (x + 30, y + 50))
        else:
            # Parte trasera de la carta
            pygame.draw.rect(screen, (150, 0, 0), rect, 0, 10)
            pygame.draw.rect(screen, GOLD, rect, 3, 10)
            for i in range(5):
                pygame.draw.circle(
                    screen, GOLD, (x + 50, y + 30 + i * 20), 10, 2
                )


class Deck:
    """Standard 52-card deck."""

    def __init__(self) -> None:
        self.cards: list[Card] = []
        self.build()

    def build(self):
        suits = ["♠", "♥", "♦", "♣"]
        values = [
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "J",
            "Q",
            "K",
            "A",
        ]
        self.cards = [Card(suit, value) for suit in suits for value in values]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self) -> Card | None:
        return self.cards.pop() if self.cards else None


def animate_deal(game, card: Card, dest_x: int, dest_y: int, buttons: list["Button"]):
    """Simple animation moving a card from the deck to a hand."""
    start_x, start_y = WIDTH // 2 - 50, -150
    steps = 15
    for i in range(steps + 1):
        x = start_x + (dest_x - start_x) * i / steps
        y = start_y + (dest_y - start_y) * i / steps
        draw_game(game, buttons)
        card.draw(int(x), int(y))
        pygame.display.flip()
        pygame.time.delay(int(1000 / FPS))


class Player:
    """Represents a blackjack player."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.hand: list[Card] = []
        self.score = 0
        self.bust = False

    def add_card(self, card: Card) -> None:
        self.hand.append(card)
        self.calculate_score()

    def calculate_score(self) -> None:
        self.score = 0
        aces = 0

        for card in self.hand:
            if card.value == "A":
                aces += 1
            self.score += card.get_numeric_value()

        # Ajustar Ases
        while self.score > 21 and aces > 0:
            self.score -= 10
            aces -= 1

        self.bust = self.score > 21

    def draw_hand(self, start_x: int, y: int) -> None:
        for i, card in enumerate(self.hand):
            card.draw(start_x + i * 110, y)


def draw_chips(x: int, y: int, amount: int) -> None:
    """Draw simple betting chips."""
    for i in range(amount):
        pygame.draw.circle(screen, CHIP_COLOR, (x + i * 15, y), 10)
        pygame.draw.circle(screen, WHITE, (x + i * 15, y), 10, 2)


class Button:
    """Simple UI button."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: tuple[int, int, int],
        hover_color: tuple[int, int, int],
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color

    def draw(self) -> None:
        pygame.draw.rect(screen, self.current_color, self.rect, 0, 10)
        pygame.draw.rect(screen, BLACK, self.rect, 2, 10)
        text_surf = button_font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos: tuple[int, int]) -> bool:
        if self.rect.collidepoint(pos):
            self.current_color = self.hover_color
            return True
        self.current_color = self.color
        return False

    def is_clicked(
        self, pos: tuple[int, int], event: pygame.event.Event
    ) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


class BlackjackGame:
    """Encapsulates game logic and state."""

    def __init__(self) -> None:
        self.deck = Deck()
        self.player = Player("Jugador")
        self.dealer = Player("Crupier")
        self.game_state = "betting"  # betting, player_turn, dealer_turn, game_over
        self.message = "Ajusta tu apuesta"
        self.result = ""
        self.wins = 0
        self.losses = 0
        self.bank = 100
        self.bet = 10
        self.new_round_initialized = False

    def new_game(self) -> None:
        self.deck = Deck()
        self.deck.shuffle()
        self.player = Player("Jugador")
        self.dealer = Player("Crupier")
        self.game_state = "betting"
        self.message = "Ajusta tu apuesta"
        self.result = ""
        self.new_round_initialized = False

    def start_round(self, buttons: list["Button"]) -> None:
        if self.bet > self.bank:
            self.message = "No tienes fichas suficientes"
            return

        self.bank -= self.bet
        self.deck.shuffle()
        self.player = Player("Jugador")
        self.dealer = Player("Crupier")
        self.game_state = "player_turn"
        self.message = "¿Pedir o plantarse?"
        self.result = ""

        # Repartir cartas iniciales con animación
        for target in [self.player, self.dealer, self.player, self.dealer]:
            card = self.deck.deal()
            if target is self.dealer and len(target.hand) == 1:
                card.visible = False
            animate_deal(self, card, 50 + len(target.hand) * 110, 120 if target is self.dealer else 360, buttons)
            target.add_card(card)

    def hit(self, buttons: list["Button"]) -> None:
        card = self.deck.deal()
        animate_deal(self, card, 50 + len(self.player.hand) * 110, 360, buttons)
        self.player.add_card(card)
        if self.player.bust:
            self.game_state = "game_over"
            self.message = "¡Te has pasado de 21!"
            self.result = "¡Gana el crupier!"
            self.dealer.hand[1].visible = True
        else:
            self.message = "¿Pedir o plantarse?"

    def stand(self, buttons: list["Button"]) -> None:
        self.game_state = "dealer_turn"
        self.dealer.hand[1].visible = True
        self.dealer.calculate_score()
        self.message = "Turno del crupier..."

        # El dealer juega automáticamente con animaciones
        while self.dealer.score < 17 and not self.dealer.bust:
            card = self.deck.deal()
            animate_deal(self, card, 50 + len(self.dealer.hand) * 110, 120, buttons)
            self.dealer.add_card(card)
            time.sleep(DEALER_DELAY)

        self.determine_winner()

    def determine_winner(self) -> None:
        self.game_state = "game_over"

        if self.dealer.bust:
            self.result = "¡Gana el jugador! (Crupier se pasó)"
            self.wins += 1
            self.bank += self.bet * 2
        elif self.player.score > self.dealer.score:
            self.result = "¡Gana el jugador!"
            self.wins += 1
            self.bank += self.bet * 2
        elif self.player.score < self.dealer.score:
            self.result = "¡Gana el crupier!"
            self.losses += 1
        else:
            self.result = "¡Empate!"
            self.bank += self.bet

        self.message = "Juego terminado"


def draw_game(game: BlackjackGame, buttons: list[Button]) -> None:
    """Render the current game state."""
    # Fondo
    screen.fill(BACKGROUND)

    # Título
    title = title_font.render("BLACKJACK", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

    # Cartas del dealer
    dealer_score = game.dealer.score if game.dealer.hand[1].visible else "?"
    dealer_text = font.render(f"Crupier: {dealer_score}", True, WHITE)
    screen.blit(dealer_text, (50, 80))
    game.dealer.draw_hand(50, 120)

    # Separador
    pygame.draw.line(screen, GOLD, (0, 280), (WIDTH, 280), 3)

    # Cartas del jugador
    player_text = font.render(f"Jugador: {game.player.score}", True, WHITE)
    screen.blit(player_text, (50, 320))
    game.player.draw_hand(50, 360)

    # Apuesta actual y banco
    bank_text = font.render(f"Banco: {game.bank}", True, WHITE)
    screen.blit(bank_text, (WIDTH - bank_text.get_width() - 20, 120))
    bet_text = font.render(f"Apuesta: {game.bet}", True, WHITE)
    screen.blit(bet_text, (WIDTH - bet_text.get_width() - 20, 150))
    draw_chips(WIDTH - 150, 180, min(game.bet // 10, 5))

    # Marcador
    score_text = font.render(
        f"Victorias: {game.wins}  Derrotas: {game.losses}", True, WHITE
    )
    screen.blit(score_text, (WIDTH - score_text.get_width() - 20, 80))

    # Mensajes
    message_text = font.render(game.message, True, WHITE)
    screen.blit(
        message_text, (WIDTH // 2 - message_text.get_width() // 2, 500)
    )

    if game.result:
        result_text = font.render(game.result, True, GOLD)
        screen.blit(
            result_text, (WIDTH // 2 - result_text.get_width() // 2, 540)
        )

    # Botones
    for button in buttons:
        button.draw()


def main() -> None:
    """Entry point of the application."""

    game = BlackjackGame()
    clock = pygame.time.Clock()

    # Crear botones
    bet_up_button = Button(50, 450, 40, 40, "+", LIGHT_GREEN, GREEN)
    bet_down_button = Button(100, 450, 40, 40, "-", LIGHT_GREEN, GREEN)
    play_button = Button(150, 450, 120, 50, "Jugar", LIGHT_GREEN, GREEN)
    hit_button = Button(150, 450, 120, 50, "Pedir", LIGHT_GREEN, GREEN)
    stand_button = Button(330, 450, 120, 50, "Plantarse", LIGHT_GREEN, GREEN)
    new_game_button = Button(510, 450, 180, 50, "Nuevo Juego", LIGHT_GREEN, GREEN)
    stats_button = Button(WIDTH - 160, 20, 140, 40, "Estadísticas", LIGHT_GREEN, GREEN)

    buttons = [
        bet_up_button,
        bet_down_button,
        play_button,
        hit_button,
        stand_button,
        new_game_button,
        stats_button,
    ]

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if stats_button.is_clicked(mouse_pos, event):
                plt.figure(figsize=(4, 3))
                plt.bar(["Ganadas", "Perdidas"], [game.wins, game.losses], color=["green", "red"])
                plt.title("Estadísticas")
                plt.show()

            if game.game_state == "betting":
                if bet_up_button.is_clicked(mouse_pos, event):
                    game.bet += 10
                elif bet_down_button.is_clicked(mouse_pos, event) and game.bet > 10:
                    game.bet -= 10
                elif play_button.is_clicked(mouse_pos, event):
                    game.start_round([hit_button, stand_button, stats_button])

            elif game.game_state == "player_turn":
                if hit_button.is_clicked(mouse_pos, event):
                    game.hit([hit_button, stand_button, stats_button])
                elif stand_button.is_clicked(mouse_pos, event):
                    game.stand([hit_button, stand_button, stats_button])

            if new_game_button.is_clicked(mouse_pos, event) and game.game_state == "game_over":
                game.new_game()

        # Seleccionar botones activos según el estado
        if game.game_state == "betting":
            active_buttons = [bet_up_button, bet_down_button, play_button, stats_button]
        elif game.game_state == "player_turn":
            active_buttons = [hit_button, stand_button, stats_button]
        elif game.game_state == "game_over":
            active_buttons = [new_game_button, stats_button]
        else:
            active_buttons = [stats_button]

        for button in active_buttons:
            button.check_hover(mouse_pos)

        # Dibujar el juego
        draw_game(game, active_buttons)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
