"""Desk arrangement. Screens are rectangles the user drags. Devices are just ids."""
import json


def load(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return data["screens"]


def screen(screens, screen_id):
    for item in screens:
        if item["id"] == screen_id:
            return item
    raise KeyError(screen_id)


def mac_screen(screens):
    for item in screens:
        if item["device"] == "mac":
            return item
    raise KeyError("mac")


def beside(screens, item):
    """MSI screen edges that touch the Mac in the desk the user arranged."""
    mac = mac_screen(screens)
    touches = []
    if item["x"] + item["w"] == mac["x"]:
        touches.append("right")
    if item["x"] == mac["x"] + mac["w"]:
        touches.append("left")
    return touches


def screen_for_mac_edge(screens, edge):
    for item in screens:
        if item.get("device") == "mac":
            continue
        edges = beside(screens, item)
        if edge == "left" and "right" in edges:
            return item["id"]
        if edge == "right" and "left" in edges:
            return item["id"]
    raise KeyError(edge)


def enter_fields(screens, edge):
    screen_id = screen_for_mac_edge(screens, edge)
    x, y = landing(screens, screen_id)
    item = screen(screens, screen_id)
    facing = beside(screens, item)[0]
    if facing == "right":
        back_x = item["hypr_x"] + item["hypr_w"] - 6
        direction = "ge"
    else:
        back_x = item["hypr_x"] + 6
        direction = "le"
    return {
        "t": "enter",
        "screen": screen_id,
        "x": x,
        "y": y,
        "back_x": back_x,
        "dir": direction,
    }


def landing(screens, screen_id):
    item = screen(screens, screen_id)
    edge = beside(screens, item)[0]
    inset = 80
    if edge == "right":
        x = item["hypr_x"] + item["hypr_w"] - inset
    else:
        x = item["hypr_x"] + inset
    y = item["hypr_y"] + item["hypr_h"] // 2
    return x, y


def place_on_mac(screens, screen_id, hypr_y):
    """Mac-local point continuing from this MSI screen's Hyprland y."""
    item = screen(screens, screen_id)
    edge = beside(screens, item)[0]
    mac = mac_screen(screens)
    rel = (hypr_y - item["hypr_y"]) / float(item["hypr_h"])
    rel = min(1, max(0, rel))
    mac_y = int(rel * mac["h"])
    if edge == "right":
        return 12, mac_y
    return mac["w"] - 12, mac_y


def handback(screens, screen_id, hypr_x, hypr_y):
    """Return a Mac-local point when the MSI pointer hits the seam, else None."""
    item = screen(screens, screen_id)
    edges = beside(screens, item)
    if not edges:
        return None
    edge = edges[0]
    seam = 6
    if edge == "right" and hypr_x < item["hypr_x"] + item["hypr_w"] - seam:
        return None
    if edge == "left" and hypr_x > item["hypr_x"] + seam:
        return None
    return place_on_mac(screens, screen_id, hypr_y)
