"""
Tests for the lego_sorter package.

Requirements Mapping (from README):
REQ-1: Match Pieces to Buckets (Specificity)
REQ-2: Manage Capacity (Required Quantity)
REQ-3: Handle Dynamic Extensions (Automatic Extension)
REQ-4: Support Maintenance (Enabling/Disabling Buckets, Fallback)
"""

import unittest
import json
import tempfile
import os

from lego_sorter import BucketConfig, Bucket, BucketCriteria, Layer, LayerCake, CriteriaEvaluator, SortingStatus


class TestBucketConfig(unittest.TestCase):
    """Test cases for BucketConfig class."""
    
    def test_initialization_empty(self):
        """Test BucketConfig initialization with no criteria."""
        config = BucketConfig()
        self.assertEqual(len(config.criteria), 0)
    
    def test_initialization_with_criteria(self):
        """Test BucketConfig initialization with criteria list."""
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        eval2 = CriteriaEvaluator("RB_PT = 3001")
        crit1 = BucketCriteria(eval1, 10)
        crit2 = BucketCriteria(eval2, 20)
        config = BucketConfig((crit1, crit2))
        self.assertEqual(len(config.criteria), 2)
        self.assertEqual(config.criteria[0].evaluator.expression, "RB_COL = Blue")
        self.assertEqual(config.criteria[0].required_quantity, 10)

    def test_required_quantity_consistency(self):
        """
        REQ-2: Manage Capacity.
        Test that either all criteria have a required quantity or none.
        This ensures that a bucket's capacity state is never ambiguous.
        """
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        eval2 = CriteriaEvaluator("RB_PT = 3001")
        
        # All have required - OK
        BucketConfig((BucketCriteria(eval1, 10), BucketCriteria(eval2, 20)))
        
        # None have required - OK
        BucketConfig((BucketCriteria(eval1, None), BucketCriteria(eval2, None)))
        
        # Mixture - Should fail because we can't determine if the bucket is 'full' 
        # if some parts have infinite capacity and others don't.
        with self.assertRaises(ValueError):
            BucketConfig((BucketCriteria(eval1, 10), BucketCriteria(eval2, None)))
        
        with self.assertRaises(ValueError):
            BucketConfig((BucketCriteria(eval1, None), BucketCriteria(eval2, 20)))
    
    def test_equality(self):
        """Test BucketConfig equality."""
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        eval2 = CriteriaEvaluator("RB_COL = Blue")
        eval3 = CriteriaEvaluator("RB_COL = Red")
        
        config1 = BucketConfig((BucketCriteria(eval1, 10),))
        config2 = BucketConfig((BucketCriteria(eval2, 10),))
        config3 = BucketConfig((BucketCriteria(eval3, 10),))
        
        self.assertEqual(config1, config2)
        self.assertNotEqual(config1, config3)

    def test_directives_mutual_exclusivity(self):
        """
        REQ-3: Handle Dynamic Extensions.
        Test that available_for_extension and allow_extension are mutually exclusive.
        A bucket cannot be both a source and a destination for extension.
        """
        # Both True should fail
        with self.assertRaises(ValueError):
            BucketConfig(available_for_extension=True, allow_extension=True)
        
        # available_for_extension=True should default allow_extension to False
        config1 = BucketConfig(available_for_extension=True)
        self.assertTrue(config1.available_for_extension)
        self.assertFalse(config1.allow_extension)
        
        # allow_extension requires criteria
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        crit1 = BucketCriteria(eval1)
        config2 = BucketConfig(criteria=(crit1,), allow_extension=True)
        self.assertTrue(config2.allow_extension)
        self.assertFalse(config2.available_for_extension)
        
        # criteria present should default allow_extension to True
        config3 = BucketConfig(criteria=(crit1,))
        self.assertTrue(config3.allow_extension)

    def test_criteria_and_directives_validation(self):
        """Test that criteria and extension directives are validated correctly."""
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        crit1 = BucketCriteria(eval1)
        
        # Criteria + available_for_extension should fail because placeholders must be empty.
        with self.assertRaises(ValueError):
            BucketConfig(criteria=(crit1,), available_for_extension=True)
            
        # allow_extension WITHOUT criteria should fail because there's nothing to extend.
        with self.assertRaises(ValueError):
            BucketConfig(criteria=(), allow_extension=True)
            
        # allow_extension WITH criteria should pass
        config = BucketConfig(criteria=(crit1,), allow_extension=True)
        self.assertEqual(len(config.criteria), 1)
        self.assertTrue(config.allow_extension)


