"""MSI-side remote pointer session. One JSON message in, side effects and replies out."""


class RemoteSession:
    def __init__(self, sink, canvas=(3200, 1080)):
        self.sink = sink
        self.max_x, self.max_y = canvas[0] - 1, canvas[1] - 1
        self.pos = None
        self.direction = None
        self.back_x = None
        self.screen_id = None

    def _clamp_place(self, x, y):
        x = max(0, min(self.max_x, int(x)))
        y = max(0, min(self.max_y, int(y)))
        self.sink.place(x, y)
        return x, y

    def feed(self, msg):
        kind = msg.get("t")
        replies = []
        if kind == "enter":
            self.direction = msg["dir"]
            self.back_x = int(msg["back_x"])
            self.screen_id = msg["screen"]
            x, y = self._clamp_place(msg["x"], msg["y"])
            self.pos = [x, y]
            replies.append({"t": "ack"})
        elif kind == "move" and self.pos is not None:
            self.pos[0] = round(self.pos[0] + float(msg["dx"]))
            self.pos[1] = round(self.pos[1] + float(msg["dy"]))
            x, y = self._clamp_place(self.pos[0], self.pos[1])
            self.pos[0], self.pos[1] = x, y
            crossed = (
                self.pos[0] >= self.back_x
                if self.direction == "ge"
                else self.pos[0] <= self.back_x
            )
            if crossed:
                replies.append(
                    {
                        "t": "back",
                        "screen": self.screen_id,
                        "hypr_y": self.pos[1],
                    }
                )
                self.pos = None
        elif kind == "button":
            self.sink.button(msg["btn"], bool(msg["down"]))
        elif kind == "key":
            self.sink.key(int(msg["code"]), bool(msg["down"]))
        elif kind == "scroll" and self.pos is not None:
            self.sink.scroll(
                int(msg.get("dx", 0)),
                int(msg.get("dy", 0)),
                bool(msg.get("horizontal", False)),
            )
        elif kind == "upall":
            self.sink.release_keys()
        elif kind == "leave":
            self.sink.release_keys()
            self.pos = None
        return replies
