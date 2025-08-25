# Fichier principal pour le jeu Clash Royale simplifié en mode texte.
# Créé par Jules.

import time
import os
import random
import threading
from queue import Queue

# --- File d'attente pour les commandes du joueur ---
input_queue = Queue()

def player_input_thread(q):
    """Thread qui écoute les entrées du joueur et les met dans la file."""
    while True:
        try:
            command = input()
            q.put(command)
            if command.lower() == 'q':
                break
        except (EOFError, KeyboardInterrupt):
            # Gère la fin de l'input ou l'interruption par l'utilisateur
            q.put('q')
            break

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
        self.hp = hp
        self.symbol = "T"

class Unit:
    """Classe de base pour toutes les unités (personnages)."""
    def __init__(self, owner, position, hp, damage, speed, range, symbol):
        self.owner = owner
        self.position = float(position)
        self.hp = hp
        self.damage = damage
        self.speed = speed
        self.range = range
        self.symbol = symbol
        self.cost = 0

    def attack(self, target):
        target.hp -= self.damage

class Knight(Unit):
    """Unité de mêlée avec des stats équilibrées."""
    def __init__(self, owner, position):
        symbol = "K" if owner.name == "Player" else "k"
        super().__init__(owner, position, hp=200, damage=50, speed=1, range=1, symbol=symbol)
        self.cost = 3

class Archer(Unit):
    """Unité à distance avec moins de vie mais une plus grande portée."""
    def __init__(self, owner, position):
        symbol = "A" if owner.name == "Player" else "a"
        super().__init__(owner, position, hp=100, damage=30, speed=1, range=5, symbol=symbol)
        self.cost = 3

# --- Classe principale du jeu ---

class Game:
    """Gère l'état et la logique du jeu."""
    def __init__(self, board_width=40):
        self.board_width = board_width
        self.player = Player("Player")
        self.ai = Player("AI")

        self.player_tower = Tower(self.player, 0)
        self.ai_tower = Tower(self.ai, self.board_width - 1)

        self.units = []
        self.game_over = False
        self.elixir_rate = 0.5  # Élixir par seconde
        self.last_update_time = time.time()

    def spawn_unit(self, player, unit_type):
        if player.elixir >= unit_type.cost:
            player.elixir -= unit_type.cost
            position = 1 if player == self.player else self.board_width - 2
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

    def handle_player_input(self):
        if not input_queue.empty():
            command = input_queue.get().lower()
            if command == 'k': self.spawn_unit(self.player, Knight)
            elif command == 'a': self.spawn_unit(self.player, Archer)
            elif command == 'q': self.game_over = True

    def handle_ai_action(self):
        if self.ai.elixir >= 3 and random.random() < 0.1:
            self.spawn_unit(self.ai, random.choice([Knight, Archer]))

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--- CLASH ROYALE TEXTE ---")
        player_info = f"JOUEUR: Tour HP: {max(0, int(self.player_tower.hp))}/1500 | Elixir: {int(self.player.elixir)}"
        ai_info = f"IA: Tour HP: {max(0, int(self.ai_tower.hp))}/1500 | Elixir: {int(self.ai.elixir)}"
        print(f"{player_info:<{self.board_width}} | {ai_info:>{self.board_width}}")

        board = ["-"] * self.board_width
        board[self.player_tower.position] = "T"
        board[self.ai_tower.position] = "T"
        for unit in self.units:
            pos = int(round(unit.position))
            if 0 <= pos < self.board_width: board[pos] = unit.symbol

        print("=" * (self.board_width * 2 + 3))
        print(f"[{''.join(board)}]")
        print("=" * (self.board_width * 2 + 3))
        print("Commandes: 'k' pour Chevalier (3), 'a' pour Archer (3), 'q' pour quitter.")

    def main_loop(self):
        input_thread = threading.Thread(target=player_input_thread, args=(input_queue,), daemon=True)
        input_thread.start()

        while not self.game_over:
            self.handle_player_input()
            self.handle_ai_action()
            self.update()
            self.render()
            time.sleep(0.1)

        # Affichage final
        self.render()
        print("\n--- FIN DE LA PARTIE ---")
        if self.player_tower.hp <= 0: print("Défaite... La tour du joueur a été détruite.")
        elif self.ai_tower.hp <= 0: print("Victoire ! Vous avez détruit la tour de l'IA !")
        else: print("Partie quittée.")

# --- Démarrage du jeu ---
if __name__ == "__main__":
    game = Game()
    game.main_loop()
