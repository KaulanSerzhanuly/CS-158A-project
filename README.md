# Networked Tic-Tac-Toe

This project implements a simple networked Tic-Tac-Toe game with a central server that pairs clients into games.

Files:
- `server.py` — game server, pairs clients and runs games
- `client.py` — interactive client you can run in a terminal
- `auto_client.py` — automated client that plays random moves (useful for demo)
- `client.py` — interactive client you can run in a terminal (now supports lobby and multiple games)
- `auto_client.py` — automated client that plays random moves (useful for demo)
- `demo.py` — runs server and two automated clients and prints sample output
- `report.md` — project report with code and explanations

Supported games:
- `tictactoe` — classic 3x3 Tic-Tac-Toe
- `rps` — Rock-Paper-Scissors (quick 2-player game)

Quick start (run in project root):

```bash
python3 server.py           # start server
python3 client.py           # start a client (run twice in separate terminals)

# or run demo which shows a sample game using two automated clients:
python3 demo.py
```
# CS-158A-project