#!/usr/bin/env python3
"""MSI side of span-kvm. Moves the Hyprland pointer. Does not grab the Mac."""
import json
import os
import socket
import struct
import subprocess
import fcntl

HOST = "0.0.0.0"
PORT = 42421
LANDING = {
    "left": (1240, 360),
    "right": (1320, 540),
}


def hypr_env():
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if not sig:
        base = os.path.join(runtime, "hypr")
        names = os.listdir(base)
        if not names:
            raise RuntimeError("no hyprland instance")
        sig = names[0]
    env = os.environ.copy()
    env["XDG_RUNTIME_DIR"] = runtime
    env["HYPRLAND_INSTANCE_SIGNATURE"] = sig
    return env


def hypr(env, code):
    subprocess.run(
        ["hyprctl", "dispatch", code],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cursor(env):
    out = subprocess.check_output(["hyprctl", "cursorpos"], env=env, text=True)
    x, y = out.strip().split(",")
    return int(x), int(y)


EV_SYN, EV_KEY, EV_REL = 0, 1, 2
SYN_REPORT, REL_X, REL_Y = 0, 0, 1
BTN = {"left": 0x110, "right": 0x111}
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT = 0x40045564, 0x40045565, 0x40045566
UI_DEV_SETUP, UI_DEV_CREATE = 0x405C5503, 0x5501


class VirtualPointer:
    def __init__(self):
        self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        for bit, codes in (
            (UI_SET_EVBIT, (EV_KEY, EV_REL)),
            (UI_SET_KEYBIT, BTN.values()),
            (UI_SET_RELBIT, (REL_X, REL_Y)),
        ):
            for code in codes:
                fcntl.ioctl(self.fd, bit, code)
        setup = struct.pack("HHHH80sI", 3, 0x1234, 0x5678, 1, b"span-kvm", 0)
        fcntl.ioctl(self.fd, UI_DEV_SETUP, setup)
        fcntl.ioctl(self.fd, UI_DEV_CREATE)

    def emit(self, typ, code, value):
        os.write(self.fd, struct.pack("QQHHi", 0, 0, typ, code, value))

    def move(self, dx, dy):
        if dx:
            self.emit(EV_REL, REL_X, int(dx))
        if dy:
            self.emit(EV_REL, REL_Y, int(dy))
        self.emit(EV_SYN, SYN_REPORT, 0)

    def button(self, name, down):
        self.emit(EV_KEY, BTN[name], 1 if down else 0)
        self.emit(EV_SYN, SYN_REPORT, 0)


def returning(edge, x):
    # Laptop occupies x 0..1280. BenQ starts at 1280. The Mac sits in that seam.
    if edge == "left":
        return x >= 1276
    if edge == "right":
        return x <= 1284
    return False


def handle(conn, env, pointer):
    buf = b""
    edge = None
    pos = None
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if not line:
                continue
            msg = json.loads(line)
            kind = msg.get("t")
            if kind == "enter":
                edge = msg["edge"]
                pos = list(LANDING[edge])
                hypr(env, "hl.dsp.cursor.move({ x = %d, y = %d })" % (pos[0], pos[1]))
                conn.sendall(b'{"t":"ack"}\n')
            elif kind == "move" and pos is not None:
                pos[0] += int(msg["dx"])
                pos[1] += int(msg["dy"])
                if pointer is not None:
                    pointer.move(msg["dx"], msg["dy"])
                else:
                    hypr(
                        env,
                        "hl.dsp.cursor.move({ x = %d, y = %d })" % (pos[0], pos[1]),
                    )
                if returning(edge, pos[0]):
                    print("back", edge, pos[0], flush=True)
                    conn.sendall(
                        ('{"t":"back","edge":"%s"}\n' % edge).encode()
                    )
                    return
            elif kind == "button" and pointer is not None:
                print("button", msg["btn"], msg["down"], flush=True)
                pointer.button(msg["btn"], msg["down"])
            elif kind == "leave":
                return


def main():
    env = hypr_env()
    try:
        pointer = VirtualPointer()
        print("span-msi virtual pointer ready", flush=True)
    except OSError as exc:
        pointer = None
        print("span-msi no uinput, clicks will not land:", exc, flush=True)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print("span-msi listening %s:%s" % (HOST, PORT), flush=True)
    while True:
        conn, addr = server.accept()
        print("span-msi client", addr, flush=True)
        try:
            handle(conn, env, pointer)
        except Exception as exc:
            print("span-msi error", exc, flush=True)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
