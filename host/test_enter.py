import os
import unittest

from layout import enter_fields, load

HERE = os.path.join(os.path.dirname(__file__), "..", "layout.json")


class EnterMessageTest(unittest.TestCase):
    def setUp(self):
        self.screens = load(HERE)

    def test_left_edge_targets_laptop_with_le_seam(self):
        msg = enter_fields(self.screens, "left")
        self.assertEqual(msg["t"], "enter")
        self.assertEqual(msg["screen"], "msi-main")
        self.assertEqual(msg["dir"], "ge")
        self.assertEqual(msg["back_x"], 1274)

    def test_right_edge_targets_external_with_ge_seam(self):
        msg = enter_fields(self.screens, "right")
        self.assertEqual(msg["screen"], "msi-ext")
        self.assertEqual(msg["dir"], "le")
        self.assertEqual(msg["back_x"], 1286)


if __name__ == "__main__":
    unittest.main()
