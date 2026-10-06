import unittest
from datetime import date, timedelta

from app.grading import correction, current_streak, grade, normalize, validate_answer


class GradingTests(unittest.TestCase):
    def test_normalization_preserves_accents(self):
        self.assertEqual(normalize("  HELLO   there! "), "hello there")
        self.assertNotEqual(normalize("sí"), normalize("si"))

    def test_choice_uses_id_not_display_text(self):
        self.assertTrue(grade("multiple_choice", {}, {"option_id": "b"}, {"option_id": "b"}))
        self.assertFalse(grade("multiple_choice", {}, {"option_id": "b"}, {"option_id": "hello"}))

    def test_word_bank_order_and_duplicate_word_ids(self):
        expected = {"token_ids": ["a", "b", "c"]}
        self.assertTrue(grade("word_bank", {}, expected, expected))
        self.assertFalse(grade("word_bank", {}, expected, {"token_ids": ["b", "a", "c"]}))
        public = {"tokens": [{"id": "a", "text": "very"}, {"id": "b", "text": "very"}, {"id": "c", "text": "good"}]}
        self.assertEqual(correction("word_bank", public, expected), "very very good")

    def test_matching_requires_exact_complete_mapping(self):
        expected = {"pairs": {"a": "x", "b": "y"}}
        self.assertTrue(grade("match_pairs", {}, expected, {"pairs": {"b": "y", "a": "x"}}))
        self.assertFalse(grade("match_pairs", {}, expected, {"pairs": {"a": "x"}}))

    def test_typed_answer_accepts_curated_variants(self):
        expected = {"accepted": ["Hello, good morning", "Good morning"]}
        self.assertTrue(grade("type_answer", {}, expected, {"text": "  GOOD MORNING!"}))
        self.assertFalse(grade("type_answer", {}, expected, {"text": 23}))
        self.assertFalse(grade("fill_blank", {}, {"accepted": ["sí"]}, {"text": "si"}))

    def test_daily_streak_boundaries(self):
        today = date(2026, 10, 6)
        previous = {today - timedelta(days=i) for i in (1, 2, 3)}
        self.assertEqual(current_streak(previous, today), 3)
        self.assertEqual(current_streak(previous | {today}, today), 4)
        self.assertEqual(current_streak(previous, today + timedelta(days=1)), 0)
        self.assertEqual(current_streak({today, today - timedelta(days=2)}, today), 1)

    def test_invalid_answer_payloads(self):
        for kind, public, answer in [
            ("multiple_choice", {"options": [{"id": "a"}]}, {"option_id": []}),
            ("word_bank", {"tokens": [{"id": "a"}]}, {"token_ids": ["a", "a"]}),
            ("word_bank", {"tokens": [{"id": "a"}]}, {"token_ids": [{}]}),
            ("match_pairs", {"left": [{"id": "a"}], "right": [{"id": "b"}]}, {"pairs": {"a": []}}),
            ("type_answer", {}, {"text": " "}),
        ]:
            with self.subTest(kind=kind, answer=answer):
                with self.assertRaises((ValueError, TypeError)):
                    validate_answer(kind, public, answer)


if __name__ == "__main__":
    unittest.main()
