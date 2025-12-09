#!/usr/bin/env python3
"""
Game Launcher
Menu to choose between Tic-Tac-Toe and Rock Paper Scissors games.
"""

import subprocess
import sys
import time

def print_menu():
    """Print the game selection menu."""
    print("\n" + "="*50)
    print("  GAME LAUNCHER")
    print("="*50)
    print("\nChoose a game to play:")
    print("  1. Tic-Tac-Toe")
    print("  2. Rock Paper Scissors")
    print("  3. Exit")
    print("\n" + "="*50)

def start_server(server_script, port, use_flags=False):
    """Start a game server in the background.
    
    Args:
        server_script: Path to the server script
        port: Port number to start the server on
        use_flags: If True, use --port flag (for server.py).
                   If False, use positional argument (for rps_server.py).
    """
    try:
        # Start server process
        if sys.platform == 'win32':
            # Windows
            if use_flags:
                process = subprocess.Popen(
                    [sys.executable, server_script, '--port', str(port)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                process = subprocess.Popen(
                    [sys.executable, server_script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
        else:
            # Unix/Linux/Mac
            if use_flags:
                process = subprocess.Popen(
                    [sys.executable, server_script, '--port', str(port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                process = subprocess.Popen(
                    [sys.executable, server_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
        
        # Give server time to start
        time.sleep(1)
        return process
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

def start_client(client_script, host='localhost', port=None, use_flags=False):
    """Start a game client in a separate terminal/process.
    
    Args:
        client_script: Path to the client script
        host: Host address to connect to
        port: Port number to connect to
        use_flags: If True, use --host and --port flags (for client.py).
                   If False, use positional arguments (for rps_client.py).
    """
    try:
        if sys.platform == 'win32':
            # Windows - start in new console window
            if port:
                if use_flags:
                    subprocess.Popen(
                        [sys.executable, client_script, '--host', host, '--port', str(port)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    subprocess.Popen(
                        [sys.executable, client_script, host, str(port)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
            else:
                if use_flags:
                    subprocess.Popen(
                        [sys.executable, client_script, '--host', host],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    subprocess.Popen(
                        [sys.executable, client_script, host],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
        else:
            # Unix/Linux/Mac - can't easily create new terminal window
            # Return False to indicate we should just show instructions
            return False
    except Exception as e:
        print(f"Error starting client: {e}")
        return False

def main():
    """Main launcher function."""
    server_process = None
    
    try:
        while True:
            print_menu()
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                # Tic-Tac-Toe
                print("\nStarting Tic-Tac-Toe game...")
                print("Note: You'll need to open another terminal/console to run a second client.")
                
                # Start server
                server_process = start_server('server.py', 8888, use_flags=True)
                if server_process:
                    print("✓ Tic-Tac-Toe server started on port 8888")
                    print("\nTo start clients, open separate terminals and run:")
                    print(f"  python3 client.py --host localhost --port 8888")
                    print("\nServer is running in the background. Press Enter to return to menu...")
                    input()
                else:
                    print("Failed to start server. Make sure port 8888 is available.")
            
            elif choice == '2':
                # Rock Paper Scissors
                print("\nStarting Rock Paper Scissors game...")
                print("Note: You'll need to open another terminal/console to run a second client.")
                
                # Start server
                server_process = start_server('rps_server.py', 8889)
                if server_process:
                    print("✓ Rock Paper Scissors server started on port 8889")
                    print("\nTo start clients, open separate terminals and run:")
                    print(f"  python3 rps_client.py localhost 8889")
                    print("\nServer is running in the background. Press Enter to return to menu...")
                    input()
                else:
                    print("Failed to start server. Make sure port 8889 is available.")
            
            elif choice == '3':
                print("\nExiting...")
                break
            
            else:
                print("\nInvalid choice. Please enter 1, 2, or 3.")
            
            # Clean up server process if it exists
            if server_process:
                try:
                    server_process.terminate()
                    server_process.wait(timeout=2)
                except:
                    try:
                        server_process.kill()
                    except:
                        pass
                server_process = None
            
            print("\n")
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        # Clean up server process
        if server_process:
            try:
                server_process.terminate()
                server_process.wait(timeout=2)
            except:
                try:
                    server_process.kill()
                except:
                    pass

if __name__ == "__main__":
    main()
