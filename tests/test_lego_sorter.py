"""Tests for the lego_sorter package."""

import unittest
import json
import tempfile
import os

from lego_sorter import BucketConfig, Layer, LayerCake, CriteriaEvaluator


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
        # Tuple: (Evaluator, Required, Current)
        criteria_list = [(eval1, 10, 0), (eval2, None, 0)]
        config = BucketConfig(criteria_list)
        self.assertEqual(len(config.criteria), 2)
        self.assertEqual(config.criteria[0][0].expression, "RB_COL = Blue")
        self.assertEqual(config.criteria[0][1], 10)
        self.assertEqual(config.criteria[0][2], 0)
    
    def test_add_criteria(self):
        """Test adding criteria to BucketConfig."""
        config = BucketConfig()
        evaluator = CriteriaEvaluator("RB_COL = Red")
        config.add_criteria(evaluator, required_quantity=5)
        self.assertEqual(len(config.criteria), 1)
        self.assertEqual(config.criteria[0][0].expression, "RB_COL = Red")
        self.assertEqual(config.criteria[0][1], 5)
        self.assertEqual(config.criteria[0][2], 0)
    
    def test_equality(self):
        """Test BucketConfig equality."""
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        eval2 = CriteriaEvaluator("RB_COL = Blue")
        eval3 = CriteriaEvaluator("RB_COL = Red")
        
        config1 = BucketConfig([(eval1, 10, 0)])
        config2 = BucketConfig([(eval2, 10, 0)])
        config3 = BucketConfig([(eval3, 10, 0)])
        
        self.assertEqual(config1, config2)
        self.assertNotEqual(config1, config3)
    
    def test_update_current_quantity(self):
        """Test updating the current quantity."""
        config = BucketConfig()
        evaluator = CriteriaEvaluator("RB_COL = Blue")
        config.add_criteria(evaluator, required_quantity=10)
        
        # Initial state
        self.assertEqual(config.criteria[0][2], 0)
        
        # Update quantity
        config.update_current_quantity(0, 5)
        self.assertEqual(config.criteria[0][2], 5)
        
        # Update again
        config.update_current_quantity(0, 8)
        self.assertEqual(config.criteria[0][2], 8)
        
        # Test invalid index
        with self.assertRaises(IndexError):
            config.update_current_quantity(1, 5)
        with self.assertRaises(IndexError):
            config.update_current_quantity(-1, 5)

    def test_increment_quantity(self):
        """Test incrementing the current quantity."""
        config = BucketConfig()
        evaluator = CriteriaEvaluator("RB_COL = Blue")
        config.add_criteria(evaluator, required_quantity=10)
        
        # Initial state
        self.assertEqual(config.criteria[0][2], 0)
        
        # Increment
        config.increment_quantity(0)
        self.assertEqual(config.criteria[0][2], 1)
        
        # Increment again
        config.increment_quantity(0)
        self.assertEqual(config.criteria[0][2], 2)
        
        # Test invalid index
        with self.assertRaises(IndexError):
            config.increment_quantity(1)

    def test_reset_quantities(self):
        """Test resetting all quantities."""
        config = BucketConfig()
        eval1 = CriteriaEvaluator("RB_COL = Blue")
        eval2 = CriteriaEvaluator("RB_COL = Red")
        config.add_criteria(eval1, required_quantity=10)
        config.add_criteria(eval2, required_quantity=5)
        
        # Set some quantities
        config.update_current_quantity(0, 5)
        config.update_current_quantity(1, 3)
        
        self.assertEqual(config.criteria[0][2], 5)
        self.assertEqual(config.criteria[1][2], 3)
        
        # Reset
        config.reset_quantities()
        
        self.assertEqual(config.criteria[0][2], 0)
        self.assertEqual(config.criteria[1][2], 0)
        # Ensure other fields are preserved
        self.assertEqual(config.criteria[0][0], eval1)
        self.assertEqual(config.criteria[0][1], 10)


