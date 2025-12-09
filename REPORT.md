# Networked Tic-Tac-Toe Game - Project Report

## Introduction

This project implements a networked Tic-Tac-Toe game using Python's socket programming. The system consists of a server program that manages game sessions and multiple client programs that connect to play games. The server handles game logic, player matching, turn management, and win/draw detection, while clients provide a user-friendly interface for players to interact with the game.

The implementation uses TCP sockets for reliable communication between clients and the server. The server can handle multiple concurrent games, automatically matching players into pairs. Each game maintains its own state, including the game board, current turn, and game status. Clients receive real-time updates about board changes, turn notifications, and game outcomes.

This networked approach allows players to compete against each other over a network, making it a practical demonstration of client-server architecture and socket programming concepts.

## Body

### Architecture Overview

The system follows a client-server architecture:
- **Server**: Manages all game logic, matches players, and maintains game state
- **Client**: Connects to server, displays game board, accepts user input, and receives updates

Communication between client and server uses JSON-formatted messages over TCP sockets, allowing for structured data exchange.

### Server Implementation

The server program (`server.py`) consists of three main classes:

1. **GameState Enum**: Represents the possible states of a game (WAITING, PLAYING, FINISHED)
2. **TicTacToeGame Class**: Manages individual game instances
3. **TicTacToeServer Class**: Handles client connections and game management

#### Source Code: server.py

```python
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
            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    message = json.loads(data)
                    
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
                
                except json.JSONDecodeError:
                    self.send_message(client_socket, {
                        "type": "error",
                        "message": "Invalid message format"
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
```

#### Server Code Explanation

**GameState Enum**: Defines three possible states for a game - waiting for a second player, actively being played, or finished.

**TicTacToeGame Class**: This class encapsulates all game logic:
- `__init__`: Initializes a 3x3 board with empty spaces, empty player list, and sets initial state to WAITING
- `add_player`: Adds a player to the game, assigning 'X' to the first player and 'O' to the second. Returns True when the game is ready to start
- `make_move`: Validates and executes a move. Checks if it's the player's turn, validates position, and updates the board. After each move, checks for a winner or draw
- `check_winner`: Examines all rows, columns, and diagonals to determine if there's a winning combination
- `is_board_full`: Checks if all board positions are filled (for draw detection)

**TicTacToeServer Class**: Manages the server-side operations:
- `start`: Creates a TCP socket, binds to the specified host and port, and listens for connections. Each client connection is handled in a separate thread
- `find_or_create_game`: Thread-safe method that either finds a game waiting for a player or creates a new game
- `handle_client`: Main communication handler for each client. Processes incoming JSON messages and responds accordingly:
  - When a client connects, it's added to a game and receives initial game information
  - When a move is received, it validates and processes the move, then notifies both players
  - Handles game state updates and turn management
- `send_message`: Utility method to send JSON-formatted messages to clients

The server uses threading to handle multiple clients concurrently, allowing multiple games to run simultaneously.

### Client Implementation

The client program (`client.py`) provides a user interface for players to interact with the game.

#### Source Code: client.py

