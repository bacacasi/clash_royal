# Fichier principal pour le jeu Clash Royale graphique.
# Créé par Jules.

import pygame
import time
import os
import random
import sys

# --- Initialisation de Pygame et Constantes ---
pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1000, 500
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clash Royale Simplifié")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (50, 150, 255) # Bleu
AI_COLOR = (255, 80, 80) # Rouge
HP_BAR_GREEN = (0, 200, 0)
HP_BAR_RED = (200, 0, 0)
GROUND_COLOR = (112, 84, 62)
SKY_COLOR = (135, 206, 235)

# Polices
UI_FONT = pygame.font.SysFont('comicsans', 30)

# --- Classes de base du jeu ---

class Player:
    """Représente un joueur (le joueur humain ou l'IA)."""
    def __init__(self, name):
        self.name = name
        self.elixir = 5.0
        self.towers = []

class Tower:
    """Représente une tour."""
    def __init__(self, owner, position, hp=1500):
        self.owner = owner
        self.position = position
        self.max_hp = hp
        self.hp = hp
        self.symbol = "T"

class Unit:
    """Classe de base pour toutes les unités (personnages)."""
    def __init__(self, owner, position, hp, damage, speed, range, symbol):
        self.owner = owner
        self.position = float(position)
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.speed = speed
        self.range = range
        self.symbol = symbol

    def attack(self, target):
        target.hp -= self.damage

class Knight(Unit):
    """Unité de mêlée avec des stats équilibrées."""
    cost = 3
    def __init__(self, owner, position):
        symbol = "K" if owner.name == "Player" else "k"
        super().__init__(owner, position, hp=200, damage=50, speed=1, range=1, symbol=symbol)

class Archer(Unit):
    """Unité à distance avec moins de vie mais une plus grande portée."""
    cost = 3
    def __init__(self, owner, position):
        symbol = "A" if owner.name == "Player" else "a"
        super().__init__(owner, position, hp=100, damage=30, speed=1, range=5, symbol=symbol)

# --- Classe principale du jeu ---

