#!/usr/bin/env python3
"""
Rock Paper Scissors Server
Handles game logic and client connections for networked Rock Paper Scissors games.
"""

import socket
import threading
import json
from enum import Enum
import random

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

class RPSGame:
    """Represents a single Rock Paper Scissors game instance."""
    
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = []  # List of (socket, address, name) tuples
        self.choices = {}  # player_index -> choice
        self.scores = [0, 0]  # Player scores
        self.round = 0
        self.state = GameState.WAITING
        self.max_rounds = 3  # Best of 3
        
    def add_player(self, client_socket, address, name="Player"):
        """Add a player to the game. Returns True if game is ready to start."""
        if len(self.players) < 2:
            self.players.append((client_socket, address, name))
            
            if len(self.players) == 2:
                self.state = GameState.PLAYING
                self.round = 1
                return True
        return False
    
    def make_choice(self, player_index, choice):
        """Record a player's choice. Returns True if both players have chosen."""
        if self.state != GameState.PLAYING:
            return False, "Game is not in progress"
        
        if player_index < 0 or player_index >= len(self.players):
            return False, "Invalid player"
        
        choice = choice.upper()
        if choice not in ['R', 'P', 'S']:
            return False, "Invalid choice. Use R (Rock), P (Paper), or S (Scissors)"
        
        self.choices[player_index] = choice
        
        if len(self.choices) == 2:
            # Both players have chosen, determine winner
            return True, "Choice recorded"
        return True, "Waiting for opponent..."
    
    def determine_round_winner(self):
        """Determine the winner of the current round. Returns (winner_index, result_string)."""
        p1_choice = self.choices.get(0)
        p2_choice = self.choices.get(1)
        
        if not p1_choice or not p2_choice:
            return None, "Waiting for choices..."
        
        choice_map = {'R': 'Rock', 'P': 'Paper', 'S': 'Scissors'}
        p1_name = choice_map[p1_choice]
        p2_name = choice_map[p2_choice]
        
        # Determine winner
        if p1_choice == p2_choice:
            return -1, f"Tie! Both chose {p1_name}"
        
        # Rock beats Scissors, Paper beats Rock, Scissors beats Paper
        winning_combos = {
            ('R', 'S'): 0,  # Rock beats Scissors
            ('P', 'R'): 0,  # Paper beats Rock
            ('S', 'P'): 0,  # Scissors beats Paper
            ('S', 'R'): 1,  # Rock beats Scissors (reversed)
            ('R', 'P'): 1,  # Paper beats Rock (reversed)
            ('P', 'S'): 1   # Scissors beats Paper (reversed)
        }
        
        winner = winning_combos.get((p1_choice, p2_choice))
        if winner == 0:
            self.scores[0] += 1
            return 0, f"{p1_name} beats {p2_name}! {self.players[0][2]} wins this round!"
        else:
            self.scores[1] += 1
            return 1, f"{p2_name} beats {p1_name}! {self.players[1][2]} wins this round!"
    
    def next_round(self):
        """Move to the next round. Returns True if game is over."""
        self.choices.clear()
        self.round += 1
        
        # Check if game is over (best of 3)
        if self.round > self.max_rounds or max(self.scores) >= 2:
            self.state = GameState.FINISHED
            return True
        return False
    
    def get_game_winner(self):
        """Get the overall game winner. Returns winner_index or -1 for tie."""
        if self.scores[0] > self.scores[1]:
            return 0
        elif self.scores[1] > self.scores[0]:
            return 1
        return -1  # Tie
    
    def get_status_message(self):
        """Get a status message for the current game state."""
        if self.state == GameState.WAITING:
            return "Waiting for another player..."
        elif self.state == GameState.FINISHED:
            winner_idx = self.get_game_winner()
            if winner_idx == -1:
                return f"Game Over! It's a tie! Final score: {self.scores[0]}-{self.scores[1]}"
            else:
                winner_name = self.players[winner_idx][2]
                return f"Game Over! {winner_name} wins! Final score: {self.scores[0]}-{self.scores[1]}"
        else:
            return f"Round {self.round} of {self.max_rounds} | Score: {self.players[0][2]} {self.scores[0]} - {self.scores[1]} {self.players[1][2]}"

