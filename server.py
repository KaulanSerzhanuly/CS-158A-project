#!/usr/bin/env python3
"""
Tic-Tac-Toe Server
Handles game logic and client connections for networked Tic-Tac-Toe games.
"""

import socket
import threading
import json
from enum import Enum

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

class TicTacToeGame:
    """Represents a single Tic-Tac-Toe game instance."""
    
    def __init__(self, game_id):
        self.game_id = game_id
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.players = []  # List of (socket, address, symbol) tuples
        self.current_turn = 0  # Index of player whose turn it is
        self.state = GameState.WAITING
        self.winner = None
        
    def add_player(self, client_socket, address):
        """Add a player to the game. Returns True if game is ready to start."""
        if len(self.players) < 2:
            symbol = 'X' if len(self.players) == 0 else 'O'
            self.players.append((client_socket, address, symbol))
            
            if len(self.players) == 2:
                self.state = GameState.PLAYING
                return True
        return False
    
    def make_move(self, row, col, player_symbol):
        """Attempt to make a move. Returns (success, message, game_over, winner)."""
        if self.state != GameState.PLAYING:
            return False, "Game is not in progress", False, None
            
        if self.players[self.current_turn][2] != player_symbol:
            return False, "Not your turn", False, None
            
        if row < 0 or row >= 3 or col < 0 or col >= 3:
            return False, "Invalid position", False, None
            
        if self.board[row][col] != ' ':
            return False, "Position already taken", False, None
            
        # Make the move
        self.board[row][col] = player_symbol
        
        # Check for win or draw
        winner = self.check_winner()
        if winner:
            self.state = GameState.FINISHED
            self.winner = winner
            return True, "Move successful", True, winner
        elif self.is_board_full():
            self.state = GameState.FINISHED
            return True, "Move successful", True, "DRAW"
        else:
            # Switch turn
            self.current_turn = 1 - self.current_turn
            return True, "Move successful", False, None
    
    def check_winner(self):
        """Check if there's a winner. Returns 'X', 'O', or None."""
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != ' ':
                return row[0]
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != ' ':
                return self.board[0][col]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return self.board[0][2]
        
        return None
    
    def is_board_full(self):
        """Check if the board is full."""
        return all(self.board[i][j] != ' ' for i in range(3) for j in range(3))
    
    def get_board_string(self):
        """Get a string representation of the board."""
        lines = []
        for i, row in enumerate(self.board):
            lines.append(" | ".join(row))
            if i < 2:
                lines.append("-" * 9)
        return "\n".join(lines)
    
    def get_status_message(self):
        """Get a status message for the current game state."""
        if self.state == GameState.WAITING:
            return "Waiting for another player..."
        elif self.state == GameState.FINISHED:
            if self.winner == "DRAW":
                return "Game ended in a DRAW!"
            else:
                return f"Game over! {self.winner} wins!"
        else:
            current_player = self.players[self.current_turn][2]
            return f"It's {current_player}'s turn"

class TicTacToeServer:
    """Main server class that handles client connections and game management."""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.games = {}  # game_id -> TicTacToeGame
        self.game_counter = 0
        self.lock = threading.Lock()
        
    def start(self):
        """Start the server and begin accepting connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"Tic-Tac-Toe Server started on {self.host}:{self.port}")
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
            game = TicTacToeGame(game_id)
            self.games[game_id] = game
            return game_id, game
    
    def handle_client(self, client_socket, address):
        """Handle communication with a single client."""
        try:
            game_id, game = self.find_or_create_game()
            
            # Add player to game
            is_ready = game.add_player(client_socket, address)
            player_symbol = game.players[-1][2]
            
            # Send initial game info
            self.send_message(client_socket, {
                "type": "game_joined",
                "game_id": game_id,
                "symbol": player_symbol,
                "board": game.board,
                "status": game.get_status_message()
            })
            
            if is_ready:
                # Notify both players that game is starting
                for player_socket, _, symbol in game.players:
                    self.send_message(player_socket, {
                        "type": "game_start",
                        "board": game.board,
                        "status": game.get_status_message(),
                        "your_turn": (symbol == game.players[game.current_turn][2])
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
                        
                        if message["type"] == "move":
                            row = message["row"]
                            col = message["col"]
                            
                            success, msg, game_over, winner = game.make_move(
                                row, col, player_symbol
                            )
                            
                            # Send response to the player who made the move
                            self.send_message(client_socket, {
                                "type": "move_response",
                                "success": success,
                                "message": msg,
                                "board": game.board,
                                "status": game.get_status_message()
                            })
                            
                            # If move was successful, notify both players
                            if success:
                                for player_socket, _, symbol in game.players:
                                    is_my_turn = (symbol == game.players[game.current_turn][2])
                                    self.send_message(player_socket, {
                                        "type": "board_update",
                                        "board": game.board,
                                        "status": game.get_status_message(),
                                        "your_turn": is_my_turn and not game_over,
                                        "game_over": game_over,
                                        "winner": winner
                                    })
                        
                        elif message["type"] == "get_status":
                            # Send current game status
                            is_my_turn = (player_symbol == game.players[game.current_turn][2])
                            self.send_message(client_socket, {
                                "type": "status_update",
                                "board": game.board,
                                "status": game.get_status_message(),
                                "your_turn": is_my_turn and game.state == GameState.PLAYING,
                                "game_over": game.state == GameState.FINISHED,
                                "winner": game.winner
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
    server = TicTacToeServer(host='localhost', port=8888)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if server.server_socket:
            server.server_socket.close()

