#!/usr/bin/env python3
"""
Automated client that plays random valid moves until game ends.
Useful for demonstration and testing.
"""
import socket
import json
import random
import time

HOST = '127.0.0.1'
PORT = 65432


def send_json(sock, obj):
    sock.sendall((json.dumps(obj) + "\n").encode())


def print_board(board):
    def c(i):
        return board[i] if board[i] != ' ' else str(i)
    print(f" {c(0)} | {c(1)} | {c(2)} ")
    print("---+---+---")
    print(f" {c(3)} | {c(4)} | {c(5)} ")
    print("---+---+---")
    print(f" {c(6)} | {c(7)} | {c(8)} ")


def run():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        rfile = s.makefile('r')
        you = None
        while True:
            line = rfile.readline()
            if not line:
                print('Server closed')
                break
            msg = json.loads(line)
            t = msg.get('type')
            if t == 'start':
                you = msg.get('you')
                print('Start. You are', you)
                print_board(msg.get('board', [' ']*9))
            elif t == 'your_turn':
                board = msg.get('board')
                avail = [i for i,c in enumerate(board) if c == ' ']
                if not avail:
                    continue
                pos = random.choice(avail)
                print(f'Playing move {pos}')
                time.sleep(0.2)
                send_json(s, { 'type': 'move', 'pos': pos })
            elif t == 'wait':
                pass
            elif t == 'update':
                print('Update. Next:', msg.get('next'))
            elif t == 'invalid':
                print('Invalid:', msg.get('reason'))
            elif t == 'game_over':
                print('Game over:', msg.get('result'))
                print_board(msg.get('board'))
                break


if __name__ == '__main__':
    run()
