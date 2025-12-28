"""Tests for the lego_sorter package."""

import unittest

from lego_sorter import LegoCriteria, BucketConfig, Bucket, Layer, SortingMachine


class TestLegoCriteria(unittest.TestCase):
    """Test cases for LegoCriteria class."""
    
    def test_initialization(self):
        """Test LegoCriteria initialization."""
        criteria = LegoCriteria(42, "test_string")
        self.assertEqual(criteria.number, 42)
        self.assertEqual(criteria.string, "test_string")
    
    def test_equality(self):
        """Test LegoCriteria equality."""
        criteria1 = LegoCriteria(1, "a")
        criteria2 = LegoCriteria(1, "a")
        criteria3 = LegoCriteria(2, "b")
        
        self.assertEqual(criteria1, criteria2)
        self.assertNotEqual(criteria1, criteria3)
    
    def test_repr(self):
        """Test LegoCriteria representation."""
        criteria = LegoCriteria(10, "value")
        self.assertEqual(repr(criteria), "LegoCriteria(number=10, string='value')")


class TestBucketConfig(unittest.TestCase):
    """Test cases for BucketConfig class."""
    
    def test_initialization_empty(self):
        """Test BucketConfig initialization with no criteria."""
        config = BucketConfig()
        self.assertEqual(len(config.criteria), 0)
    
    def test_initialization_with_criteria(self):
        """Test BucketConfig initialization with criteria list."""
        criteria_list = [LegoCriteria(1, "a"), LegoCriteria(2, "b")]
        config = BucketConfig(criteria_list)
        self.assertEqual(len(config.criteria), 2)
        self.assertEqual(config.criteria[0], LegoCriteria(1, "a"))
    
    def test_add_criteria(self):
        """Test adding criteria to BucketConfig."""
        config = BucketConfig()
        criteria = LegoCriteria(5, "test")
        config.add_criteria(criteria)
        self.assertEqual(len(config.criteria), 1)
        self.assertEqual(config.criteria[0], criteria)
    
    def test_equality(self):
        """Test BucketConfig equality."""
        config1 = BucketConfig([LegoCriteria(1, "a")])
        config2 = BucketConfig([LegoCriteria(1, "a")])
        config3 = BucketConfig([LegoCriteria(2, "b")])
        
        self.assertEqual(config1, config2)
        self.assertNotEqual(config1, config3)


class TestBucket(unittest.TestCase):
    """Test cases for Bucket class."""
    
    def test_initialization(self):
        """Test Bucket initialization."""
        config = BucketConfig([LegoCriteria(1, "a")])
        bucket = Bucket(5, config)
        self.assertEqual(bucket.position, 5)
        self.assertEqual(bucket.config, config)
    
    def test_initialization_no_config(self):
        """Test Bucket initialization without config."""
        bucket = Bucket(10)
        self.assertEqual(bucket.position, 10)
        self.assertIsInstance(bucket.config, BucketConfig)
        self.assertEqual(len(bucket.config.criteria), 0)
    
    def test_position_validation(self):
        """Test Bucket position validation."""
        # Valid positions
        Bucket(1)
        Bucket(16)
        Bucket(8)
        
        # Invalid positions
        with self.assertRaises(ValueError):
            Bucket(0)
        with self.assertRaises(ValueError):
            Bucket(17)
        with self.assertRaises(ValueError):
            Bucket(-1)
    
    def test_equality(self):
        """Test Bucket equality."""
        config = BucketConfig([LegoCriteria(1, "a")])
        bucket1 = Bucket(5, config)
        bucket2 = Bucket(5, BucketConfig([LegoCriteria(1, "a")]))
        bucket3 = Bucket(6, config)
        
        self.assertEqual(bucket1, bucket2)
        self.assertNotEqual(bucket1, bucket3)


