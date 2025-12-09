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