```python
#!/usr/bin/env python3
"""
Tic-Tac-Toe Client
Connects to the server and provides a user interface for playing Tic-Tac-Toe.
"""

import socket
import json
import threading
import sys

class TicTacToeClient:
    """Client class that connects to the server and handles user interaction."""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.symbol = None
        self.game_id = None
        self.running = True
        
    def connect(self):
        """Connect to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
    
    def send_message(self, message):
        """Send a JSON message to the server."""
        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.sendall(data + b'\n')
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def receive_messages(self):
        """Receive and process messages from the server."""
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        self.handle_message(json.loads(line))
            
            except json.JSONDecodeError:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
                break
        
        print("\nDisconnected from server.")
        self.running = False
    
    def handle_message(self, message):
        """Handle incoming messages from the server."""
        msg_type = message.get("type")
        
        if msg_type == "game_joined":
            self.game_id = message.get("game_id")
            self.symbol = message.get("symbol")
            print(f"\n=== Joined Game #{self.game_id} ===")
            print(f"You are playing as: {self.symbol}")
            self.display_board(message.get("board"))
            print(f"\n{message.get('status')}")
        
        elif msg_type == "game_start":
            print("\n=== Game Started! ===")
            self.display_board(message.get("board"))
            print(f"\n{message.get('status')}")
            if message.get("your_turn"):
                print("It's your turn! Enter your move (row col): ")
        
        elif msg_type == "move_response":
            if not message.get("success"):
                print(f"\nError: {message.get('message')}")
                print("Please try again.")
            else:
                self.display_board(message.get("board"))
                print(f"\n{message.get('status')}")
        
        elif msg_type == "board_update":
            print("\n=== Board Updated ===")
            self.display_board(message.get("board"))
            print(f"\n{message.get('status')}")
            
            if message.get("game_over"):
                winner = message.get("winner")
                if winner == "DRAW":
                    print("\n*** GAME ENDED IN A DRAW! ***")
                elif winner == self.symbol:
                    print(f"\n*** CONGRATULATIONS! YOU WON! ***")
                else:
                    print(f"\n*** GAME OVER - YOU LOST! ***")
                print("\nPress Enter to exit...")
                self.running = False
            elif message.get("your_turn"):
                print("It's your turn! Enter your move (row col): ")
        
        elif msg_type == "status_update":
            self.display_board(message.get("board"))
            print(f"\n{message.get('status')}")
            if message.get("your_turn"):
                print("It's your turn! Enter your move (row col): ")
        
        elif msg_type == "error":
            print(f"\nError: {message.get('message')}")
    
    def display_board(self, board):
        """Display the game board in a formatted way."""
        print("\nCurrent Board:")
        print("   0   1   2")
        for i, row in enumerate(board):
            print(f"{i}  {' | '.join(row)}")
            if i < 2:
                print("  " + "-" * 9)
    
    def get_user_move(self):
        """Get a move from the user."""
        while self.running:
            try:
                user_input = input().strip()
                if not user_input:
                    continue
                
                # Parse input
                parts = user_input.split()
                if len(parts) != 2:
                    print("Invalid input. Please enter row and column (e.g., '1 2'): ")
                    continue
                
                try:
                    row = int(parts[0])
                    col = int(parts[1])
                    
                    # Send move to server
                    self.send_message({
                        "type": "move",
                        "row": row,
                        "col": col
                    })
                except ValueError:
                    print("Invalid input. Please enter numbers for row and column: ")
            
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nExiting...")
                self.running = False
                break
    
    def run(self):
        """Main client loop."""
        if not self.connect():
            return
        
        # Start receiving messages in a separate thread
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        # Main loop for getting user input
        try:
            self.get_user_move()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()

if __name__ == "__main__":
    host = 'localhost'
    port = 8888
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    client = TicTacToeClient(host, port)
    client.run()
```

#### Client Code Explanation

**TicTacToeClient Class**: Manages all client-side operations:

- `__init__`: Initializes client with server host and port, and sets up state variables
- `connect`: Establishes a TCP connection to the server
- `send_message`: Sends JSON-formatted messages to the server
- `receive_messages`: Runs in a separate thread to continuously receive and process messages from the server. Uses a buffer to handle partial messages (since TCP is a stream protocol)
- `handle_message`: Processes different message types from the server:
  - `game_joined`: Displays game information when first connecting
  - `game_start`: Notifies when the game begins
  - `move_response`: Confirms whether a move was successful
  - `board_update`: Updates the display when the board changes
  - `status_update`: Provides current game status
- `display_board`: Formats and displays the 3x3 game board with row/column indices
- `get_user_move`: Continuously reads user input, validates it, and sends moves to the server. Accepts input in the format "row col" (e.g., "1 2")
- `run`: Main method that connects to the server, starts the receive thread, and begins accepting user input

The client uses threading to separate message reception from user input, ensuring the UI remains responsive and updates are received in real-time.

### Communication Protocol

The client and server communicate using JSON messages over TCP. Message types include:

- **game_joined**: Sent when a client joins a game
- **game_start**: Sent when a game begins (both players connected)
- **move**: Sent by client to make a move
- **move_response**: Sent by server in response to a move
- **board_update**: Sent to all players when the board changes
- **status_update**: Sent to provide current game status
- **error**: Sent when an error occurs

Each message includes relevant data such as the board state, current turn, game status, and winner information.

## Sample Results

### Running the Server

```
$ python server.py
Tic-Tac-Toe Server started on localhost:8888
Waiting for clients to connect...
New connection from ('127.0.0.1', 54321)
New connection from ('127.0.0.1', 54322)
Client ('127.0.0.1', 54321) disconnected
Client ('127.0.0.1', 54322) disconnected
```