class TestLayer(unittest.TestCase):
    """Test cases for Layer class."""
    
    def test_initialization(self):
        """Test Layer initialization."""
        layer = Layer()
        self.assertEqual(len(layer.buckets), 0)
    
    def test_add_bucket(self):
        """Test adding buckets to a layer."""
        layer = Layer()
        bucket1 = Bucket(1)
        bucket2 = Bucket(5)
        
        layer.add_bucket(bucket1)
        layer.add_bucket(bucket2)
        
        self.assertEqual(len(layer.buckets), 2)
        self.assertEqual(layer.get_bucket(1), bucket1)
        self.assertEqual(layer.get_bucket(5), bucket2)
    
    def test_add_bucket_duplicate_position(self):
        """Test that adding bucket to occupied position raises error."""
        layer = Layer()
        bucket1 = Bucket(1)
        bucket2 = Bucket(1)
        
        layer.add_bucket(bucket1)
        with self.assertRaises(ValueError):
            layer.add_bucket(bucket2)
    
    def test_get_bucket(self):
        """Test getting buckets from layer."""
        layer = Layer()
        bucket = Bucket(10)
        layer.add_bucket(bucket)
        
        self.assertEqual(layer.get_bucket(10), bucket)
        self.assertIsNone(layer.get_bucket(5))
    
    def test_remove_bucket(self):
        """Test removing buckets from layer."""
        layer = Layer()
        bucket = Bucket(3)
        layer.add_bucket(bucket)
        
        removed = layer.remove_bucket(3)
        self.assertEqual(removed, bucket)
        self.assertIsNone(layer.get_bucket(3))
        
        # Remove non-existent bucket
        self.assertIsNone(layer.remove_bucket(5))
    
    def test_equality(self):
        """Test Layer equality."""
        layer1 = Layer()
        layer2 = Layer()
        layer1.add_bucket(Bucket(1))
        layer2.add_bucket(Bucket(1))
        
        self.assertEqual(layer1, layer2)
        
        layer2.add_bucket(Bucket(2))
        self.assertNotEqual(layer1, layer2)


class TestSortingMachine(unittest.TestCase):
    """Test cases for SortingMachine class."""
    
    def test_initialization(self):
        """Test SortingMachine initialization."""
        machine = SortingMachine()
        self.assertEqual(len(machine.layers), 0)
        self.assertEqual(machine.layer_count(), 0)
    
    def test_add_layer(self):
        """Test adding layers to sorting machine."""
        machine = SortingMachine()
        layer1 = Layer()
        layer2 = Layer()
        
        machine.add_layer(layer1)
        machine.add_layer(layer2)
        
        self.assertEqual(machine.layer_count(), 2)
        self.assertEqual(machine.get_layer(0), layer1)
        self.assertEqual(machine.get_layer(1), layer2)
    
    def test_get_layer(self):
        """Test getting layers from sorting machine."""
        machine = SortingMachine()
        layer = Layer()
        machine.add_layer(layer)
        
        self.assertEqual(machine.get_layer(0), layer)
        
        with self.assertRaises(IndexError):
            machine.get_layer(1)
    
    def test_remove_layer(self):
        """Test removing layers from sorting machine."""
        machine = SortingMachine()
        layer1 = Layer()
        layer2 = Layer()
        machine.add_layer(layer1)
        machine.add_layer(layer2)
        
        removed = machine.remove_layer(0)
        self.assertEqual(removed, layer1)
        self.assertEqual(machine.layer_count(), 1)
        self.assertEqual(machine.get_layer(0), layer2)
    
    def test_equality(self):
        """Test SortingMachine equality."""
        machine1 = SortingMachine()
        machine2 = SortingMachine()
        layer = Layer()
        
        machine1.add_layer(layer)
        machine2.add_layer(Layer())
        
        self.assertEqual(machine1, machine2)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_complete_sorting_machine(self):
        """Test creating a complete sorting machine with layers, buckets, and criteria."""
        # Create sorting machine
        machine = SortingMachine()
        
        # Create first layer with some buckets
        layer1 = Layer()
        
        # Bucket 1 with multiple criteria
        config1 = BucketConfig()
        config1.add_criteria(LegoCriteria(1, "red"))
        config1.add_criteria(LegoCriteria(2, "brick"))
        bucket1 = Bucket(1, config1)
        layer1.add_bucket(bucket1)
        
        # Bucket 5 with single criteria
        config2 = BucketConfig([LegoCriteria(10, "blue")])
        bucket2 = Bucket(5, config2)
        layer1.add_bucket(bucket2)
        
        # Add layer to machine
        machine.add_layer(layer1)
        
        # Create second layer
        layer2 = Layer()
        bucket3 = Bucket(3, BucketConfig([LegoCriteria(20, "green")]))
        layer2.add_bucket(bucket3)
        machine.add_layer(layer2)
        
        # Verify structure
        self.assertEqual(machine.layer_count(), 2)
        self.assertEqual(machine.get_layer(0).get_bucket(1).position, 1)
        self.assertEqual(len(machine.get_layer(0).get_bucket(1).config.criteria), 2)
        self.assertEqual(machine.get_layer(0).get_bucket(5).config.criteria[0].string, "blue")
        self.assertEqual(machine.get_layer(1).get_bucket(3).config.criteria[0].number, 20)


if __name__ == '__main__':
    unittest.main()
