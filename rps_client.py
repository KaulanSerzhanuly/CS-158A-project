#!/usr/bin/env python3
"""
Rock Paper Scissors Client
Connects to the server and provides a user interface for playing Rock Paper Scissors.
"""

import socket
import json
import threading
import sys

class RPSClient:
    """Client class that connects to the server and handles user interaction."""
    
    def __init__(self, host='localhost', port=8889):
        self.host = host
        self.port = port
        self.socket = None
        self.player_index = None
        self.player_name = None
        self.running = True
        self.waiting_for_choice = False
        
    def connect(self):
        """Connect to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to Rock Paper Scissors server at {self.host}:{self.port}")
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
            self.player_index = message.get("player_index")
            self.player_name = message.get("player_name")
            print(f"\n=== Joined Game #{message.get('game_id')} ===")
            print(f"You are: {self.player_name}")
            print(f"{message.get('status')}")
        
        elif msg_type == "game_start":
            print("\n=== Game Started! ===")
            print(f"Opponent: {message.get('opponent')}")
            print(f"{message.get('status')}")
            if message.get("your_turn"):
                self.waiting_for_choice = True
                print("\nMake your choice: R (Rock), P (Paper), or S (Scissors)")
                print("Your choice (R/P/S): ", end='', flush=True)
        
        elif msg_type == "choice_response":
            if not message.get("success"):
                print(f"\nError: {message.get('message')}")
                print("Please try again: R (Rock), P (Paper), or S (Scissors)")
                self.waiting_for_choice = True
                print("Your choice (R/P/S): ", end='', flush=True)
            else:
                print(f"\n{message.get('message')}")
                if "Waiting" in message.get('message', ''):
                    print("Waiting for your opponent to choose...")
                    self.waiting_for_choice = False
        
        elif msg_type == "opponent_chose":
            print(f"\n{message.get('status')}")
            if message.get("your_turn"):
                self.waiting_for_choice = True
                print("Make your choice: R (Rock), P (Paper), or S (Scissors)")
                print("Your choice (R/P/S): ", end='', flush=True)
        
        elif msg_type == "round_result":
            print("\n" + "="*50)
            print("ROUND RESULT")
            print("="*50)
            print(f"Your choice: {message.get('your_choice')}")
            print(f"Opponent's choice: {message.get('opponent_choice')}")
            print(f"\n{message.get('result')}")
            print(f"\n{message.get('status')}")
            
            if not message.get("game_over"):
                if message.get("your_turn"):
                    self.waiting_for_choice = True
                    print("\nMake your choice for the next round: R (Rock), P (Paper), or S (Scissors)")
                    print("Your choice (R/P/S): ", end='', flush=True)
        
        elif msg_type == "game_over":
            print("\n" + "="*50)
            print("GAME OVER")
            print("="*50)
            print(f"{message.get('status')}")
            
            if message.get("you_won"):
                print("\n*** CONGRATULATIONS! YOU WON! ***")
            elif message.get("is_tie"):
                print("\n*** GAME ENDED IN A TIE! ***")
            else:
                print("\n*** GAME OVER - YOU LOST! ***")
            
            print("\nPress Enter to exit...")
            self.running = False
        
        elif msg_type == "status_update":
            print(f"\n{message.get('status')}")
        
        elif msg_type == "error":
            print(f"\nError: {message.get('message')}")
    
    def get_user_choice(self):
        """Get a choice from the user."""
        while self.running:
            try:
                if not self.waiting_for_choice:
                    import time
                    time.sleep(0.1)
                    continue
                
                user_input = input("Your choice (R/P/S): ").strip().upper()
                if not user_input:
                    continue
                
                if user_input in ['R', 'P', 'S']:
                    self.waiting_for_choice = False
                    self.send_message({
                        "type": "choice",
                        "choice": user_input
                    })
                else:
                    print("Invalid choice. Please enter R (Rock), P (Paper), or S (Scissors)")
            
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
            self.get_user_choice()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()

if __name__ == "__main__":
    host = 'localhost'
    port = 8889
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    client = RPSClient(host, port)
    client.run()