class TestLayer(unittest.TestCase):
    """Test cases for Layer class."""
    
    def test_initialization(self):
        """Test Layer initialization."""
        layer = Layer()
        self.assertEqual(len(layer.buckets), 0)
    
    def test_set_bucket(self):
        """Test setting buckets in a layer."""
        layer = Layer()
        config1 = BucketConfig()
        config2 = BucketConfig()
        
        layer.set_bucket(1, config1)
        layer.set_bucket(5, config2)
        
        self.assertEqual(len(layer.buckets), 2)
        self.assertEqual(layer.get_bucket(1), config1)
        self.assertEqual(layer.get_bucket(5), config2)
    
    def test_set_bucket_invalid_position(self):
        """Test that setting bucket with invalid position raises error."""
        layer = Layer()
        config = BucketConfig()
        
        with self.assertRaises(ValueError):
            layer.set_bucket(0, config)
        with self.assertRaises(ValueError):
            layer.set_bucket(17, config)
    
    def test_get_bucket(self):
        """Test getting buckets from layer."""
        layer = Layer()
        config = BucketConfig()
        layer.set_bucket(10, config)
        
        self.assertEqual(layer.get_bucket(10), config)
        self.assertIsNone(layer.get_bucket(5))
    
    def test_remove_bucket(self):
        """Test removing buckets from layer."""
        layer = Layer()
        config = BucketConfig()
        layer.set_bucket(3, config)
        
        removed = layer.remove_bucket(3)
        self.assertEqual(removed, config)
        self.assertIsNone(layer.get_bucket(3))
        
        # Remove non-existent bucket
        self.assertIsNone(layer.remove_bucket(5))
    
    def test_equality(self):
        """Test Layer equality."""
        layer1 = Layer()
        layer2 = Layer()
        config = BucketConfig()
        
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
    
    def test_remove_layer(self):
        """Test removing layers from layer cake."""
        cake = LayerCake()
        layer1 = Layer()
        layer2 = Layer()
        cake.add_layer(layer1)
        cake.add_layer(layer2)
        
        removed = cake.remove_layer(0)
        self.assertEqual(removed, layer1)
        self.assertEqual(cake.layer_count(), 1)
        self.assertEqual(cake.get_layer(0), layer2)
    
    def test_equality(self):
        """Test LayerCake equality."""
        cake1 = LayerCake()
        cake2 = LayerCake()
        layer = Layer()
        
        cake1.add_layer(layer)
        cake2.add_layer(Layer())
        
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
        config1 = BucketConfig()
        config1.add_criteria(CriteriaEvaluator("RB_COL = Red"))
        config1.add_criteria(CriteriaEvaluator("RB_PT = 3001"))
        layer1.set_bucket(1, config1)
        
        # Bucket 5 with single criteria
        config2 = BucketConfig([(CriteriaEvaluator("RB_COL = Blue"), None, 0)])
        layer1.set_bucket(5, config2)
        
        # Add layer to cake
        cake.add_layer(layer1)
        
        # Create second layer
        layer2 = Layer()
        config3 = BucketConfig([(CriteriaEvaluator("RB_COL = Green"), None, 0)])
        layer2.set_bucket(3, config3)
        cake.add_layer(layer2)
        
        # Verify structure
        self.assertEqual(cake.layer_count(), 2)
        # get_bucket now returns BucketConfig directly
        self.assertEqual(len(cake.get_layer(0).get_bucket(1).criteria), 2)
        self.assertEqual(cake.get_layer(0).get_bucket(5).criteria[0][0].expression, "RB_COL = Blue")
        self.assertEqual(cake.get_layer(1).get_bucket(3).criteria[0][0].expression, "RB_COL = Green")

    def test_from_json(self):
        """Test loading LayerCake from JSON."""
        import json
        import tempfile
        import os
        
        json_content = [
            {
                "1": [
                    {"expression": "RB_COL = Red", "required": 10},
                    {"expression": "RB_PT = 3001"}
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
            self.assertEqual(len(bucket1.criteria), 2)
            self.assertEqual(bucket1.criteria[0][0].expression, "RB_COL = Red")
            self.assertEqual(bucket1.criteria[0][1], 10)
            self.assertEqual(bucket1.criteria[1][0].expression, "RB_PT = 3001")
            self.assertIsNone(bucket1.criteria[1][1])
            
            bucket5 = layer0.get_bucket(5)
            self.assertEqual(len(bucket5.criteria), 1)
            self.assertEqual(bucket5.criteria[0][0].expression, "RB_COL = Blue")
            
            # Layer 1
            layer1 = cake.get_layer(1)
            bucket3 = layer1.get_bucket(3)
            self.assertEqual(len(bucket3.criteria), 1)
            self.assertEqual(bucket3.criteria[0][0].expression, "RB_COL = Green")
            self.assertEqual(bucket3.criteria[0][1], 5)
            
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
            self.assertEqual(bucket1.criteria[0][0].expression, "RB_COL = Red")
            
            # Check bucket 2 (should be same config as 1 but distinct object)
            bucket2 = layer0.get_bucket(2)
            self.assertIsNotNone(bucket2)
            self.assertEqual(bucket2.criteria[0][0].expression, "RB_COL = Red")
            self.assertIsNot(bucket1, bucket2) # Should be distinct objects
            
            # Verify independence
            bucket1.increment_quantity(0)
            self.assertEqual(bucket1.criteria[0][2], 1)
            self.assertEqual(bucket2.criteria[0][2], 0)
            
            # Check bucket 3
            bucket3 = layer0.get_bucket(3)
            self.assertIsNotNone(bucket3)
            self.assertEqual(bucket3.criteria[0][0].expression, "RB_COL = Blue")
            
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
