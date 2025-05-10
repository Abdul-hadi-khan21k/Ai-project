import pygame
import numpy as np
import random
import nltk
from nltk.corpus import words

# Ensure nltk word corpus is available
nltk.download('words')
with open("sowpods.txt") as f:
    ENGLISH_WORDS = set(line.strip().lower() for line in f if len(line.strip()) >= 3)

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1000, 700
HEX_SIZE = 40
BOARD_RADIUS = 5

# Colors - Dark Mode
WHITE = (30, 30, 30)
BLACK = (220, 220, 220)
GRAY = (80, 80, 80)
RED = (255, 80, 80)
BLUE = (80, 160, 255)
GREEN = (100, 255, 100)
LIGHT_RED = (80, 30, 30)
LIGHT_BLUE = (30, 30, 80)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hexagonal Scrabble")
font = pygame.font.Font(None, 36)

# Game state flags
game_started = False


def draw_start_screen():
    screen.fill(WHITE)
    title_text = font.render("Welcome to Hexagonal Scrabble", True, BLACK)
    start_text = font.render("Start", True, BLACK)
    exit_text = font.render("Exit", True, BLACK)

    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    start_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    exit_rect = exit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))

    pygame.draw.rect(screen, GRAY, start_rect.inflate(40, 20))
    pygame.draw.rect(screen, GRAY, exit_rect.inflate(40, 20))

    screen.blit(title_text, title_rect)
    screen.blit(start_text, start_rect)
    screen.blit(exit_text, exit_rect)

    return start_rect, exit_rect


def hex_to_pixel(q, r):
    x = WIDTH // 2 + HEX_SIZE * (3 / 2 * q)
    y = HEIGHT // 2 + HEX_SIZE * (np.sqrt(3) * (r + q / 2))
    return x, y


def hexagon_points(x, y, size):
    return [
        (x + size * np.cos(np.pi / 3 * i), y + size * np.sin(np.pi / 3 * i))
        for i in range(6)
    ]


DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]

board = {}
for q in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
    for r in range(-BOARD_RADIUS, BOARD_RADIUS + 1):
        if abs(q + r) <= BOARD_RADIUS:
            board[(q, r)] = None

player_score = 0
ai_score = 0
current_input = ""
selected_cell = None
validated_words = set()
player_rack = [random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8)]
last_scored_paths = []

LETTER_VALUES = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4,
    'G': 2, 'H': 4, 'I': 1, 'J': 8, 'K': 5, 'L': 1,
    'M': 3, 'N': 1, 'O': 1, 'P': 3, 'Q': 10, 'R': 1,
    'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
    'Y': 4, 'Z': 10
}


def draw_board():
    screen.fill(WHITE)
    for (q, r), tile in board.items():
        x, y = hex_to_pixel(q, r)
        polygon = hexagon_points(x, y, HEX_SIZE)

        for path, owner in last_scored_paths:
            if (q, r) in path:
                pygame.draw.polygon(screen, LIGHT_RED if owner == "player" else LIGHT_BLUE, polygon)

        pygame.draw.polygon(screen, GRAY, polygon, 2)

        if tile:
            letter, owner = tile
            color = RED if owner == "player" else BLUE
            text = font.render(letter, True, color)
            screen.blit(text, (x - 10, y - 10))

    if selected_cell:
        x, y = hex_to_pixel(*selected_cell)
        pygame.draw.polygon(screen, GREEN, hexagon_points(x, y, HEX_SIZE), 3)

    score_text = font.render(f"Player: {player_score}   AI: {ai_score}", True, BLACK)
    screen.blit(score_text, (20, 20))

    input_text = font.render(f"Letter: {current_input.upper()}", True, BLACK)
    screen.blit(input_text, (20, 60))

    rack_text = font.render("Rack: " + ' '.join(player_rack), True, BLACK)
    screen.blit(rack_text, (20, HEIGHT - 40))


def place_letter(q, r, letter, player):
    if board[(q, r)] is None:
        board[(q, r)] = (letter.upper(), player)
        return True
    return False


