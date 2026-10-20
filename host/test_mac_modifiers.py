import unittest

from keys import (
    FLAG_ALT,
    FLAG_COMMAND,
    FLAG_CONTROL,
    FLAG_MODIFIER_LINUX,
    FLAG_SHIFT,
    active_modifier_linux_codes,
    modifier_key_messages,
)


class ModifierSyncTest(unittest.TestCase):
    def test_shift_only(self):
        self.assertEqual(active_modifier_linux_codes(FLAG_SHIFT), [42])

    def test_command_and_control(self):
        flags = FLAG_COMMAND | FLAG_CONTROL
        self.assertEqual(sorted(active_modifier_linux_codes(flags)), [29, 125])

    def test_messages_are_key_down(self):
        msgs = modifier_key_messages(FLAG_ALT)
        self.assertEqual(msgs, [{"t": "key", "code": 56, "down": True}])

    def test_table_matches_modifier_bits_names(self):
        by_code = {code: name for name, code in (
            ("ctrl", 29),
            ("shift", 42),
            ("alt", 56),
            ("meta", 125),
        )}
        for _mask, code in FLAG_MODIFIER_LINUX:
            self.assertIn(code, by_code)


if __name__ == "__main__":
    unittest.main()
