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
GROUND_COLOR = (112, 84, 62) # Ancien
SKY_COLOR = (135, 206, 235) # Ancien
GRASS_COLOR = (34, 139, 34)
RIVER_COLOR = (70, 130, 180)
BRIDGE_COLOR = (184, 134, 11) # Ocre

# Polices
UI_FONT = pygame.font.SysFont('sans-serif', 30)

# --- Classes de base du jeu ---

class Player:
    """Représente un joueur (le joueur humain ou l'IA)."""
    def __init__(self, name):
        self.name = name
        self.elixir = 5.0
        self.towers = []

class Tower:
    """Représente une tour."""
    def __init__(self, owner, pos, tower_type='princess', hp=1500):
        self.owner = owner
        self.pos = pygame.math.Vector2(pos)
        self.tower_type = tower_type
        if self.tower_type == 'king':
            hp = 2500
        self.max_hp = hp
        self.hp = hp
        self.size = (60, 100) if self.tower_type == 'king' else (40, 80)

class Unit:
    """Classe de base pour toutes les unités (personnages)."""
    def __init__(self, owner, pos, hp, damage, speed, range):
        self.owner = owner
        self.pos = pygame.math.Vector2(pos)
        self.max_hp = hp
        self.hp = hp
        self.damage = damage
        self.speed = speed  # en pixels par seconde
        self.range = range  # en pixels

    def attack(self, target):
        target.hp -= self.damage

class Knight(Unit):
    """Unité de mêlée avec des stats équilibrées."""
    cost = 3
    def __init__(self, owner, pos):
        super().__init__(owner, pos, hp=200, damage=50, speed=40, range=40)

class Archer(Unit):
    """Unité à distance avec moins de vie mais une plus grande portée."""
    cost = 3
    def __init__(self, owner, pos):
        super().__init__(owner, pos, hp=100, damage=30, speed=50, range=120)

# --- Classe principale du jeu ---

