#!/usr/bin/env python3
"""Mac side of span-kvm.

The cursor stays visible until the MSI acks. A missing ack or a dead
socket puts it back in the center. Run this with the Python that already
has Accessibility:
/Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9
"""
import json
import socket
import sys
import threading
import time

import Quartz

sys.stdout = open("/tmp/span-mac.log", "a", buffering=1)
sys.stderr = sys.stdout

MSI = ("172.20.10.4", 42421)
ACK_S = 1.0
CENTER = (720, 450)

phase = "local"  # local | waiting | remote
lock = threading.Lock()
sock = None
waiting_since = 0.0
pin = None
last_edge = None


def send(msg):
    global sock
    data = (json.dumps(msg) + "\n").encode()
    try:
        if sock is None:
            return False
        sock.sendall(data)
        return True
    except OSError:
        return False


def connect():
    global sock
    try:
        client = socket.create_connection(MSI, timeout=0.4)
        client.settimeout(0.4)
        sock = client
        return True
    except OSError:
        sock = None
        return False


def reader():
    global phase, sock
    buf = b""
    while True:
        with lock:
            current = sock
        if current is None:
            time.sleep(0.05)
            continue
        try:
            chunk = current.recv(4096)
        except socket.timeout:
            continue
        except OSError:
            chunk = b""
        if not chunk:
            with lock:
                if sock is current:
                    sock = None
                    if phase != "local":
                        release("peer closed")
            continue
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("t") == "ack":
                with lock:
                    if phase == "waiting":
                        phase = "remote"
                        pin = edge_point(last_edge or "right")
                        Quartz.CGWarpMouseCursorPosition(pin)
                        hide()
                        print("acked, mac cursor pinned", pin, flush=True)


def edge_point(edge):
    xmin, ymin, xmax, ymax = bounds()
    y = (ymin + ymax) / 2
    if edge == "left":
        return (xmin + 1, y)
    return (xmax - 1, y)


def release(reason):
    global phase, sock, pin
    print("release:", reason, flush=True)
    phase = "local"
    pin = None
    send({"t": "leave"})
    if sock is not None:
        try:
            sock.close()
        except OSError:
            pass
        sock = None
    show()
    Quartz.CGWarpMouseCursorPosition(CENTER)


def hide():
    Quartz.CGDisplayHideCursor(Quartz.CGMainDisplayID())


def show():
    disp = Quartz.CGMainDisplayID()
    for _ in range(8):
        Quartz.CGDisplayShowCursor(disp)


def bounds():
    b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    return b.origin.x, b.origin.y, b.origin.x + b.size.width, b.origin.y + b.size.height


def crossed(event):
    x = Quartz.CGEventGetLocation(event).x
    dx = Quartz.CGEventGetDoubleValueField(event, Quartz.kCGMouseEventDeltaX)
    xmin, _, xmax, _ = bounds()
    if x + dx <= xmin:
        return "left"
    if x + dx >= xmax:
        return "right"
    return None


def mods_down(event):
    flags = Quartz.CGEventGetFlags(event)
    need = (
        Quartz.kCGEventFlagMaskControl
        | Quartz.kCGEventFlagMaskShift
        | Quartz.kCGEventFlagMaskCommand
        | Quartz.kCGEventFlagMaskAlternate
    )
    return flags & need == need


def begin(edge):
    global phase, waiting_since, last_edge
    with lock:
        if phase != "local":
            return
        phase = "waiting"
        last_edge = edge
        waiting_since = time.time()
    print("waiting", edge, flush=True)
    if not connect() or not send({"t": "enter", "edge": edge}):
        with lock:
            release("connect failed")
        return
    deadline = time.time() + ACK_S
    while time.time() < deadline:
        with lock:
            if phase != "waiting":
                return
        time.sleep(0.02)
    with lock:
        if phase == "waiting":
            release("no ack")


def callback(proxy, etype, event, refcon):
    global phase
    if etype == Quartz.kCGEventTapDisabledByTimeout:
        if tap is not None:
            Quartz.CGEventTapEnable(tap, True)
        return event
    if mods_down(event):
        with lock:
            if phase != "local":
                release("chord")
        return event
    if etype not in (
        Quartz.kCGEventMouseMoved,
        Quartz.kCGEventLeftMouseDragged,
        Quartz.kCGEventRightMouseDragged,
    ):
        return event
    with lock:
        state = phase
        if state == "waiting" and time.time() - waiting_since > ACK_S:
            release("no ack")
            state = "local"
        edge = crossed(event) if state == "local" else None
        if edge and state == "local":
            threading.Thread(target=begin, args=(edge,), daemon=True).start()
            return event
        if state == "remote":
            dx = Quartz.CGEventGetDoubleValueField(event, Quartz.kCGMouseEventDeltaX)
            dy = Quartz.CGEventGetDoubleValueField(event, Quartz.kCGMouseEventDeltaY)
            if not send({"t": "move", "dx": dx, "dy": dy}):
                release("send failed")
            else:
                # Drop the local move. Warping back covers the cases where
                # the window server still applies the event.
                Quartz.CGEventSetType(event, Quartz.kCGEventNull)
                if pin is not None:
                    Quartz.CGWarpMouseCursorPosition(pin)
            return event
    return event


def main():
    global tap
    mask = (
        Quartz.CGEventMaskBit(Quartz.kCGEventMouseMoved)
        | Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseDragged)
        | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDragged)
        | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
    )
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        Quartz.kCGEventTapOptionDefault,
        mask,
        callback,
        None,
    )
    if tap is None:
        raise SystemExit("event tap was not created; Accessibility is missing")
    source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(), source, Quartz.kCFRunLoopCommonModes
    )
    Quartz.CGEventTapEnable(tap, True)
    threading.Thread(target=reader, daemon=True).start()
    print("span-mac running", flush=True)
    Quartz.CFRunLoopRun()


if __name__ == "__main__":
    main()
