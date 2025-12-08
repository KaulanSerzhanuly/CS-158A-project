#!/usr/bin/env python3
"""
Tic-Tac-Toe game server.

Protocol: newline-delimited JSON. Messages are dicts with a `type` field.
Clients send: {"type": "move", "pos": 4}

Server messages include: start, your_turn, update, invalid, game_over
"""
import socket
import threading
import json
import time

HOST = '127.0.0.1'
PORT = 65432


def send_json(sock, obj):
    data = json.dumps(obj) + "\n"
    try:
        sock.sendall(data.encode())
    except Exception:
        pass


def recv_json(rfile):
    try:
        line = rfile.readline()
        if not line:
            return None
        return json.loads(line.strip())
    except Exception:
        return None


class Game(threading.Thread):
    def __init__(self, p1_sock, p2_sock):
        super().__init__(daemon=True)
        self.p1 = p1_sock
        self.p2 = p2_sock
        self.board = [" "] * 9
        self.lock = threading.Lock()
        self.current = 'X'

    def run(self):
        # Prepare file-like readers
        try:
            r1 = self.p1.makefile('r')
            r2 = self.p2.makefile('r')
        except Exception:
            return

        players = { 'X': (self.p1, r1), 'O': (self.p2, r2) }

        # Send start messages
        send_json(self.p1, { 'type': 'start', 'you': 'X', 'board': self.board })
        send_json(self.p2, { 'type': 'start', 'you': 'O', 'board': self.board })

        game_over = False
        winner = None

        while not game_over:
            cur_sock, cur_rfile = players[self.current]
            other = 'O' if self.current == 'X' else 'X'
            other_sock, _ = players[other]

            send_json(cur_sock, { 'type': 'your_turn', 'board': self.board })
            send_json(other_sock, { 'type': 'wait', 'board': self.board })

            msg = recv_json(cur_rfile)
            if msg is None:
                # disconnected
                winner = other
                game_over = True
                break

            if msg.get('type') != 'move':
                send_json(cur_sock, { 'type': 'invalid', 'reason': 'expected move' })
                continue

            pos = msg.get('pos')
            if not isinstance(pos, int) or pos < 0 or pos > 8:
                send_json(cur_sock, { 'type': 'invalid', 'reason': 'bad position' })
                continue

            with self.lock:
                if self.board[pos] != " ":
                    send_json(cur_sock, { 'type': 'invalid', 'reason': 'cell occupied' })
                    continue
                self.board[pos] = self.current

            # Check win/draw
            if self.check_win(self.current):
                game_over = True
                winner = self.current
            elif all(c != " " for c in self.board):
                game_over = True
                winner = None
            else:
                self.current = other

            # Broadcast update (only if game continues). Avoid sending an "update" when
            # the game has just finished because the `next` field would be confusing
            # (it would still reference the current player). Clients will instead
            # receive the final `game_over` message below.
            if not game_over:
                send_json(self.p1, { 'type': 'update', 'board': self.board, 'next': self.current })
                send_json(self.p2, { 'type': 'update', 'board': self.board, 'next': self.current })

        # game finished
        if winner is None:
            res1 = res2 = 'draw'
        else:
            res1 = 'win' if winner == 'X' else 'loss'
            res2 = 'win' if winner == 'O' else 'loss'

        send_json(self.p1, { 'type': 'game_over', 'result': res1, 'board': self.board })
        send_json(self.p2, { 'type': 'game_over', 'result': res2, 'board': self.board })

        try:
            self.p1.close()
        except Exception:
            pass
        try:
            self.p2.close()
        except Exception:
            pass

    def check_win(self, mark):
        b = self.board
        lines = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for i,j,k in lines:
            if b[i] == b[j] == b[k] == mark:
                return True
        return False


class GameServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        # waiting lists keyed by game name
        self.waiting = {
            'tictactoe': [],
            'rps': []
        }
        self.lock = threading.Lock()

        # supported games
        self.games = list(self.waiting.keys())

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"Server listening on {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                print('Client connected from', addr)
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        # read initial messages to allow 'list' and 'join <game>' actions
        try:
            rfile = conn.makefile('r')
        except Exception:
            conn.close(); return

        while True:
            msg = recv_json(rfile)
            if msg is None:
                try:
                    conn.close()
                except Exception:
                    pass
                return

            mtype = msg.get('type')
            if mtype == 'list':
                send_json(conn, { 'type': 'list', 'games': self.games })
                # keep waiting for a join message
                continue
            if mtype == 'join':
                game_name = msg.get('game', 'tictactoe')
                if game_name not in self.waiting:
                    send_json(conn, { 'type': 'invalid', 'reason': 'unknown game' })
                    continue
                with self.lock:
                    self.waiting[game_name].append((conn, rfile))
                    if len(self.waiting[game_name]) >= 2:
                        p1_conn, p1_r = self.waiting[game_name].pop(0)
                        p2_conn, p2_r = self.waiting[game_name].pop(0)
                        if game_name == 'tictactoe':
                            game = Game(p1_conn, p2_conn)
                        elif game_name == 'rps':
                            game = RPSGame(p1_conn, p2_conn)
                        else:
                            # fallback
                            game = Game(p1_conn, p2_conn)
                        game.start()
                return
            # If client sent nothing recognizable, treat as joining tic-tac-toe
            else:
                # enqueue for default game
                with self.lock:
                    self.waiting['tictactoe'].append((conn, rfile))
                    if len(self.waiting['tictactoe']) >= 2:
                        p1_conn, p1_r = self.waiting['tictactoe'].pop(0)
                        p2_conn, p2_r = self.waiting['tictactoe'].pop(0)
                        game = Game(p1_conn, p2_conn)
                        game.start()
                return


class RPSGame(threading.Thread):
    """Simple Rock-Paper-Scissors between two players.
    Protocol: each client sends {type: 'choice', 'move': 'rock'|'paper'|'scissors'}
    Server waits until both choices arrive, then sends game_over with results.
    """
    def __init__(self, p1_sock, p2_sock):
        super().__init__(daemon=True)
        self.p1 = p1_sock
        self.p2 = p2_sock

    def run(self):
        try:
            r1 = self.p1.makefile('r')
            r2 = self.p2.makefile('r')
        except Exception:
            return

        send_json(self.p1, { 'type': 'start', 'game': 'rps', 'you': 'P1' })
        send_json(self.p2, { 'type': 'start', 'game': 'rps', 'you': 'P2' })

        choice = { 'p1': None, 'p2': None }

        # Read from both until we have both choices
        while choice['p1'] is None or choice['p2'] is None:
            if choice['p1'] is None:
                msg = recv_json(r1)
                if msg and msg.get('type') == 'choice':
                    choice['p1'] = msg.get('move')
            if choice['p2'] is None:
                msg = recv_json(r2)
                if msg and msg.get('type') == 'choice':
                    choice['p2'] = msg.get('move')

        # determine winner
        res1, res2 = self.judge(choice['p1'], choice['p2'])

        send_json(self.p1, { 'type': 'game_over', 'result': res1, 'choice': choice['p1'], 'opponent': choice['p2'] })
        send_json(self.p2, { 'type': 'game_over', 'result': res2, 'choice': choice['p2'], 'opponent': choice['p1'] })

        try:
            self.p1.close()
        except Exception:
            pass
        try:
            self.p2.close()
        except Exception:
            pass

    def judge(self, a, b):
        # normalize
        a = (a or '').lower()
        b = (b or '').lower()
        mapping = {'rock':0, 'paper':1, 'scissors':2, 'r':0, 'p':1, 's':2}
        if a not in mapping or b not in mapping:
            return 'invalid', 'invalid'
        va = mapping[a]
        vb = mapping[b]
        if va == vb:
            return 'draw', 'draw'
        # rock(0) beats scissors(2); paper(1) beats rock(0); scissors(2) beats paper(1)
        if (va - vb) % 3 == 1:
            return 'win', 'loss'
        return 'loss', 'win'


if __name__ == '__main__':
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print('Server shutting down')
