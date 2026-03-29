import unittest

from app.utils.compute_card_classes import compute_card_classes


class TestComputeCardClasses(unittest.TestCase):
    def test_single_card_uses_full_width_classes(self):
        lg_classes, md_classes = compute_card_classes([{"title": "One"}])

        self.assertEqual(lg_classes, ["col-lg-12"])
        self.assertEqual(md_classes, ["col-md-12"])

    def test_two_cards_split_evenly(self):
        lg_classes, md_classes = compute_card_classes([{}, {}])

        self.assertEqual(lg_classes, ["col-lg-6", "col-lg-6"])
        self.assertEqual(md_classes, ["col-md-6", "col-md-6"])

    def test_three_cards_use_thirds(self):
        lg_classes, md_classes = compute_card_classes([{}, {}, {}])

        self.assertEqual(lg_classes, ["col-lg-4", "col-lg-4", "col-lg-4"])
        self.assertEqual(md_classes, ["col-md-6", "col-md-6", "col-md-12"])

    def test_five_cards_use_balanced_large_layout(self):
        lg_classes, md_classes = compute_card_classes([{}, {}, {}, {}, {}])

        self.assertEqual(
            lg_classes,
            ["col-lg-6", "col-lg-6", "col-lg-4", "col-lg-4", "col-lg-4"],
        )
        self.assertEqual(
            md_classes,
            ["col-md-6", "col-md-6", "col-md-6", "col-md-6", "col-md-12"],
        )


if __name__ == "__main__":
    unittest.main()
