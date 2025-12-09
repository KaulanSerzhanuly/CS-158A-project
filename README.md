# CS-158A-project

## Networked Multi-Game Platform

A networked gaming platform featuring Tic-Tac-Toe and Rock Paper Scissors games, implemented using Python sockets. The platform includes servers that manage multiple games and clients that connect to play.

## Files

### Core Game Files
- `server.py` — game server, pairs clients and runs games (supports lobby and multiple games)
- `client.py` — interactive client you can run in a terminal (supports lobby and multiple games)
- `auto_client.py` — automated client that plays random moves (useful for demo)
- `demo.py` — runs server and two automated clients and prints sample output

### Rock Paper Scissors Game (Separate Implementation)
- `rps_server.py` — Rock Paper Scissors server program
- `rps_client.py` — Rock Paper Scissors client program

### Launcher
- `game_launcher.py` — Menu launcher to choose and play either game

### Documentation
- `report.md` — project report with code and explanations

## Supported Games

- `tictactoe` — classic 3x3 Tic-Tac-Toe
- `rps` — Rock-Paper-Scissors (quick 2-player game)

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

#### Using the Unified Server (with Lobby)

**Starting the Server:**
```bash
python server.py
```
The server will start on `localhost:65432` by default and supports both tictactoe and rps games through a lobby system.

**Running Clients:**
Open multiple terminal windows and run:
```bash
python client.py
```

Or specify a different host/port:
```bash
python client.py --host <host> --port <port>
```

**Playing:**
1. Start the server first
2. Run at least two client instances
3. Clients will see available games and can choose to join `tictactoe` or `rps`
4. When two clients join the same game, it will automatically start
5. For Tic-Tac-Toe: Players take turns entering moves (0-8 or row col format)
6. For RPS: Players choose rock, paper, or scissors

**Demo Mode:**
```bash
python demo.py
```
This runs the server and two automated clients to show a sample game.

#### Rock Paper Scissors (Separate Server)

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
- Lobby system for game selection

### Rock Paper Scissors
- Multi-player support (2 players per game)
- Quick single-round gameplay (via unified server)
- Best of 3 rounds gameplay (via separate rps_server)
- Real-time score tracking
- Round-by-round results
- Multiple concurrent games
- Thread-safe server implementation

### General
- Both games use the same networking architecture
- Simple JSON-based message protocol
- Easy-to-use command-line interfaces
- No external dependencies (uses only Python standard library)
- Lobby system for game selection (unified server)
