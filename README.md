# CS-158A-project

## Networked Multi-Game Platform

A networked gaming platform featuring Tic-Tac-Toe and Rock Paper Scissors games, implemented using Python sockets. The platform includes servers that manage multiple games and clients that connect to play.

## Files

### Tic-Tac-Toe Game
- `server.py` - Tic-Tac-Toe server program that handles game logic and client connections
- `client.py` - Tic-Tac-Toe client program that connects to the server and provides user interface

### Rock Paper Scissors Game
- `rps_server.py` - Rock Paper Scissors server program
- `rps_client.py` - Rock Paper Scissors client program

### Launcher
- `game_launcher.py` - Menu launcher to choose and play either game

### Documentation
- `REPORT.md` - Complete project report with code explanations and sample results

## How to Run

### Quick Start (Recommended)

Use the game launcher to easily start either game:

```bash
python game_launcher.py
```

The launcher will:
1. Show a menu to choose between Tic-Tac-Toe and Rock Paper Scissors
2. Start the appropriate server automatically
3. Launch a client for you to play

**Note:** You'll need to open a second terminal/console window to run another client instance to play against.

### Manual Start

#### Tic-Tac-Toe

**Starting the Server:**
```bash
python server.py
```
The server will start on `localhost:8888` by default.

**Running Clients:**
Open multiple terminal windows and run:
```bash
python client.py
```

Or specify a different host/port:
```bash
python client.py <host> <port>
```

**Playing:**
1. Start the server first
2. Run at least two client instances
3. When two clients are connected, the game will automatically start
4. Players take turns entering moves in the format: `row col` (e.g., `1 2`)
5. The game will display the board, current turn, and game outcome

#### Rock Paper Scissors

**Starting the Server:**
```bash
python rps_server.py
```
The server will start on `localhost:8889` by default.

**Running Clients:**
Open multiple terminal windows and run:
```bash
python rps_client.py
```

Or specify a different host/port:
```bash
python rps_client.py <host> <port>
```

**Playing:**
1. Start the server first
2. Run at least two client instances
3. When two clients are connected, the game will automatically start
4. Players take turns choosing: `R` (Rock), `P` (Paper), or `S` (Scissors)
5. The game is best of 3 rounds - first to 2 wins!
6. The game will display round results, scores, and final winner

## Requirements

- Python 3.x
- No external dependencies (uses only standard library)

## Features

### Tic-Tac-Toe
- Multi-player support (2 players per game)
- Real-time board updates
- Win/draw detection
- Turn management
- Multiple concurrent games
- Thread-safe server implementation

### Rock Paper Scissors
- Multi-player support (2 players per game)
- Best of 3 rounds gameplay
- Real-time score tracking
- Round-by-round results
- Multiple concurrent games
- Thread-safe server implementation

### General
- Both games use the same networking architecture
- Simple JSON-based message protocol
- Easy-to-use command-line interfaces
- No external dependencies (uses only Python standard library)