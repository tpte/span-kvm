#!/usr/bin/env python3
"""Mac side of span-kvm.

The cursor stays visible until the MSI acks. A missing ack or a dead
socket puts it back in the center. Run this with the Python that already
has Accessibility:
/Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9
"""
import json
import os
import socket
import sys
import threading
import time

import Quartz

from gate import decide
from keys import linux_code, modifier_key_messages
from layout import enter_fields, load, place_on_mac

sys.stdout = open("/tmp/span-mac.log", "a", buffering=1)
sys.stderr = sys.stdout

MSI = ("172.20.10.4", 42421)
ACK_S = 1.0
CENTER = (720, 450)
LAYOUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "layout.json")
quiet_until = 0.0

phase = "local"  # local | waiting | remote
lock = threading.Lock()
sock = None
waiting_since = 0.0
pin = None
last_edge = None
held_flags = 0


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
    global phase, sock, pin
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
                        for payload in modifier_key_messages(held_flags):
                            send(payload)
                        print("acked, mac cursor pinned", pin, flush=True)
            elif msg.get("t") == "back":
                with lock:
                    screens = load(LAYOUT)
                    point = place_on_mac(screens, msg["screen"], msg["hypr_y"])
                    settle("slide back", point, quiet=0.12, clear_mod_flags=False)


def edge_point(edge):
    xmin, ymin, xmax, ymax = bounds()
    y = (ymin + ymax) / 2
    if edge == "left":
        return (xmin + 1, y)
    return (xmax - 1, y)


def home_point(edge):
    xmin, _, xmax, ymax = bounds()
    y = ymax / 2
    if edge == "left":
        return (xmin + 36, y)
    if edge == "right":
        return (xmax - 36, y)
    return CENTER


def settle(reason, point, quiet=0.35, clear_mod_flags=True):
    """Return the pointer to the Mac without dropping the MSI socket."""
    global phase, pin, quiet_until, held_flags
    print("release:", reason, point, flush=True)
    phase = "local"
    pin = None
    quiet_until = time.time() + quiet
    if clear_mod_flags:
        held_flags = 0
    send({"t": "upall"})
    show()
    Quartz.CGWarpMouseCursorPosition(point)


def release(reason, edge=None):
    global sock
    settle(reason, home_point(edge))
    send({"t": "leave"})
    if sock is not None:
        try:
            sock.close()
        except OSError:
            pass
        sock = None


def hide():
    Quartz.CGDisplayHideCursor(Quartz.CGMainDisplayID())


def show():
    disp = Quartz.CGMainDisplayID()
    for _ in range(32):
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


def flag_changes(event):
    global held_flags
    flags = Quartz.CGEventGetFlags(event)
    pairs = (
        (Quartz.kCGEventFlagMaskControl, 29),
        (Quartz.kCGEventFlagMaskShift, 42),
        (Quartz.kCGEventFlagMaskAlternate, 56),
        (Quartz.kCGEventFlagMaskCommand, 125),
    )
    changes = []
    for bit, code in pairs:
        now = bool(flags & bit)
        was = bool(held_flags & bit)
        if now != was:
            changes.append((code, now))
    held_flags = flags
    return changes


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
    global phase, waiting_since, last_edge, pin
    with lock:
        if phase != "local":
            return
        phase = "waiting"
        last_edge = edge
        pin = edge_point(edge)
        waiting_since = time.time()
        Quartz.CGWarpMouseCursorPosition(pin)
    print("waiting", edge, flush=True)
    screens = load(LAYOUT)
    if not connect() or not send(enter_fields(screens, edge)):
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


def kind_of(etype):
    if etype in (
        Quartz.kCGEventMouseMoved,
        Quartz.kCGEventLeftMouseDragged,
        Quartz.kCGEventRightMouseDragged,
    ):
        return "move"
    if etype in (Quartz.kCGEventLeftMouseUp, Quartz.kCGEventRightMouseUp, Quartz.kCGEventOtherMouseUp):
        return "up"
    if etype in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventRightMouseDown, Quartz.kCGEventOtherMouseDown):
        return "down"
    if etype in (Quartz.kCGEventKeyDown, Quartz.kCGEventKeyUp):
        return "key"
    if etype == Quartz.kCGEventScrollWheel:
        return "scroll"
    return "other"


