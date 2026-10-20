"""What the Mac event tap does with one pointer event.

`pass` means the Mac keeps the event.
`drop` means the Mac must not apply it.
The second value is the message to send to the MSI, or None.
"""


def decide(phase, kind):
    if phase == "local":
        return "pass", None
    if kind == "move" and phase == "waiting":
        return "drop", None
    if kind == "move" and phase == "remote":
        return "drop", "move"
    if kind in ("down", "up") and phase == "remote":
        return "drop", kind
    if kind in ("down", "up") and phase == "waiting":
        return "drop", None
    return "pass", None
