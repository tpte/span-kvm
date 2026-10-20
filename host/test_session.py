import unittest

from session import RemoteSession


class FakeSink:
    def __init__(self):
        self.places = []
        self.buttons = []
        self.keys = []
        self.scrolls = []
        self.released = 0

    def place(self, x, y):
        self.places.append((x, y))

    def button(self, name, down):
        self.buttons.append((name, down))

    def key(self, code, down):
        self.keys.append((code, down))

    def scroll(self, dx, dy, horizontal):
        self.scrolls.append((dx, dy, horizontal))

    def release_keys(self):
        self.released += 1


class RemoteSessionTest(unittest.TestCase):
    def setUp(self):
        self.sink = FakeSink()
        self.session = RemoteSession(self.sink)

    def test_enter_acks_and_places(self):
        replies = self.session.feed(
            {
                "t": "enter",
                "dir": "ge",
                "back_x": 1274,
                "screen": "msi-main",
                "x": 1200,
                "y": 360,
            }
        )
        self.assertEqual(replies, [{"t": "ack"}])
        self.assertEqual(self.sink.places[-1], (1200, 360))

    def test_move_rounds_fractional_deltas(self):
        self.session.feed(
            {
                "t": "enter",
                "dir": "ge",
                "back_x": 2000,
                "screen": "msi-main",
                "x": 100,
                "y": 100,
            }
        )
        self.session.feed({"t": "move", "dx": 1.4, "dy": -0.6})
        self.assertEqual(self.sink.places[-1], (101, 99))

    def test_middle_click_while_remote(self):
        self.session.feed(
            {
                "t": "enter",
                "dir": "ge",
                "back_x": 2000,
                "screen": "msi-main",
                "x": 100,
                "y": 100,
            }
        )
        self.session.feed({"t": "button", "btn": "middle", "down": True})
        self.session.feed({"t": "button", "btn": "middle", "down": False})
        self.assertEqual(
            self.sink.buttons,
            [("middle", True), ("middle", False)],
        )

    def test_key_events_reach_sink(self):
        self.session.feed(
            {
                "t": "enter",
                "dir": "ge",
                "back_x": 2000,
                "screen": "msi-main",
                "x": 100,
                "y": 100,
            }
        )
        self.session.feed({"t": "key", "code": 30, "down": True})
        self.assertEqual(self.sink.keys, [(30, True)])

    def test_scroll_while_remote(self):
        self.session.feed(
            {
                "t": "enter",
                "dir": "ge",
                "back_x": 2000,
                "screen": "msi-main",
                "x": 100,
                "y": 100,
            }
        )
        self.session.feed({"t": "scroll", "dy": -3})
        self.assertEqual(self.sink.scrolls, [(0, -3, False)])

    def test_seam_cross_sends_back(self):
        replies = self.session.feed(
            {
                "t": "enter",
                "dir": "ge",
                "back_x": 120,
                "screen": "msi-main",
                "x": 100,
                "y": 200,
            }
        )
        self.assertEqual(replies, [{"t": "ack"}])
        replies = self.session.feed({"t": "move", "dx": 25, "dy": 0})
        self.assertEqual(
            replies,
            [{"t": "back", "screen": "msi-main", "hypr_y": 200}],
        )
        self.assertIsNone(self.session.pos)

    def test_upall_releases_keys(self):
        self.session.feed({"t": "upall"})
        self.assertEqual(self.sink.released, 1)

    def test_leave_clears_session(self):
        self.session.feed(
            {
                "t": "enter",
                "dir": "le",
                "back_x": 1286,
                "screen": "msi-ext",
                "x": 1400,
                "y": 300,
            }
        )
        self.session.feed({"t": "leave"})
        self.assertIsNone(self.session.pos)
        self.assertEqual(self.sink.released, 1)


if __name__ == "__main__":
    unittest.main()