class TestBucketState(unittest.TestCase):
    """Test cases for BucketState class."""
    
    def test_initialization(self):
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        config = BucketConfig((BucketCriteria(eval1, 10),))
        state = Bucket(config)
        self.assertEqual(state.config, config)
        self.assertEqual(state.current_quantities, [0])
        
    def test_increment_quantity(self):
        """REQ-2: Manage Capacity. Test quantity tracking."""
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        config = BucketConfig((BucketCriteria(eval1, 10),))
        state = Bucket(config)
        state.increment_quantity(0)
        self.assertEqual(state.current_quantities, [1])
        state.increment_quantity(0)
        self.assertEqual(state.current_quantities, [2])
        
    def test_reset_quantities(self):
        """Test resetting quantities (e.g. after emptying a bucket)."""
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        config = BucketConfig((BucketCriteria(eval1, 10),))
        state = Bucket(config)
        state.increment_quantity(0)
        state.reset_quantities()
        self.assertEqual(state.current_quantities, [0])

    def test_evaluate_full(self):
        """
        REQ-2: Manage Capacity.
        Test that a bucket stops matching once it reaches its required quantity.
        This is the core mechanism for capacity management.
        """
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        config = BucketConfig((BucketCriteria(eval1, 1),))
        state = Bucket(config)
        
        # Use real RbColour object
        from lego_sorter.rb_colour import RbColour
        mock_col = RbColour(1, "Blue", False)
        
        # Should match initially
        spec, idx = state.evaluate(None, mock_col)
        self.assertEqual(idx, 0)
        
        # Fill it to capacity
        state.increment_quantity(0)
        
        # Should NOT match anymore because it's full.
        spec, idx = state.evaluate(None, mock_col)
        self.assertEqual(idx, -1)


class TestLayer(unittest.TestCase):
    """Test cases for Layer class."""
    
    def test_initialization(self):
        """Test Layer initialization."""
        layer = Layer()
        self.assertEqual(len(layer.buckets), 16)
        for i in range(1, 17):
            self.assertIsInstance(layer.get_bucket(i), Bucket)
    
    def test_set_bucket(self):
        """Test setting buckets in a layer."""
        layer = Layer()
        config1 = BucketConfig((BucketCriteria(CriteriaEvaluator("RB_COL = Red")),))
        
        layer.set_bucket(1, config1)
        
        self.assertEqual(layer.get_bucket(1).config, config1)
    
    def test_set_bucket_invalid_position(self):
        """Test that setting bucket with invalid position raises error."""
        layer = Layer()
        config = BucketConfig()
        
        with self.assertRaises(ValueError):
            layer.set_bucket(0, config)
        with self.assertRaises(ValueError):
            layer.set_bucket(17, config)
    
    def test_equality(self):
        """Test Layer equality."""
        layer1 = Layer()
        layer2 = Layer()
        config = BucketConfig((BucketCriteria(CriteriaEvaluator("RB_COL = Red")),))
        
        layer1.set_bucket(1, config)
        layer2.set_bucket(1, config)
        
        self.assertEqual(layer1, layer2)
        
        layer2.set_bucket(2, config)
        self.assertNotEqual(layer1, layer2) 