def button_of(etype, event):
    if etype in (Quartz.kCGEventRightMouseDown, Quartz.kCGEventRightMouseUp):
        return "right"
    if etype in (Quartz.kCGEventOtherMouseDown, Quartz.kCGEventOtherMouseUp):
        return "middle"
    return "left"


def callback(proxy, etype, event, refcon):
    global phase
    if etype == Quartz.kCGEventTapDisabledByTimeout:
        if tap is not None:
            Quartz.CGEventTapEnable(tap, True)
        return event
    if mods_down(event):
        with lock:
            remote = phase != "local"
            if remote:
                send({"t": "upall"})
                release("chord")
        return None if remote else event
    if etype == Quartz.kCGEventFlagsChanged:
        changes = flag_changes(event)
        with lock:
            if phase == "remote":
                for code, down in changes:
                    send({"t": "key", "code": code, "down": down})
                return None
        return event
    kind = kind_of(etype)
    if kind == "key":
        with lock:
            state = phase
        if state != "remote":
            return None if state == "waiting" else event
        mac_code = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        code = linux_code(mac_code)
        if code is not None:
            send({"t": "key", "code": code, "down": etype == Quartz.kCGEventKeyDown})
        return None
    if kind == "other":
        return event
    with lock:
        state = phase
        if state == "waiting" and time.time() - waiting_since > ACK_S:
            release("no ack")
            state = "local"
        if time.time() < quiet_until:
            return event
        edge = crossed(event) if state == "local" and kind == "move" else None
        if edge and state == "local":
            threading.Thread(target=begin, args=(edge,), daemon=True).start()
            return None
        effect, message = decide(state, kind)
        if effect == "pass":
            return event
        if message == "move":
            dx = Quartz.CGEventGetDoubleValueField(event, Quartz.kCGMouseEventDeltaX)
            dy = Quartz.CGEventGetDoubleValueField(event, Quartz.kCGMouseEventDeltaY)
            if not send({"t": "move", "dx": dx, "dy": dy}):
                release("send failed")
        elif message in ("down", "up"):
            if not send({"t": "button", "btn": button_of(etype, event), "down": message == "down"}):
                release("send failed")
        elif message == "scroll":
            dy = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGScrollWheelEventDeltaAxis1
            )
            dx = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGScrollWheelEventDeltaAxis2
            )
            horizontal = bool(dx) and not dy
            if not send(
                {
                    "t": "scroll",
                    "dx": int(dx),
                    "dy": int(dy),
                    "horizontal": horizontal,
                }
            ):
                release("send failed")
        return None


def serve_desk():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "desk.html")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/layout"):
                body = open(LAYOUT, "rb").read()
                kind = "application/json"
            else:
                body = open(html_path, "rb").read()
                kind = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            size = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(size)
            json.loads(body)
            with open(LAYOUT, "wb") as handle:
                handle.write(body)
            self.send_response(204)
            self.end_headers()

        def log_message(self, fmt, *args):
            return

    ThreadingHTTPServer(("127.0.0.1", 42422), Handler).serve_forever()


def main():
    global tap
    threading.Thread(target=serve_desk, daemon=True).start()
    print("desk ui http://127.0.0.1:42422", flush=True)
    mask = (
        Quartz.CGEventMaskBit(Quartz.kCGEventMouseMoved)
        | Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseDragged)
        | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDragged)
        | Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseDown)
        | Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseUp)
        | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDown)
        | Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseUp)
        | Quartz.CGEventMaskBit(Quartz.kCGEventOtherMouseDown)
        | Quartz.CGEventMaskBit(Quartz.kCGEventOtherMouseUp)
        | Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
        | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
        | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        | Quartz.CGEventMaskBit(Quartz.kCGEventScrollWheel)
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
