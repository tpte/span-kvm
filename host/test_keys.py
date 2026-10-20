import unittest

from keys import MAC_TO_LINUX, MODIFIER_BITS, linux_code


class KeysTest(unittest.TestCase):
    def test_modifiers_map_to_linux_evdev(self):
        expected = {"ctrl": 29, "shift": 42, "alt": 56, "meta": 125}
        for name, code in MODIFIER_BITS:
            self.assertEqual(expected[name], code)

    def test_mac_flag_codes_match_modifier_table(self):
        mac_modifiers = {59: 29, 56: 42, 58: 56, 55: 125}
        for mac_code, linux_code_expected in mac_modifiers.items():
            self.assertEqual(linux_code(mac_code), linux_code_expected)

    def test_space_and_enter(self):
        self.assertEqual(linux_code(49), 57)
        self.assertEqual(linux_code(36), 28)

    def test_unknown_mac_key_is_ignored(self):
        self.assertIsNone(linux_code(99999))

    def test_common_letter_keys_are_mapped(self):
        for mac in (0, 4, 8, 12, 16, 25):
            self.assertIsNotNone(linux_code(mac))
            self.assertIn(mac, MAC_TO_LINUX)


if __name__ == "__main__":
    unittest.main()
