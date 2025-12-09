#!/usr/bin/env python3
"""
Demo script: starts server and two automated clients, collects their output.
Run this to produce a sample game result.
"""
import subprocess
import time
import os
import signal

HERE = os.path.dirname(__file__)

def run_demo():
    server = subprocess.Popen(['python3', os.path.join(HERE, 'server.py')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        # give server a moment to start
        time.sleep(0.3)

        c1 = subprocess.Popen(['python3', os.path.join(HERE, 'auto_client.py')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        c2 = subprocess.Popen(['python3', os.path.join(HERE, 'auto_client.py')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        out1, out2 = '', ''
        try:
            out1, _ = c1.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            c1.kill(); out1 = 'client1 timeout'
        try:
            out2, _ = c2.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            c2.kill(); out2 = 'client2 timeout'

        # stop the server
        server.terminate()
        try:
            server.wait(timeout=1)
        except Exception:
            server.kill()

        s_out = ''
        try:
            s_out, _ = server.communicate(timeout=1)
        except Exception:
            s_out = ''

        print('--- SERVER ---')
        print(s_out)
        print('--- CLIENT 1 ---')
        print(out1)
        print('--- CLIENT 2 ---')
        print(out2)

    finally:
        try:
            server.kill()
        except Exception:
            pass


if __name__ == '__main__':
    run_demo()
