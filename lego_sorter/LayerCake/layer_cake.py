"""Layer class for representing a layer of buckets."""

import json
from typing import Dict, List, Optional, Tuple, Union
from .bucket_config import BucketConfig, BucketCriteria
from .bucket_state import Bucket
from .criteria_evaluator import CriteriaEvaluator
from ..rb_parts import RbParts
from ..rb_colour import RbColours


class Layer:
    """A layer containing buckets at positions 1 to 16."""
    
    def __init__(self):
        """Initialize a Layer with 16 empty buckets."""
        self.buckets: Dict[int, Bucket] = {i: Bucket() for i in range(1, 17)}
    
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
        self.buckets[position] = Bucket(config)
    
    def get_bucket(self, position: int) -> Bucket:
        """Get a bucket state at a specific position.
        
        Args:
            position: Position to retrieve (1-16)
        
        Returns:
            BucketState at the position
        """
        if not 1 <= position <= 16:
            raise ValueError("Bucket position must be between 1 and 16")
        return self.buckets[position]
    
    def __repr__(self):
        return f"Layer(buckets={self.buckets})"
    
    def __eq__(self, other):
        if not isinstance(other, Layer):
            return False
        return self.buckets == other.buckets

    def reset_quantities(self):
        """Reset current quantities for all buckets in this layer to 0."""
        for bucket in self.buckets.values():
            bucket.reset_quantities()


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
    
    def layer_count(self) -> int:
        """Get the number of layers in the layer cake.
        
        Returns:
            Number of layers
        """
        return len(self.layer_cake)
    
    def reset_quantities(self):
        """Reset all current quantities in the entire layer cake to 0."""
        for layer in self.layer_cake:
            layer.reset_quantities()
    
    def reset_layer_quantities(self, layer_num: int):
        """Reset current quantities for all buckets in a specific layer.
        
        Args:
            layer_num: 1-based layer number.
        """
        self.get_layer(layer_num - 1).reset_quantities()

    def reset_bucket_quantities(self, layer_num: int, bucket_id: int):
        """Reset current quantities for a specific bucket in a specific layer.
        
        Args:
            layer_num: 1-based layer number.
            bucket_id: 1-based bucket ID (1-16).
        """
        self.get_layer(layer_num - 1).get_bucket(bucket_id).reset_quantities()
    
    def find_best_bucket(self, part_num: str, color_id: Optional[int] = None) -> Tuple[Optional[int], Optional[int]]:
        """
        Find the most appropriate bucket for a given part and color.
        
        Args:
            part_num: Rebrickable part number.
            color_id: Optional Rebrickable color ID.
            
        Returns:
            A tuple of (layer_num, bucket_id), or (None, None) if no bucket matches.
            Layer number is 1-based, bucket ID is 1-16.
        """
        # Resolve part and color
        try:
            rb_part = RbParts(part_num)
        except ValueError:
            rb_part = None
            
        rb_col = None
        if color_id is not None:
            try:
                rb_col = RbColours(color_id)
            except ValueError:
                rb_col = color_id # Pass ID if object lookup fails, evaluator handles it

        best_layer_idx = None
        best_bucket_id = None
        best_criteria_idx = None
        max_specificity = -1

        # Iterate through all layers and buckets
        for l_idx, layer in enumerate(self.layer_cake):
            for b_id in range(1, 17):
                bucket = layer.get_bucket(b_id)
                
                # Skip disabled buckets
                if not bucket.enabled:
                    continue
                    
                specificity, criteria_idx = bucket.evaluate(rb_part, rb_col)
                
                if specificity > -1:
                    # Check if this bucket is better
                    # 1. Higher specificity
                    # 2. Same specificity but higher layer number (index)
                    if specificity > max_specificity:
                        max_specificity = specificity
                        best_layer_idx = l_idx
                        best_bucket_id = b_id
                        best_criteria_idx = criteria_idx
                    elif specificity == max_specificity:
                        # If specificity is equal, use the one with highest layer number
                        if l_idx > best_layer_idx:
                            best_layer_idx = l_idx
                            best_bucket_id = b_id
                            best_criteria_idx = criteria_idx
                        # If same layer and same specificity, we keep the first one found (lowest bucket ID)
                            
        if best_layer_idx is not None:
            best_bucket_state = self.layer_cake[best_layer_idx].get_bucket(best_bucket_id)
            best_bucket_state.increment_quantity(best_criteria_idx)
            
            # Check if bucket is now complete and needs extension
            if best_bucket_state.is_complete:
                self._handle_bucket_extension(best_bucket_state)
                
            return best_layer_idx + 1, best_bucket_id
            
        return None, None

    def _handle_bucket_extension(self, completed_bucket: Bucket):
        """
        Find an available extension bucket and copy the configuration.
        
        Args:
            completed_bucket: The bucket that has just been completed.
        """
        for layer in self.layer_cake:
            for b_id in range(1, 17):
                target_bucket = layer.get_bucket(b_id)
                if target_bucket.config.available_for_extension:
                    # Found a placeholder!
                    # Copy the config and reset state
                    target_bucket.config = completed_bucket.config
                    target_bucket.reset_quantities()
                    target_bucket.enabled = True
                    return # Only extend to one bucket

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

                    criteria_list = []
                    available_for_ext = False
                    allow_ext = False

                    if isinstance(criteria_list_data, list):
                        # Shorthand: just a list of criteria
                        for criteria_data in criteria_list_data:
                            if isinstance(criteria_data, str):
                                expression = criteria_data
                                required = None
                            else:
                                expression = criteria_data["expression"]
                                required = criteria_data.get("required")
                            evaluator = CriteriaEvaluator(expression)
                            criteria_list.append(BucketCriteria(evaluator, required))
                        allow_ext = None
                    elif isinstance(criteria_list_data, dict):
                        # Full object: can have directives and criteria
                        available_for_ext = criteria_list_data.get("available_for_extension", False)
                        allow_ext = criteria_list_data.get("allow_extension")
                        
                        raw_criteria = criteria_list_data.get("criteria", [])
                        for criteria_data in raw_criteria:
                            if isinstance(criteria_data, str):
                                expression = criteria_data
                                required = None
                            else:
                                expression = criteria_data["expression"]
                                required = criteria_data.get("required")
                            evaluator = CriteriaEvaluator(expression)
                            criteria_list.append(BucketCriteria(evaluator, required))
                    
                    config = BucketConfig(
                        criteria=tuple(criteria_list),
                        available_for_extension=available_for_ext,
                        allow_extension=allow_ext
                    )
                    layer.set_bucket(position, config)
            cake.add_layer(layer)
            
        return cake

    def __eq__(self, other):
        if not isinstance(other, LayerCake):
            return False
        return self.layer_cake == other.layer_cake