class Game:
    """Gère l'état et la logique du jeu."""
    def __init__(self):
        self.player = Player("Player")
        self.ai = Player("AI")

        self.player.towers = [
            Tower(self.player, (WIDTH * 1/4, HEIGHT - 120), 'princess'),
            Tower(self.player, (WIDTH * 3/4, HEIGHT - 120), 'princess'),
            Tower(self.player, (WIDTH * 1/2, HEIGHT - 80), 'king')
        ]
        self.ai.towers = [
            Tower(self.ai, (WIDTH * 1/4, 120), 'princess'),
            Tower(self.ai, (WIDTH * 3/4, 120), 'princess'),
            Tower(self.ai, (WIDTH * 1/2, 80), 'king')
        ]

        self.units = []
        self.game_over = False
        self.winner = None
        self.elixir_rate = 0.5
        self.last_update_time = time.time()

        # --- UI Buttons ---
        self.knight_button = pygame.Rect(10, HEIGHT - 60, 120, 50)
        self.archer_button = pygame.Rect(140, HEIGHT - 60, 120, 50)
        self.selected_unit_type = None


    def spawn_unit(self, player, unit_type, pos):
        if player.elixir >= unit_type.cost:
            player.elixir -= unit_type.cost
            new_unit = unit_type(player, pos)
            self.units.append(new_unit)

    def update(self):
        delta_time = time.time() - self.last_update_time
        self.last_update_time = time.time()

        self.player.elixir = min(10, self.player.elixir + self.elixir_rate * delta_time)
        self.ai.elixir = min(10, self.ai.elixir + self.elixir_rate * delta_time)

        # --- Mouvement et attaques des unités ---
        all_targets = self.player.towers + self.ai.towers + self.units
        for unit in self.units:
            enemy_targets = [t for t in all_targets if t.owner != unit.owner]
            if not enemy_targets:
                continue

            enemy_targets.sort(key=lambda t: unit.pos.distance_to(t.pos))
            closest_target = enemy_targets[0]

            if unit.pos.distance_to(closest_target.pos) <= unit.range:
                unit.attack(closest_target)
            else:
                # --- Logique de Mouvement 2D ---
                is_player_unit = unit.owner == self.player

                # La position Y de l'autre côté de la rivière
                # Les unités du joueur (en bas) montent, les unités de l'IA (en haut) descendent
                enemy_side_y = HEIGHT / 2 - 20 if is_player_unit else HEIGHT / 2 + 20

                # Déterminer le pont cible en fonction de la position x de l'unité
                target_bridge_x = WIDTH / 4 if unit.pos.x < WIDTH / 2 else WIDTH * 3 / 4

                # Si l'unité n'a pas encore atteint l'autre côté de la rivière
                if (is_player_unit and unit.pos.y > enemy_side_y) or (not is_player_unit and unit.pos.y < enemy_side_y):
                    # Viser le pont
                    immediate_target_pos = pygame.math.Vector2(target_bridge_x, HEIGHT / 2)
                else:
                    # Une fois la rivière traversée, viser la cible ennemie la plus proche
                    immediate_target_pos = closest_target.pos

                # Déplacer l'unité vers sa cible immédiate
                if unit.pos.distance_to(immediate_target_pos) > 5: # Marge pour éviter les tremblements
                    direction_vec = (immediate_target_pos - unit.pos).normalize()
                    unit.pos += direction_vec * unit.speed * delta_time

        # --- Retrait des unités/tours mortes ---
        self.units = [u for u in self.units if u.hp > 0]
        self.player.towers = [t for t in self.player.towers if t.hp > 0]
        self.ai.towers = [t for t in self.ai.towers if t.hp > 0]

        # --- Vérification de fin de partie ---
        player_king_down = not any(t.tower_type == 'king' for t in self.player.towers)
        ai_king_down = not any(t.tower_type == 'king' for t in self.ai.towers)

        if player_king_down:
            self.game_over = True
            self.winner = self.ai
        elif ai_king_down:
            self.game_over = True
            self.winner = self.player

    def handle_ai_action(self):
        if self.ai.elixir >= 3 and random.random() < 0.1:
            pos = (random.randint(50, WIDTH - 50), random.randint(50, HEIGHT // 2 - 50))
            self.spawn_unit(self.ai, random.choice([Knight, Archer]), pos)

    def draw_health_bar(self, entity, width, height):
        """Dessine une barre de vie pour une entité."""
        ratio = max(0, entity.hp / entity.max_hp)
        bar_pos_x = entity.pos.x - width // 2
        bar_pos_y = entity.pos.y - entity.size[1] // 2 - 10 if isinstance(entity, Tower) else entity.pos.y - 20

        pygame.draw.rect(WIN, HP_BAR_RED, (bar_pos_x, bar_pos_y, width, height))
        pygame.draw.rect(WIN, HP_BAR_GREEN, (bar_pos_x, bar_pos_y, width * ratio, height))

    def render(self):
        """Dessine tous les éléments du jeu."""
        # --- Dessin de l'arène ---
        WIN.fill(GRASS_COLOR)
        # Rivière
        pygame.draw.rect(WIN, RIVER_COLOR, (0, HEIGHT/2 - 40, WIDTH, 80))
        # Ponts
        pygame.draw.rect(WIN, BRIDGE_COLOR, (WIDTH * 1/4 - 30, HEIGHT/2 - 40, 60, 80))
        pygame.draw.rect(WIN, BRIDGE_COLOR, (WIDTH * 3/4 - 30, HEIGHT/2 - 40, 60, 80))

        for tower in self.player.towers + self.ai.towers:
            color = PLAYER_COLOR if tower.owner == self.player else AI_COLOR
            center = (int(tower.pos.x), int(tower.pos.y))
            rect = pygame.Rect(center[0] - tower.size[0]//2, center[1] - tower.size[1]//2, tower.size[0], tower.size[1])
            pygame.draw.rect(WIN, color, rect)
            self.draw_health_bar(tower, tower.size[0], 5)

        for unit in self.units:
            color = PLAYER_COLOR if unit.owner == self.player else AI_COLOR
            center = (int(unit.pos.x), int(unit.pos.y))
            if isinstance(unit, Knight):
                rect = pygame.Rect(center[0] - 15, center[1] - 15, 30, 30)
                pygame.draw.rect(WIN, color, rect)
                self.draw_health_bar(unit, 30, 4)
            elif isinstance(unit, Archer):
                pygame.draw.circle(WIN, color, center, 15)
                self.draw_health_bar(unit, 30, 4)

        # --- UI ---
        player_elixir_text = UI_FONT.render(f"Elixir: {int(self.player.elixir)}", 1, BLACK)
        WIN.blit(player_elixir_text, (10, 10))
        pygame.draw.rect(WIN, PLAYER_COLOR, self.knight_button)
        knight_text = UI_FONT.render("Knight (3)", 1, WHITE)
        WIN.blit(knight_text, (self.knight_button.x + 10, self.knight_button.y + 10))
        pygame.draw.rect(WIN, PLAYER_COLOR, self.archer_button)
        archer_text = UI_FONT.render("Archer (3)", 1, WHITE)
        WIN.blit(archer_text, (self.archer_button.x + 10, self.archer_button.y + 10))

        # --- Dessin du mode de placement ---
        if self.selected_unit_type:
            mouse_pos = pygame.mouse.get_pos()
            # Zone de déploiement valide (côté joueur)
            valid_placement = mouse_pos[1] > HEIGHT / 2
            # Couleur de prévisualisation (bleu si valide, rouge si invalide)
            preview_color = (*PLAYER_COLOR, 128) if valid_placement else (*AI_COLOR, 128)

            # Prévisualisation de l'unité
            if self.selected_unit_type == Knight:
                pygame.draw.rect(WIN, preview_color, (mouse_pos[0] - 15, mouse_pos[1] - 15, 30, 30))
            elif self.selected_unit_type == Archer:
                pygame.draw.circle(WIN, preview_color, mouse_pos, 15)

        pygame.display.update()

    def main_loop(self):
        """Boucle de jeu principale."""
        clock = pygame.time.Clock()
        while not self.game_over:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True

                # Clic droit pour annuler le placement
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.selected_unit_type = None

                # Clic gauche
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Si une unité est sélectionnée, on essaie de la placer
                    if self.selected_unit_type:
                        # On ne peut placer que de notre côté de la rivière
                        if event.pos[1] > HEIGHT / 2:
                            self.spawn_unit(self.player, self.selected_unit_type, event.pos)
                        self.selected_unit_type = None # Quitte le mode placement après une tentative
                    # Sinon, on vérifie si on clique sur un bouton
                    else:
                        if self.knight_button.collidepoint(event.pos):
                            if self.player.elixir >= Knight.cost:
                                self.selected_unit_type = Knight
                        elif self.archer_button.collidepoint(event.pos):
                            if self.player.elixir >= Archer.cost:
                                self.selected_unit_type = Archer

            if not self.game_over:
                self.update()
                self.handle_ai_action()
            self.render()

        # Logique de fin de partie
        font = pygame.font.SysFont('comicsans', 80)
        text = font.render(f"{self.winner.name} WINS!", 1, WHITE)
        WIN.blit(text, (WIDTH/2 - text.get_width()/2, HEIGHT/2 - text.get_height()/2))
        pygame.display.update()
        pygame.time.wait(3000)

        pygame.quit()
        sys.exit()

# --- Démarrage du jeu ---
if __name__ == "__main__":
    game = Game()
    game.main_loop()
