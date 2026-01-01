"""Tests for CriteriaEvaluator with Rebrickable data."""

import unittest
from unittest.mock import MagicMock, patch
from lego_sorter.LayerCake.criteria_evaluator import CriteriaEvaluator
from lego_sorter.rb_parts import RbPart, RbPartCategory
from lego_sorter.rb_colour import RbColour, RbColours

class TestCriteriaEvaluator(unittest.TestCase):
    def setUp(self):
        # Mock RbColours to avoid loading CSVs
        self.mock_color = RbColour(1, "Blue", False)
        
        # Mock RbPart
        self.mock_category = RbPartCategory(11, "Bricks")
        self.mock_part = RbPart("3001", "Brick 2x4", self.mock_category)

    def test_color_id_match(self):
        evaluator = CriteriaEvaluator("RB_COL = 1")
        # Pass mock color
        result = evaluator.evaluate(rb_col=self.mock_color)
        self.assertTrue(result)

    def test_color_name_match(self):
        evaluator = CriteriaEvaluator("RB_COL = Blue")
        result = evaluator.evaluate(rb_col=self.mock_color)
        self.assertTrue(result)

    def test_part_num_match(self):
        evaluator = CriteriaEvaluator("RB_PT = 3001")
        result = evaluator.evaluate(rb_part=self.mock_part)
        self.assertTrue(result)

    def test_part_category_match(self):
        evaluator = CriteriaEvaluator("RB_PT_CAT = Bricks")
        result = evaluator.evaluate(rb_part=self.mock_part)
        self.assertTrue(result)

    def test_complex_expression(self):
        evaluator = CriteriaEvaluator("RB_COL = Blue AND RB_PT = 3001")
        result = evaluator.evaluate(rb_part=self.mock_part, rb_col=self.mock_color)
        self.assertTrue(result)

    def test_fail_condition(self):
        evaluator = CriteriaEvaluator("RB_COL = Red")
        result = evaluator.evaluate(rb_col=self.mock_color)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