class RPSServer:
    """Main server class that handles client connections and game management."""
    
    def __init__(self, host='localhost', port=8889):
        self.host = host
        self.port = port
        self.server_socket = None
        self.games = {}  # game_id -> RPSGame
        self.game_counter = 0
        self.lock = threading.Lock()
        
    def start(self):
        """Start the server and begin accepting connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"Rock Paper Scissors Server started on {self.host}:{self.port}")
        print("Waiting for clients to connect...")
        
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"New connection from {address}")
            
            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()
    
    def find_or_create_game(self):
        """Find a waiting game or create a new one."""
        with self.lock:
            # Look for a game waiting for a player
            for game_id, game in self.games.items():
                if game.state == GameState.WAITING:
                    return game_id, game
            
            # Create a new game
            self.game_counter += 1
            game_id = self.game_counter
            game = RPSGame(game_id)
            self.games[game_id] = game
            return game_id, game
    
    def handle_client(self, client_socket, address):
        """Handle communication with a single client."""
        try:
            game_id, game = self.find_or_create_game()
            
            # Get player name (optional)
            player_name = f"Player {len(game.players) + 1}"
            
            # Add player to game
            is_ready = game.add_player(client_socket, address, player_name)
            player_index = len(game.players) - 1
            
            # Send initial game info
            self.send_message(client_socket, {
                "type": "game_joined",
                "game_id": game_id,
                "player_index": player_index,
                "player_name": player_name,
                "status": game.get_status_message()
            })
            
            if is_ready:
                # Notify both players that game is starting
                for idx, (player_socket, _, _) in enumerate(game.players):
                    self.send_message(player_socket, {
                        "type": "game_start",
                        "status": game.get_status_message(),
                        "opponent": game.players[1-idx][2],
                        "your_turn": True
                    })
            
            # Handle game messages
            buffer = ""
            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if not line:
                            continue
                        
                        try:
                            message = json.loads(line)
                        except json.JSONDecodeError:
                            self.send_message(client_socket, {
                                "type": "error",
                                "message": "Invalid message format"
                            })
                            continue
                        
                        if message["type"] == "choice":
                            choice = message.get("choice", "").upper()
                            
                            success, msg = game.make_choice(player_index, choice)
                            
                            # Send response to the player who made the choice
                            self.send_message(client_socket, {
                                "type": "choice_response",
                                "success": success,
                                "message": msg,
                                "status": game.get_status_message()
                            })
                            
                            # If both players have chosen, determine winner
                            if len(game.choices) == 2:
                                winner_idx, result_msg = game.determine_round_winner()
                                
                                # Store choices before clearing
                                choices_copy = game.choices.copy()
                                
                                game_over = game.next_round()
                                
                                choice_map = {'R': 'Rock', 'P': 'Paper', 'S': 'Scissors'}
                                
                                # Notify both players of round result
                                for idx, (player_socket, _, _) in enumerate(game.players):
                                    is_winner = (winner_idx == idx)
                                    is_tie = (winner_idx == -1)
                                    
                                    self.send_message(player_socket, {
                                        "type": "round_result",
                                        "result": result_msg,
                                        "your_choice": choice_map.get(choices_copy.get(idx, ''), ''),
                                        "opponent_choice": choice_map.get(choices_copy.get(1-idx, ''), ''),
                                        "scores": game.scores.copy(),
                                        "round": game.round,
                                        "you_won_round": is_winner,
                                        "round_tie": is_tie,
                                        "status": game.get_status_message(),
                                        "game_over": game_over,
                                        "your_turn": not game_over
                                    })
                                
                                if game_over:
                                    # Game finished
                                    final_winner = game.get_game_winner()
                                    for idx, (player_socket, _, _) in enumerate(game.players):
                                        you_won = (final_winner == idx)
                                        is_tie = (final_winner == -1)
                                        
                                        self.send_message(player_socket, {
                                            "type": "game_over",
                                            "status": game.get_status_message(),
                                            "you_won": you_won,
                                            "is_tie": is_tie,
                                            "final_scores": game.scores.copy()
                                        })
                            elif success:
                                # Waiting for opponent
                                for idx, (player_socket, _, _) in enumerate(game.players):
                                    if idx != player_index:
                                        self.send_message(player_socket, {
                                            "type": "opponent_chose",
                                            "status": game.get_status_message(),
                                            "your_turn": True
                                        })
                        
                        elif message["type"] == "get_status":
                            # Send current game status
                            self.send_message(client_socket, {
                                "type": "status_update",
                                "status": game.get_status_message(),
                                "scores": game.scores.copy(),
                                "round": game.round,
                                "game_over": game.state == GameState.FINISHED
                            })
                
                except Exception as e:
                    print(f"Error handling message: {e}")
                    break
        
        except Exception as e:
            print(f"Error with client {address}: {e}")
        finally:
            # Clean up
            client_socket.close()
            print(f"Client {address} disconnected")
    
    def send_message(self, client_socket, message):
        """Send a JSON message to a client."""
        try:
            data = json.dumps(message).encode('utf-8')
            client_socket.sendall(data + b'\n')
        except Exception as e:
            print(f"Error sending message: {e}")

if __name__ == "__main__":
    server = RPSServer(host='localhost', port=8889)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if server.server_socket:
            server.server_socket.close()