class TestLayerCake(unittest.TestCase):
    """Test cases for LayerCake class."""
    
    def test_initialization(self):
        """Test LayerCake initialization."""
        cake = LayerCake()
        self.assertEqual(len(cake.layer_cake), 0)
        self.assertEqual(cake.layer_count(), 0)
    
    def test_add_layer(self):
        """Test adding layers to layer cake."""
        cake = LayerCake()
        layer1 = Layer()
        layer2 = Layer()
        
        cake.add_layer(layer1)
        cake.add_layer(layer2)
        
        self.assertEqual(cake.layer_count(), 2)
        self.assertEqual(cake.get_layer(0), layer1)
        self.assertEqual(cake.get_layer(1), layer2)
    
    def test_get_layer(self):
        """Test getting layers from layer cake."""
        cake = LayerCake()
        layer = Layer()
        cake.add_layer(layer)
        
        self.assertEqual(cake.get_layer(0), layer)
        
        with self.assertRaises(IndexError):
            cake.get_layer(1)
    
    def test_equality(self):
        """Test LayerCake equality."""
        cake1 = LayerCake()
        cake2 = LayerCake()
        layer = Layer()
        
        cake1.add_layer(layer)
        cake2.add_layer(layer)
        
        self.assertEqual(cake1, cake2)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_complete_sorting_machine(self):
        """Test creating a complete sorting machine with layers, buckets, and criteria."""
        # Create layer cake
        cake = LayerCake()
        
        # Create first layer with some buckets
        layer1 = Layer()
        
        # Bucket 1 with multiple criteria
        criteria = (
            BucketCriteria(CriteriaEvaluator("RB_COL = Red")),
            BucketCriteria(CriteriaEvaluator("RB_PT = 3001"))
        )
        config1 = BucketConfig(criteria)
        layer1.set_bucket(1, config1)
        
        # Bucket 5 with single criteria
        config2 = BucketConfig((BucketCriteria(CriteriaEvaluator("RB_COL = Blue")),))
        layer1.set_bucket(5, config2)
        
        # Add layer to cake
        cake.add_layer(layer1)
        
        # Create second layer
        layer2 = Layer()
        config3 = BucketConfig((BucketCriteria(CriteriaEvaluator("RB_COL = Green")),))
        layer2.set_bucket(3, config3)
        cake.add_layer(layer2)
        
        # Verify structure
        self.assertEqual(cake.layer_count(), 2)
        self.assertEqual(len(cake.get_layer(0).get_bucket(1).config.criteria), 2)
        self.assertEqual(cake.get_layer(0).get_bucket(5).config.criteria[0].evaluator.expression, "RB_COL = Blue")
        self.assertEqual(cake.get_layer(1).get_bucket(3).config.criteria[0].evaluator.expression, "RB_COL = Green")

    def test_from_json(self):
        """Test loading LayerCake from JSON."""
        json_content = [
            {
                "1": [
                    {"expression": "RB_COL = Red", "required": 10},
                    {"expression": "RB_PT = 3001", "required": 20}
                ],
                "5": [
                    {"expression": "RB_COL = Blue"}
                ]
            },
            {
                "3": [
                    {"expression": "RB_COL = Green", "required": 5}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(json_content, tmp)
            tmp_path = tmp.name
            
        try:
            cake = LayerCake.from_json(tmp_path)
            
            self.assertEqual(cake.layer_count(), 2)
            
            # Layer 0
            layer0 = cake.get_layer(0)
            bucket1 = layer0.get_bucket(1)
            self.assertEqual(len(bucket1.config.criteria), 2)
            self.assertEqual(bucket1.config.criteria[0].evaluator.expression, "RB_COL = Red")
            self.assertEqual(bucket1.config.criteria[0].required_quantity, 10)
            self.assertEqual(bucket1.config.criteria[1].evaluator.expression, "RB_PT = 3001")
            self.assertEqual(bucket1.config.criteria[1].required_quantity, 20)
            self.assertTrue(bucket1.config.allow_extension) # Should be True by default
            
            bucket5 = layer0.get_bucket(5)
            self.assertEqual(len(bucket5.config.criteria), 1)
            self.assertEqual(bucket5.config.criteria[0].evaluator.expression, "RB_COL = Blue")
            self.assertTrue(bucket5.config.allow_extension) # Should be True by default
            
            # Layer 1
            layer1 = cake.get_layer(1)
            bucket3 = layer1.get_bucket(3)
            self.assertEqual(len(bucket3.config.criteria), 1)
            self.assertEqual(bucket3.config.criteria[0].evaluator.expression, "RB_COL = Green")
            self.assertEqual(bucket3.config.criteria[0].required_quantity, 5)
            self.assertTrue(bucket3.config.allow_extension) # Should be True by default
            
        finally:
            os.remove(tmp_path)

    def test_from_json_multiple_buckets(self):
        json_content = [
            {
                "1, 2": [
                    {"expression": "RB_COL = Red", "required": 10}
                ],
                "3": [
                    {"expression": "RB_COL = Blue"}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(json_content, tmp)
            tmp_path = tmp.name
            
        try:
            cake = LayerCake.from_json(tmp_path)
            
            self.assertEqual(cake.layer_count(), 1)
            layer0 = cake.get_layer(0)
            
            # Check bucket 1
            bucket1 = layer0.get_bucket(1)
            self.assertIsNotNone(bucket1)
            self.assertEqual(bucket1.config.criteria[0].evaluator.expression, "RB_COL = Red")
            
            # Check bucket 2 (should be same config as 1 but distinct state object)
            bucket2 = layer0.get_bucket(2)
            self.assertIsNotNone(bucket2)
            self.assertEqual(bucket2.config.criteria[0].evaluator.expression, "RB_COL = Red")
            self.assertIsNot(bucket1, bucket2) # Should be distinct state objects
            
            # Verify independence
            bucket1.increment_quantity(0)
            self.assertEqual(bucket1.current_quantities[0], 1)
            self.assertEqual(bucket2.current_quantities[0], 0)
            
            # Check bucket 3
            bucket3 = layer0.get_bucket(3)
            self.assertIsNotNone(bucket3)
            self.assertEqual(bucket3.config.criteria[0].evaluator.expression, "RB_COL = Blue")
            
        finally:
            os.remove(tmp_path)

    def test_from_json_with_directives(self):
        """Test loading LayerCake from JSON with extension directives."""
        json_content = [
            {
                "1": {
                    "available_for_extension": True
                },
                "2": {
                    "allow_extension": True,
                    "criteria": ["RB_COL = Blue"]
                },
                "3": [
                    {"expression": "RB_COL = Red"}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(json_content, tmp)
            tmp_path = tmp.name
            
        try:
            cake = LayerCake.from_json(tmp_path)
            
            layer0 = cake.get_layer(0)
            
            # Bucket 1: available_for_extension
            bucket1 = layer0.get_bucket(1)
            self.assertTrue(bucket1.config.available_for_extension)
            self.assertFalse(bucket1.config.allow_extension)
            self.assertEqual(len(bucket1.config.criteria), 0)
            
            # Bucket 2: allow_extension
            bucket2 = layer0.get_bucket(2)
            self.assertTrue(bucket2.config.allow_extension)
            self.assertFalse(bucket2.config.available_for_extension)
            self.assertEqual(len(bucket2.config.criteria), 1)
            self.assertEqual(bucket2.config.criteria[0].evaluator.expression, "RB_COL = Blue")
            
            # Bucket 3: criteria (shorthand)
            bucket3 = layer0.get_bucket(3)
            self.assertEqual(len(bucket3.config.criteria), 1)
            self.assertEqual(bucket3.config.criteria[0].evaluator.expression, "RB_COL = Red")
            
        finally:
            os.remove(tmp_path)

    def test_disabled_bucket_skipped(self):
        """
        REQ-4: Support Maintenance.
        Test that disabled buckets are skipped during find_best_bucket.
        This allows operators to disable buckets for emptying without stopping the machine.
        """
        cake = LayerCake()
        layer = Layer()
        
        # Bucket 1: Very specific (Red AND 3001)
        config1 = BucketConfig((BucketCriteria(CriteriaEvaluator("RB_COL = Red AND RB_PT = 3001")),))
        layer.set_bucket(1, config1)
        
        # Bucket 2: Less specific (Just Red)
        config2 = BucketConfig((BucketCriteria(CriteriaEvaluator("RB_COL = Red")),))
        layer.set_bucket(2, config2)
        
        cake.add_layer(layer)
        
        # Red is ID 4 in colors.csv
        # Initially, bucket 1 should be chosen (higher specificity)
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertEqual(b_id, 1)
        self.assertEqual(status, SortingStatus.MATCH)
        
        # Disable bucket 1 (e.g. it's being emptied)
        cake.get_layer(0).get_bucket(1).enabled = False
        
        # Now it should pick bucket 2 (next best match) because fallback is allowed by default.
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertEqual(b_id, 2)
        self.assertEqual(status, SortingStatus.MATCH)
        
        # Disable bucket 2
        cake.get_layer(0).get_bucket(2).enabled = False
        
        # Now it should return NO_MATCH because no enabled buckets match.
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertIsNone(b_id)
        self.assertEqual(status, SortingStatus.NO_MATCH)

    def test_bucket_extension(self):
        """
        REQ-3: Handle Dynamic Extensions.
        Test that a bucket extends to an available_for_extension bucket when complete.
        This allows the machine to dynamically allocate more capacity for high-volume parts.
        """
        cake = LayerCake()
        layer = Layer()
        
        # Bucket 1: Red, required 1, allow_extension True
        eval1 = CriteriaEvaluator("RB_COL = Red")
        crit1 = BucketCriteria(eval1, 1)
        config1 = BucketConfig(criteria=(crit1,), allow_extension=True)
        layer.set_bucket(1, config1)
        
        # Bucket 2: Placeholder (available for extension)
        config2 = BucketConfig(available_for_extension=True)
        layer.set_bucket(2, config2)
        
        cake.add_layer(layer)
        
        # Red is ID 4
        # First part: goes to bucket 1
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertEqual(b_id, 1)
        self.assertEqual(status, SortingStatus.MATCH)
        
        # Bucket 1 should now be complete, and bucket 2 should have its config copied over.
        bucket1 = cake.get_layer(0).get_bucket(1)
        bucket2 = cake.get_layer(0).get_bucket(2)
        
        self.assertTrue(bucket1.is_complete)
        self.assertEqual(bucket2.config.criteria[0].evaluator.expression, "RB_COL = Red")
        self.assertFalse(bucket2.config.available_for_extension)
        
        # Second part: should go to bucket 2 because bucket 1 is full.
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertEqual(b_id, 2)
        self.assertEqual(status, SortingStatus.MATCH)
        self.assertEqual(bucket2.current_quantities[0], 1)

    def test_allow_fallback_if_disabled(self):
        """
        REQ-4: Support Maintenance.
        Test the allow_fallback_if_disabled configuration.
        This allows operators to decide if a part should be rejected or sent to a 
        less specific bucket when the primary bucket is disabled.
        """
        cake = LayerCake()
        layer = Layer()
        
        # Bucket 1: Specific (Red), allow_fallback_if_disabled=False
        config1 = BucketConfig(
            criteria=(BucketCriteria(CriteriaEvaluator("RB_COL = Red")),),
            allow_fallback_if_disabled=False
        )
        layer.set_bucket(1, config1)
        
        # Bucket 2: General (Any), allow_fallback_if_disabled=True
        config2 = BucketConfig(
            criteria=(BucketCriteria(CriteriaEvaluator("RB_COL != 999")),),
            allow_fallback_if_disabled=True
        )
        layer.set_bucket(2, config2)
        
        cake.add_layer(layer)
        
        # Red is ID 4
        # Initially, bucket 1 is chosen
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertEqual(b_id, 1)
        self.assertEqual(status, SortingStatus.MATCH)
        
        # Disable bucket 1
        cake.get_layer(0).get_bucket(1).enabled = False
        
        # Now it should return DISABLED_REJECTED because bucket 1 is the best match 
        # but doesn't allow fallback. We don't want Red pieces going into the 'Any' bucket.
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertIsNone(b_id)
        self.assertEqual(status, SortingStatus.DISABLED_REJECTED)
        
        # Enable bucket 1, but change config to allow fallback
        cake.get_layer(0).get_bucket(1).enabled = True
        config1_new = BucketConfig(
            criteria=(BucketCriteria(CriteriaEvaluator("RB_COL = Red")),),
            allow_fallback_if_disabled=True
        )
        cake.get_layer(0).set_bucket(1, config1_new)
        cake.get_layer(0).get_bucket(1).enabled = False
        
        # Now it should fallback to bucket 2 because fallback is now allowed.
        l_num, b_id, status = cake.find_best_bucket("3001", 4)
        self.assertEqual(b_id, 2)
        self.assertEqual(status, SortingStatus.MATCH)

    def test_sorting_status_codes(self):
        """
        REQ-1, REQ-4.
        Test that find_best_bucket returns correct status codes for different scenarios.
        This ensures the caller can react appropriately to different sorting outcomes.
        """
        cake = LayerCake()
        layer = Layer()
        
        # Bucket 1: Red only, no fallback
        config1 = BucketConfig(
            criteria=(BucketCriteria(CriteriaEvaluator("RB_COL = Red")),),
            allow_fallback_if_disabled=False
        )
        layer.set_bucket(1, config1)
        cake.add_layer(layer)
        
        # Scenario 1: Match (Red piece)
        _, _, status = cake.find_best_bucket("3001", 4) # Red
        self.assertEqual(status, SortingStatus.MATCH)
        
        # Scenario 2: No Match (Blue piece, no blue bucket)
        _, _, status = cake.find_best_bucket("3001", 1) # Blue
        self.assertEqual(status, SortingStatus.NO_MATCH)
        
        # Scenario 3: Disabled Rejected (Red piece, but red bucket is disabled and fallback forbidden)
        cake.get_layer(0).get_bucket(1).enabled = False
        _, _, status = cake.find_best_bucket("3001", 4) # Red
        self.assertEqual(status, SortingStatus.DISABLED_REJECTED)

    def test_bucket_name_and_summarize(self):
        """Test that bucket names are parsed and the machine state can be summarized."""
        json_content = [
            {
                "1": {
                    "name": "Red Bricks",
                    "criteria": ["RB_COL = Red"]
                },
                "16": {
                    "name": "Overflow",
                    "available_for_extension": True
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(json_content, tmp)
            tmp_path = tmp.name
            
        try:
            cake = LayerCake.from_json(tmp_path)
            
            # Verify names
            self.assertEqual(cake.get_layer(0).get_bucket(1).config.name, "Red Bricks")
            self.assertEqual(cake.get_layer(0).get_bucket(16).config.name, "Overflow")
            
            # Verify summarize
            summary_json = cake.summarize()
            summary = json.loads(summary_json)
            
            self.assertEqual(len(summary), 1) # 1 layer
            self.assertEqual(summary[0]["1"]["config"]["name"], "Red Bricks")
            self.assertEqual(summary[0]["16"]["config"]["name"], "Overflow")
            self.assertEqual(summary[0]["1"]["current_quantities"], [0])
            self.assertTrue(summary[0]["1"]["enabled"])
            
        finally:
            os.remove(tmp_path)

    def test_from_json_duplicate_buckets(self):
        json_content = [
            {
                "1, 2": [
                    {"expression": "RB_COL = Red"}
                ],
                "2": [ # Duplicate definition of bucket 2
                    {"expression": "RB_COL = Blue"}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(json_content, tmp)
            tmp_path = tmp.name
            
        try:
            with self.assertRaises(ValueError) as cm:
                LayerCake.from_json(tmp_path)
            self.assertIn("Bucket position 2 defined multiple times", str(cm.exception))
        finally:
            os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