class Game:
    """Gère l'état et la logique du jeu."""
    def __init__(self):
        self.logical_board_width = 100  # Unités logiques pour la distance
        self.player = Player("Player")
        self.ai = Player("AI")

        # Les positions sont maintenant logiques
        self.player_tower = Tower(self.player, 0)
        self.ai_tower = Tower(self.ai, self.logical_board_width)

        self.units = []
        self.game_over = False
        self.elixir_rate = 0.5  # Élixir par seconde
        self.last_update_time = time.time()

        # --- UI Buttons ---
        self.knight_button = pygame.Rect(10, HEIGHT - 60, 120, 50)
        self.archer_button = pygame.Rect(140, HEIGHT - 60, 120, 50)

    def spawn_unit(self, player, unit_type):
        if player.elixir >= unit_type.cost:
            player.elixir -= unit_type.cost
            # Les unités apparaissent près de leur tour respective
            position = 1 if player == self.player else self.logical_board_width - 1
            new_unit = unit_type(player, position)
            self.units.append(new_unit)

    def update(self):
        """Met à jour tout l'état du jeu pour un tick."""
        delta_time = time.time() - self.last_update_time
        self.last_update_time = time.time()

        # --- Mise à jour de l'élixir ---
        self.player.elixir = min(10, self.player.elixir + self.elixir_rate * delta_time)
        self.ai.elixir = min(10, self.ai.elixir + self.elixir_rate * delta_time)

        # --- Mouvement et attaques des unités ---
        for unit in self.units:
            targets = [self.ai_tower] + [u for u in self.units if u.owner != unit.owner] if unit.owner == self.player else [self.player_tower] + [u for u in self.units if u.owner != unit.owner]
            targets.sort(key=lambda t: abs(t.position - unit.position))
            closest_target = targets[0] if targets else None

            if closest_target:
                if abs(closest_target.position - unit.position) <= unit.range:
                    unit.attack(closest_target)
                else:
                    direction = 1 if unit.owner == self.player else -1
                    unit.position += direction * unit.speed * delta_time

        # --- Retrait des unités mortes et vérification des tours ---
        self.units = [u for u in self.units if u.hp > 0]
        if self.player_tower.hp <= 0 or self.ai_tower.hp <= 0:
            self.game_over = True

    def handle_ai_action(self):
        if self.ai.elixir >= 3 and random.random() < 0.1:
            self.spawn_unit(self.ai, random.choice([Knight, Archer]))

    def draw_health_bar(self, entity, x, y, width, height):
        """Dessine une barre de vie pour une entité à une position donnée."""
        ratio = max(0, entity.hp / entity.max_hp)
        # Barre de fond (rouge)
        pygame.draw.rect(WIN, HP_BAR_RED, (x - width // 2, y, width, height))
        # Barre de vie (verte)
        pygame.draw.rect(WIN, HP_BAR_GREEN, (x - width // 2, y, width * ratio, height))

    def render(self):
        """Dessine tous les éléments du jeu à l'écran."""
        # --- Fond ---
        WIN.fill(SKY_COLOR)
        ground_y = HEIGHT - 100
        pygame.draw.rect(WIN, GROUND_COLOR, (0, ground_y, WIDTH, 100))

        # --- Coordonnées et dimensions pour le rendu ---
        path_start_x = 100
        path_end_x = WIDTH - 100
        path_width = path_end_x - path_start_x
        scale_x = path_width / self.logical_board_width

        # --- Tours ---
        player_tower_rect = pygame.Rect(path_start_x - 50, ground_y - 80, 40, 80)
        pygame.draw.rect(WIN, PLAYER_COLOR, player_tower_rect)
        self.draw_health_bar(self.player_tower, player_tower_rect.centerx, player_tower_rect.top - 10, player_tower_rect.width, 5)

        ai_tower_rect = pygame.Rect(path_end_x + 10, ground_y - 80, 40, 80)
        pygame.draw.rect(WIN, AI_COLOR, ai_tower_rect)
        self.draw_health_bar(self.ai_tower, ai_tower_rect.centerx, ai_tower_rect.top - 10, ai_tower_rect.width, 5)

        # --- Unités ---
        for unit in self.units:
            screen_x = path_start_x + unit.position * scale_x
            color = PLAYER_COLOR if unit.owner == self.player else AI_COLOR

            if isinstance(unit, Knight):
                unit_rect = pygame.Rect(screen_x - 15, ground_y - 30, 30, 30)
                pygame.draw.rect(WIN, color, unit_rect)
                self.draw_health_bar(unit, unit_rect.centerx, unit_rect.top - 10, unit_rect.width, 4)
            elif isinstance(unit, Archer):
                unit_center = (int(screen_x), ground_y - 15)
                pygame.draw.circle(WIN, color, unit_center, 15)
                self.draw_health_bar(unit, unit_center[0], unit_center[1] - 25, 30, 4)

        # --- UI (Elixir et Boutons) ---
        player_elixir_text = UI_FONT.render(f"Elixir: {int(self.player.elixir)}", 1, BLACK)
        WIN.blit(player_elixir_text, (10, 10))

        # Bouton Chevalier
        pygame.draw.rect(WIN, PLAYER_COLOR, self.knight_button)
        knight_text = UI_FONT.render("Knight (3)", 1, WHITE)
        WIN.blit(knight_text, (self.knight_button.x + 10, self.knight_button.y + 10))

        # Bouton Archer
        pygame.draw.rect(WIN, PLAYER_COLOR, self.archer_button)
        archer_text = UI_FONT.render("Archer (3)", 1, WHITE)
        WIN.blit(archer_text, (self.archer_button.x + 10, self.archer_button.y + 10))

        # --- Mise à jour de l'affichage ---
        pygame.display.update()

    def main_loop(self):
        """Boucle de jeu principale pour la version graphique."""
        clock = pygame.time.Clock()

        while not self.game_over:
            clock.tick(60) # Limite le jeu à 60 images par seconde

            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.knight_button.collidepoint(event.pos):
                        self.spawn_unit(self.player, Knight)
                    elif self.archer_button.collidepoint(event.pos):
                        self.spawn_unit(self.player, Archer)

            # Logique du jeu
            if not self.game_over:
                self.update()
                self.handle_ai_action()

            # Rendu
            self.render()

        pygame.quit()
        sys.exit()

# --- Démarrage du jeu ---
if __name__ == "__main__":
    game = Game()
    game.main_loop()
