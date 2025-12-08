#!/usr/bin/env python3
"""
Simple interactive Tic-Tac-Toe client.
Connects to the server, receives updates and sends moves typed by the user.
"""
import socket
import json
import argparse

HOST = '127.0.0.1'
PORT = 65432


def send_json(sock, obj):
    sock.sendall((json.dumps(obj) + "\n").encode())


def print_board(board):
    # prettier board rendering with clear separators and indices for empty cells
    def c(i):
        return board[i] if board[i] != ' ' else str(i)
    sep = '\n' + '───┼───┼───' + '\n'
    row0 = f" {c(0)} │ {c(1)} │ {c(2)} "
    row1 = f" {c(3)} │ {c(4)} │ {c(5)} "
    row2 = f" {c(6)} │ {c(7)} │ {c(8)} "
    print(row0 + sep + row1 + sep + row2)


def prompt_move(board, you):
    """Prompt the user for a move with validation. Returns int 0-8 or None to quit."""
    while True:
        try:
            raw = input(f"Your move ({you}) — enter 0-8, or q to quit: ").strip()
        except EOFError:
            # treat EOF (piped input exhausted) as a quit
            print('\nInput closed — quitting.')
            return None
        if raw.lower() in ('q', 'quit', 'exit'):
            return None
        # allow row,col like 0,2 or '1 2'
        if ',' in raw:
            parts = [p.strip() for p in raw.split(',') if p.strip()]
        else:
            parts = raw.split()
        try:
            if len(parts) == 1:
                pos = int(parts[0])
            elif len(parts) == 2:
                r = int(parts[0]); c = int(parts[1])
                if 0 <= r <= 2 and 0 <= c <= 2:
                    pos = r*3 + c
                else:
                    print('Row/col out of range (use 0-2).')
                    continue
            else:
                print('Invalid input format.')
                continue
        except ValueError:
            print('Please enter numbers like "4" or "1 2".')
            continue

        if pos < 0 or pos > 8:
            print('Position out of range (0-8).')
            continue
        if board[pos] != ' ':
            print('Cell occupied — choose another.')
            continue
        return pos


def run(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        rfile = s.makefile('r')
        print('Connected to server')
        you = None

        # Lobby: ask server for available games
        send_json(s, { 'type': 'list' })
        # read until we get a 'list' response
        games = None
        while True:
            line = rfile.readline()
            if not line:
                print('Server closed connection')
                return
            msg = json.loads(line)
            if msg.get('type') == 'list':
                games = msg.get('games', [])
                break
        print('\nAvailable games:')
        for g in games:
            print(' -', g)
        # choose game
        choice = input('Enter game to join (default: tictactoe): ').strip() or 'tictactoe'
        if choice not in games:
            print('Unknown game, defaulting to tictactoe')
            choice = 'tictactoe'
        send_json(s, { 'type': 'join', 'game': choice })
        while True:
            line = rfile.readline()
            if not line:
                print('Server closed connection')
                break
            msg = json.loads(line)
            t = msg.get('type')
            if t == 'start':
                # server indicates which game we're in
                g = msg.get('game', 'tictactoe')
                if g == 'rps':
                    you = msg.get('you')
                    print('\nRock-Paper-Scissors game started. You are', you)
                    print('Choose: rock, paper, scissors (or r/p/s)')
                    # prompt and send choice
                    while True:
                        ch = input('Your choice: ').strip().lower()
                        if ch in ('rock','paper','scissors','r','p','s'):
                            send_json(s, { 'type': 'choice', 'move': ch })
                            break
                        print('Invalid choice; try rock/paper/scissors')
                    continue
                else:
                    you = msg.get('you')
                    print('Game started. You are', you)
                    print_board(msg.get('board', [' ']*9))
            elif t == 'your_turn':
                board = msg.get('board')
                print('\nYour turn')
                print_board(board)
                posi = prompt_move(board, you)
                if posi is None:
                    print('Quitting game.')
                    break
                send_json(s, { 'type': 'move', 'pos': posi })
            elif t == 'wait':
                print('\nWaiting for opponent...')
            elif t == 'update':
                print('\nBoard updated. Next:', msg.get('next'))
                print_board(msg.get('board'))
            elif t == 'invalid':
                print('Invalid move:', msg.get('reason'))
            elif t == 'game_over':
                print('\nGame over:', msg.get('result'))
                print_board(msg.get('board'))
                break
            else:
                print('Unknown message:', msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=HOST)
    parser.add_argument('--port', type=int, default=PORT)
    args = parser.parse_args()
    run(args.host, args.port)
