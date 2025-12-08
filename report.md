# Networked Tic-Tac-Toe Project Report

## Introduction

This project implements a simple networked Tic-Tac-Toe game consisting of a central server that manages games and clients that connect to play. The server pairs connected clients into games, enforces game rules, and relays board updates. Clients can be interactive (human input) or automated for demonstrations.

## Body

### Source Code

Below are the source files used in the project. Each file is followed by an explanation of its purpose and key parts.

---

**`server.py`**

```python
[see file server.py in project root]
```

Explanation:
- The server listens on TCP port 65432 and accepts connections.
- Connected clients are placed in a waiting list; when two clients are available they are paired into a `Game` thread.
- `Game` manages the 3x3 board (represented as a list of length 9), sends `start` messages to both clients, and runs the move loop:
  - It prompts the current player with a `your_turn` message.
  - It receives a `move` message with a `pos` (0-8), validates it and updates the board.
  - After each move it checks for a win or draw and broadcasts `update` messages to both players.
  - At the end it sends `game_over` with `result` set to `win`/`loss`/`draw`.

- The server also exposes a small lobby protocol: upon connecting a client can request the available games by sending `{ "type": "list" }`, or join a specific game with `{ "type": "join", "game": "rps" }`.
- A new simple game `RPS` (Rock-Paper-Scissors) is implemented as `RPSGame`. Each player sends a `{ "type": "choice", "move": "rock" }` and the server computes the winner and sends a `game_over` message showing each player's choice and the result.

Key server snippets (illustrative):

```python
# waiting lists keyed by game name
self.waiting = { 'tictactoe': [], 'rps': [] }

# when two clients join the same game we create the appropriate game thread
if game_name == 'tictactoe':
  game = Game(p1_conn, p2_conn)
elif game_name == 'rps':
  game = RPSGame(p1_conn, p2_conn)
```

RPS judge (simplified):

```python
def judge(self, a, b):
  mapping = {'rock':0, 'paper':1, 'scissors':2}
  va, vb = mapping[a], mapping[b]
  if va == vb: return 'draw','draw'
  if (va - vb) % 3 == 1: return 'win','loss'
  return 'loss','win'
```

---

**`client.py`**

```python
[see file client.py in project root]
```

Explanation:
- `client.py` connects to the server and listens for JSON messages (newline-delimited).
- When it receives `your_turn` it prints the board and prompts the user to enter a move 0–8.
- It sends moves as JSON objects: `{ "type": "move", "pos": 4 }`.
- It prints updates and the final game result.

Client UI improvements and snippets:

```python
def prompt_move(board, you):
  # accepts single index like '4' or row/col like '1 2' or '1,2'
  raw = input(f"Your move ({you}) — enter 0-8, or q to quit: ")
  # validation: range, occupancy, and helpful error messages
```

The client also implements a small lobby flow: it requests the server's available games (`{type:'list'}`) and sends `{type:'join', game:'rps'}` to join RPS. For RPS the client prompts for `rock/paper/scissors` and sends `{type:'choice', move:...}`.

---

**`auto_client.py`**

```python
[see file auto_client.py in project root]
```

Explanation:
- `auto_client.py` acts like `client.py` but chooses random valid moves automatically. This is useful for automated demos or testing without human interaction.

---

**`demo.py`**

```python
[see file demo.py in project root]
```

Explanation:
- `demo.py` starts the server in a subprocess and launches two `auto_client.py` subprocesses. It captures their output and prints server and client logs. This provides a reproducible sample run.

### Protocol Summary

- Messages are JSON objects terminated by a newline.
- Client -> Server: `{ "type": "move", "pos": N }`
- Server -> Client examples:
  - `{ "type": "start", "you": "X", "board": [...] }`
  - `{ "type": "your_turn", "board": [...] }`
  - `{ "type": "update", "board": [...], "next": "O" }`
  - `{ "type": "game_over", "result": "win"|"loss"|"draw", "board": [...] }`

## Sample Results

Run `python3 demo.py` to produce a sample game with two automated players. The demo prints server logs and both clients' outputs.

Sample run (captured from `python3 demo.py`):

--- SERVER ---

--- CLIENT 1 ---
Start. You are X
 0 | 1 | 2 
---+---+---
 3 | 4 | 5 
---+---+---
 6 | 7 | 8 
Playing move 4
Update. Next: O
Update. Next: X
Playing move 2
Update. Next: O
Update. Next: X
Playing move 7
Update. Next: O
Update. Next: X
Playing move 1
Game over: win
 O | X | X 
---+---+---
 3 | X | 5 
---+---+---
 O | X | O 

--- CLIENT 2 ---
Start. You are O
 0 | 1 | 2 
---+---+---
 3 | 4 | 5 
---+---+---
 6 | 7 | 8 
Update. Next: O
Playing move 8
Update. Next: X
Update. Next: O
Playing move 6
Update. Next: X
Update. Next: O
Playing move 0
Update. Next: X
Game over: loss
 O | X | X 
---+---+---
 3 | X | 5 
---+---+---
 O | X | O 

### RPS sample run

I also tested the Rock-Paper-Scissors game with two small test clients. Sample responses received by the two clients were:

- Client 1 (sent `rock`):

  {"type": "game_over", "result": "loss", "choice": "rock", "opponent": "paper"}

- Client 2 (sent `paper`):

  {"type": "game_over", "result": "win", "choice": "paper", "opponent": "rock"}


## Conclusion

This project demonstrates a simple but functional client-server architecture for a turn-based multiplayer game. The server cleanly separates pairing and per-game logic, and the clients follow a small, easy-to-parse JSON protocol. The code is intentionally minimal and easy to extend (e.g., add persistence, lobby, or a GUI client).
