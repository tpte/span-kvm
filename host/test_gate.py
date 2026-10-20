import unittest

from gate import decide
from keys import linux_code


class DecideTest(unittest.TestCase):
    def test_remote_click_is_forwarded_and_not_applied_locally(self):
        effect, message = decide("remote", "down")
        self.assertEqual(effect, "drop")
        self.assertEqual(message, "down")

    def test_remote_move_does_not_stay_on_the_mac(self):
        effect, message = decide("remote", "move")
        self.assertEqual(effect, "drop")
        self.assertEqual(message, "move")

    def test_letter_a_reaches_linux(self):
        self.assertEqual(linux_code(0), 30)

    def test_local_move_is_not_forwarded(self):
        effect, message = decide("local", "move")
        self.assertEqual(effect, "pass")
        self.assertIsNone(message)

    def test_remote_scroll_is_forwarded(self):
        effect, message = decide("remote", "scroll")
        self.assertEqual(effect, "drop")
        self.assertEqual(message, "scroll")


if __name__ == "__main__":
    unittest.main()
