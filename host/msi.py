#!/usr/bin/env python3
"""MSI side of span-kvm. Moves the Hyprland pointer. Does not grab the Mac."""
import json
import os
import socket
import subprocess

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


def handle(conn, env):
    buf = b""
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
                x, y = LANDING[msg["edge"]]
                hypr(env, "hl.dsp.cursor.move({ x = %d, y = %d })" % (x, y))
                conn.sendall(b'{"t":"ack"}\n')
            elif kind == "move":
                x, y = cursor(env)
                hypr(
                    env,
                    "hl.dsp.cursor.move({ x = %d, y = %d })"
                    % (x + int(msg["dx"]), y + int(msg["dy"])),
                )
            elif kind == "leave":
                return


def main():
    env = hypr_env()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print("span-msi listening %s:%s" % (HOST, PORT), flush=True)
    while True:
        conn, addr = server.accept()
        print("span-msi client", addr, flush=True)
        try:
            handle(conn, env)
        except Exception as exc:
            print("span-msi error", exc, flush=True)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
