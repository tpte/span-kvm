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


EV_SYN, EV_KEY, EV_ABS, EV_REL = 0, 1, 3, 2
SYN_REPORT, ABS_X, ABS_Y = 0, 0, 1
REL_WHEEL, REL_HWHEEL = 8, 6
BTN = {"left": 0x110, "right": 0x111, "middle": 0x112}
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_ABSBIT, UI_SET_RELBIT = (
    0x40045564,
    0x40045565,
    0x40045567,
    0x40045566,
)
UI_DEV_SETUP, UI_DEV_CREATE = 0x405C5503, 0x5501
UI_ABS_SETUP = 0x401C5504


class VirtualPointer:
    """Absolute pointer. Relative reports get libinput acceleration and drift."""

    def __init__(self):
        self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        self.held = set()
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_ABS)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_REL)
        fcntl.ioctl(self.fd, UI_SET_RELBIT, REL_WHEEL)
        fcntl.ioctl(self.fd, UI_SET_RELBIT, REL_HWHEEL)
        for code in list(BTN.values()) + list(range(1, 249)):
            try:
                fcntl.ioctl(self.fd, UI_SET_KEYBIT, code)
            except OSError:
                pass
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_X)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_Y)
        fcntl.ioctl(self.fd, UI_ABS_SETUP, struct.pack("HH6i", ABS_X, 0, 0, 0, 3199, 0, 0, 0))
        fcntl.ioctl(self.fd, UI_ABS_SETUP, struct.pack("HH6i", ABS_Y, 0, 0, 0, 1079, 0, 0, 0))
        setup = struct.pack("HHHH80sI", 3, 0x1234, 0x5678, 1, b"span-kvm", 0)
        fcntl.ioctl(self.fd, UI_DEV_SETUP, setup)
        fcntl.ioctl(self.fd, UI_DEV_CREATE)

    def emit(self, typ, code, value):
        os.write(self.fd, struct.pack("QQHHi", 0, 0, typ, code, int(value)))

    def place(self, x, y):
        self.emit(EV_ABS, ABS_X, max(0, min(3199, x)))
        self.emit(EV_ABS, ABS_Y, max(0, min(1079, y)))
        self.emit(EV_SYN, SYN_REPORT, 0)

    def button(self, name, down):
        self.emit(EV_KEY, BTN[name], 1 if down else 0)
        self.emit(EV_SYN, SYN_REPORT, 0)

    def key(self, code, down):
        code = int(code)
        self.emit(EV_KEY, code, 1 if down else 0)
        self.emit(EV_SYN, SYN_REPORT, 0)
        if down:
            self.held.add(code)
        else:
            self.held.discard(code)

    def release_keys(self):
        for code in list(self.held):
            self.key(code, False)

    def scroll(self, dx, dy, horizontal):
        if horizontal and dx:
            self.emit(EV_REL, REL_HWHEEL, dx)
        elif dy:
            self.emit(EV_REL, REL_WHEEL, dy)
        self.emit(EV_SYN, SYN_REPORT, 0)


class HyprSink:
    def __init__(self, env):
        self.env = env

    def place(self, x, y):
        hypr(self.env, "hl.dsp.cursor.move({ x = %d, y = %d })" % (x, y))

    def button(self, name, down):
        pass

    def key(self, code, down):
        pass

    def scroll(self, dx, dy, horizontal):
        pass

    def release_keys(self):
        pass


def handle(conn, env, pointer):
    from session import RemoteSession

    buf = b""
    sink = pointer if pointer is not None else HyprSink(env)
    session = RemoteSession(sink)
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
            if msg.get("t") == "leave":
                session.feed(msg)
                return
            for reply in session.feed(msg):
                if reply.get("t") == "back":
                    print(
                        "back",
                        reply["screen"],
                        reply["hypr_y"],
                        flush=True,
                    )
                conn.sendall((json.dumps(reply) + "\n").encode())


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