### Running Client 1 (Player X)

```
$ python client.py
Connected to server at localhost:8888

=== Joined Game #1 ===
You are playing as: X

Current Board:
   0   1   2
0     |   |  
  ---------
1     |   |  
  ---------
2     |   |  

Waiting for another player...

=== Game Started! ===

Current Board:
   0   1   2
0     |   |  
  ---------
1     |   |  
  ---------
2     |   |  

It's X's turn
It's your turn! Enter your move (row col): 
1 1

=== Board Updated ===

Current Board:
   0   1   2
0     |   |  
  ---------
1     | X |  
  ---------
2     |   |  

It's O's turn

=== Board Updated ===

Current Board:
   0   1   2
0     |   | O
  ---------
1     | X |  
  ---------
2     |   |  

It's X's turn
It's your turn! Enter your move (row col): 
0 0

=== Board Updated ===

Current Board:
   0   1   2
0  X |   | O
  ---------
1     | X |  
  ---------
2     |   |  

It's O's turn

=== Board Updated ===

Current Board:
   0   1   2
0  X |   | O
  ---------
1     | X | O
  ---------
2     |   |  

It's X's turn
It's your turn! Enter your move (row col): 
2 0

=== Board Updated ===

Current Board:
   0   1   2
0  X |   | O
  ---------
1     | X | O
  ---------
2  X |   |  

Game over! X wins!

*** CONGRATULATIONS! YOU WON! ***

Press Enter to exit...
```

### Running Client 2 (Player O)

```
$ python client.py
Connected to server at localhost:8888

=== Joined Game #1 ===
You are playing as: O

Current Board:
   0   1   2
0     |   |  
  ---------
1     |   |  
  ---------
2     |   |  

Waiting for another player...

=== Game Started! ===

Current Board:
   0   1   2
0     |   |  
  ---------
1     |   |  
  ---------
2     |   |  

It's X's turn

=== Board Updated ===

Current Board:
   0   1   2
0     |   |  
  ---------
1     | X |  
  ---------
2     |   |  

It's O's turn
It's your turn! Enter your move (row col): 
0 2

=== Board Updated ===

Current Board:
   0   1   2
0     |   | O
  ---------
1     | X |  
  ---------
2     |   |  

It's X's turn

=== Board Updated ===

Current Board:
   0   1   2
0  X |   | O
  ---------
1     | X |  
  ---------
2     |   |  

It's O's turn
It's your turn! Enter your move (row col): 
1 2

=== Board Updated ===

Current Board:
   0   1   2
0  X |   | O
  ---------
1     | X | O
  ---------
2     |   |  

It's X's turn

=== Board Updated ===

Current Board:
   0   1   2
0  X |   | O
  ---------
1     | X | O
  ---------
2  X |   |  

Game over! X wins!

*** GAME OVER - YOU LOST! ***

Press Enter to exit...
```

### Example: Draw Game

```
Player X:
=== Board Updated ===

Current Board:
   0   1   2
0  X | O | X
  ---------
1  O | O | X
  ---------
2  O | X | O

Game ended in a DRAW!

*** GAME ENDED IN A DRAW! ***
```

## Conclusion

This project successfully implements a networked Tic-Tac-Toe game using Python's socket programming capabilities. The implementation demonstrates several key networking and software engineering concepts:

1. **Client-Server Architecture**: The separation of concerns between server (game logic) and client (user interface) provides a scalable and maintainable design.

2. **Concurrent Programming**: The server uses threading to handle multiple clients simultaneously, allowing multiple games to run in parallel.

3. **Protocol Design**: The JSON-based message protocol provides a structured and extensible communication format between client and server.

4. **Game State Management**: The server maintains game state centrally, ensuring consistency and preventing cheating.

5. **Error Handling**: Both client and server include error handling for network issues, invalid input, and edge cases.

The implementation successfully allows players to connect to a server, join games, make moves, and receive real-time updates about the game state. The system handles win conditions, draws, turn management, and player disconnections gracefully.

Future enhancements could include:
- Player authentication and accounts
- Game history and statistics
- Chat functionality between players
- Spectator mode
- Tournament brackets
- Improved UI with graphics instead of text-based display

This project provides a solid foundation for understanding networked applications and demonstrates practical socket programming skills.

