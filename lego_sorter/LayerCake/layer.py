"""Layer class for representing a layer of buckets."""

import json
from typing import Dict, List, Optional, Union
from .bucket_config import BucketConfig
from .criteria_evaluator import CriteriaEvaluator


class Layer:
    """A layer containing buckets at positions 1 to 16."""
    
    def __init__(self):
        """Initialize a Layer with empty bucket positions."""
        self.buckets: Dict[int, BucketConfig] = {}
    
    def set_bucket(self, position: int, config: BucketConfig):
        """Set a bucket configuration at a specific position.
        
        Args:
            position: Position of the bucket (1-16)
            config: BucketConfig object
        
        Raises:
            ValueError: If position is not between 1 and 16
        """
        if not 1 <= position <= 16:
            raise ValueError("Bucket position must be between 1 and 16")
        self.buckets[position] = config
    
    def get_bucket(self, position: int) -> Optional[BucketConfig]:
        """Get a bucket configuration at a specific position.
        
        Args:
            position: Position to retrieve (1-16)
        
        Returns:
            BucketConfig at the position, or None if no bucket exists
        """
        return self.buckets.get(position)
    
    def remove_bucket(self, position: int) -> Optional[BucketConfig]:
        """Remove a bucket configuration at a specific position.
        
        Args:
            position: Position to remove (1-16)
        
        Returns:
            Removed BucketConfig, or None if no bucket existed at that position
        """
        return self.buckets.pop(position, None)
    
    def __repr__(self):
        return f"Layer(buckets={self.buckets})"
    
    def __eq__(self, other):
        if not isinstance(other, Layer):
            return False
        return self.buckets == other.buckets


class LayerCake:
    """A collection of layers forming the sorting machine."""
    
    def __init__(self):
        """Initialize a LayerCake with no layers."""
        self.layer_cake: List[Layer] = []
    
    def add_layer(self, layer: Layer):
        """Add a layer to the layer cake.
        
        Args:
            layer: Layer object to add
        """
        self.layer_cake.append(layer)
    
    def get_layer(self, index: int) -> Layer:
        """Get a layer at a specific index.
        
        Args:
            index: Index of the layer (0-based)
        
        Returns:
            Layer at the specified index
        
        Raises:
            IndexError: If index is out of range
        """
        return self.layer_cake[index]
    
    def remove_layer(self, index: int) -> Layer:
        """Remove a layer at a specific index.
        
        Args:
            index: Index of the layer to remove (0-based)
        
        Returns:
            Removed layer
        
        Raises:
            IndexError: If index is out of range
        """
        return self.layer_cake.pop(index)
    
    def layer_count(self) -> int:
        """Get the number of layers in the layer cake.
        
        Returns:
            Number of layers
        """
        return len(self.layer_cake)
    
    @classmethod
    def from_json(cls, file_path: str) -> 'LayerCake':
        """
        Initialize a LayerCake from a JSON file.
        
        The JSON format should be a list of layers, where each layer is a dictionary
        mapping bucket positions (as strings) to a list of criteria objects.
        The keys can be single integers (e.g., "1") or comma-separated lists (e.g., "1, 2, 3").
        
        Example format:
        [
            {
                "1, 2": [
                    {"expression": "RB_COL = Red", "required": 10},
                    {"expression": "RB_PT = 3001"}
                ],
                "5": [ ... ]
            },
            ...
        ]
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            Initialized LayerCake object.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        cake = cls()
        
        for layer_data in data:
            layer = Layer()
            seen_positions = set()
            
            for pos_str, criteria_list_data in layer_data.items():
                # Parse positions (handle single int or comma-separated list)
                try:
                    positions = [int(p.strip()) for p in pos_str.split(',')]
                except ValueError:
                    # Handle case where key might not be a simple integer list
                    # For now, we assume valid input as per requirements
                    continue

                for position in positions:
                    if position in seen_positions:
                        raise ValueError(f"Bucket position {position} defined multiple times in the same layer.")
                    seen_positions.add(position)

                    config = BucketConfig()
                    
                    for criteria_data in criteria_list_data:
                        expression = criteria_data["expression"]
                        required = criteria_data.get("required") # None if missing
                        
                        evaluator = CriteriaEvaluator(expression)
                        config.add_criteria(evaluator, required_quantity=required)
                    
                    layer.set_bucket(position, config)
            cake.add_layer(layer)
            
        return cake

    def __eq__(self, other):
        if not isinstance(other, LayerCake):
            return False
        return self.layer_cake == other.layer_cake

