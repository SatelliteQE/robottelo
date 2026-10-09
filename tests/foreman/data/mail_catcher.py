"""Minimal, dependency-free SMTP server used to "catch" outgoing mail locally on
foremanctl-based hosts, where ``delivery_method`` is hardcoded to ``smtp`` and
cannot be switched to ``file``.

Usage: python3 mail_catcher.py <port> <mails_dir>
"""

from contextlib import suppress
from email import message_from_bytes
import mailbox
import os
import socket
import sys
import threading

PORT = int(sys.argv[1])
MAILS_DIR = sys.argv[2]


def handle(conn):
    conn.settimeout(60)
    rfile = conn.makefile('rb')
    wfile = conn.makefile('wb')

    def send(line):
        wfile.write(line.encode() + b'\r\n')
        wfile.flush()

    send('220 mail-catcher')
    recipients = []
    try:
        while True:
            line = rfile.readline()
            if not line:
                break
            cmd = line.decode(errors='replace').strip()
            upper = cmd.upper()
            if upper.startswith('EHLO') or upper.startswith('HELO'):
                send('250 mail-catcher')
            elif upper.startswith('MAIL FROM'):
                send('250 OK')
            elif upper.startswith('RCPT TO'):
                start = cmd.find('<')
                end = cmd.find('>')
                if start != -1 and end != -1:
                    addr = cmd[start + 1 : end]
                else:
                    addr = cmd.split(':', 1)[-1].strip()
                recipients.append(addr)
                send('250 OK')
            elif upper.startswith('DATA'):
                send('354 End data with <CR><LF>.<CR><LF>')
                data_lines = []
                while True:
                    dline = rfile.readline()
                    if dline in (b'.\r\n', b'.\n', b''):
                        break
                    if dline.startswith(b'..'):
                        dline = dline[1:]
                    data_lines.append(dline)
                message = message_from_bytes(b''.join(data_lines))
                for addr in recipients:
                    box = mailbox.mbox(os.path.join(MAILS_DIR, addr))
                    box.lock()
                    try:
                        box.add(message)
                        box.flush()
                    finally:
                        box.unlock()
                        box.close()
                send('250 OK: queued')
                recipients = []
            elif upper.startswith('RSET'):
                recipients = []
                send('250 OK')
            elif upper.startswith('QUIT'):
                send('221 Bye')
                break
            else:
                send('502 Command not implemented')
    except Exception:
        pass
    finally:
        with suppress(Exception):
            conn.close()


def main():
    os.makedirs(MAILS_DIR, exist_ok=True)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(50)
    while True:
        conn, _addr = server.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == '__main__':
    main()