def collect_words():
    words_found = []
    for (q, r), tile in board.items():
        if tile:
            for dq, dr in DIRECTIONS:
                word = tile[0]
                path = [(q, r)]
                for i in range(1, 6):
                    pos = (q + dq * i, r + dr * i)
                    if pos in board and board[pos]:
                        word += board[pos][0]
                        path.append(pos)
                    else:
                        break
                    if len(word) >= 3 and word.lower() in ENGLISH_WORDS:
                        words_found.append((word.lower(), path))
    return words_found


def update_scores(current_player):
    global player_score, ai_score, last_scored_paths
    new_words = collect_words()
    last_scored_paths = []
    for word, path in new_words:
        if word not in validated_words:
            validated_words.add(word)
            last_pos = path[-1]
            owner = board[last_pos][1]
            if owner == current_player:
                points = sum(LETTER_VALUES.get(ch.upper(), 1) for ch in word)
                if owner == "player":
                    player_score += points
                else:
                    ai_score += points
                last_scored_paths.append((path, owner))


def score_potential_move(pos, letter):
    q, r = pos
    temp_board = board.copy()
    temp_board[pos] = (letter, "ai")
    score = 0
    directions_used = set()

    for dq, dr in DIRECTIONS:
        word = letter
        path = [pos]
        for i in range(1, 6):
            next_pos = (q + dq * i, r + dr * i)
            if next_pos in temp_board and temp_board[next_pos]:
                word += temp_board[next_pos][0]
                path.append(next_pos)
            else:
                break
        if len(word) >= 3 and word.lower() in ENGLISH_WORDS:
            word_score = sum(LETTER_VALUES.get(ch.upper(), 1) for ch in word)
            score += word_score
            directions_used.add((dq, dr))

    return score + len(directions_used)


def ai_play():
    available = [pos for pos, val in board.items() if val is None]
    if not available:
        return

    best_score = -1
    best_move = None

    for pos in available:
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            move_score = score_potential_move(pos, letter)
            if move_score > best_score:
                best_score = move_score
                best_move = (pos, letter)

    if best_move:
        (q, r), letter = best_move
        place_letter(q, r, letter, "ai")
        update_scores("ai")


def refill_rack():
    while len(player_rack) < 8:
        player_rack.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))


def check_winner():
    if player_score >= 150 and ai_score >= 150:
        return "It's a tie!"
    elif player_score >= 150:
        return "Player wins!"
    elif ai_score >= 150:
        return "AI wins!"
    return None


def show_winner_message(message):
    screen.fill(WHITE)
    text = font.render(message, True, BLACK)
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, rect)
    pygame.display.flip()
    pygame.time.delay(5000)

# Main loop
running = True
player_turn = True
clock = pygame.time.Clock()

while running:
    if not game_started:
        start_rect, exit_rect = draw_start_screen()
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    game_started = True
                elif exit_rect.collidepoint(event.pos):
                    running = False
        continue

    draw_board()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            for (q, r) in board:
                hx, hy = hex_to_pixel(q, r)
                if np.hypot(hx - x, hy - y) < HEX_SIZE:
                    selected_cell = (q, r)
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and player_turn and selected_cell:
                if current_input.isalpha() and len(current_input) == 1 and current_input.upper() in player_rack:
                    if place_letter(selected_cell[0], selected_cell[1], current_input, "player"):
                        player_rack.remove(current_input.upper())
                        refill_rack()
                        update_scores("player")

                        winner = check_winner()
                        if winner:
                            show_winner_message(winner)
                            running = False
                        else:
                            player_turn = False
                            ai_play()

                            winner = check_winner()
                            if winner:
                                show_winner_message(winner)
                                running = False
                            else:
                                player_turn = True
                current_input = ""
            elif event.key == pygame.K_BACKSPACE:
                current_input = current_input[:-1]
            elif event.unicode.isalpha():
                current_input += event.unicode

    clock.tick(30)

pygame.quit()
