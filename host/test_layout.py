import os
import unittest

from layout import handback, landing, load

HERE = os.path.join(os.path.dirname(__file__), "..", "layout.json")


class LayoutTest(unittest.TestCase):
    def setUp(self):
        self.screens = load(HERE)

    def test_laptop_right_edge_returns_to_the_left_of_the_mac(self):
        point = handback(self.screens, "msi-main", 1278, 360)
        self.assertEqual(point[0], 12)

    def test_external_left_edge_returns_to_the_right_of_the_mac(self):
        point = handback(self.screens, "msi-ext", 1282, 540)
        self.assertEqual(point[0], 1440 - 12)

    def test_middle_of_the_laptop_does_not_return(self):
        self.assertIsNone(handback(self.screens, "msi-main", 400, 360))

    def test_landing_is_inset_from_the_seam(self):
        self.assertEqual(landing(self.screens, "msi-main")[0], 1280 - 80)
        self.assertEqual(landing(self.screens, "msi-ext")[0], 1280 + 80)


if __name__ == "__main__":
    unittest.main()
