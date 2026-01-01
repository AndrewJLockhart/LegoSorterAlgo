"""Layer class for representing a layer of buckets."""

import json
from enum import Enum
from typing import Dict, List, Optional, Tuple
from .bucket_config import BucketConfig, BucketCriteria
from .bucket_state import Bucket
from .criteria_evaluator import CriteriaEvaluator
from ..rb_parts import RbParts
from ..rb_colour import RbColours


class SortingStatus(Enum):
    """
    Status codes for sorting results.
    
    These codes allow the caller to distinguish between a successful match, 
    a complete lack of matching rules, and a rejection due to maintenance 
    (disabled bucket) with fallback disabled.
    """
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    DISABLED_REJECTED = "DISABLED_REJECTED"


class Layer:
    """
    A layer containing buckets at positions 1 to 16.
    
    A Layer represents a physical row or section of buckets in the sorting machine.
    """
    
    def __init__(self):
        """Initialize a Layer with 16 empty buckets."""
        self.buckets: Dict[int, Bucket] = {i: Bucket() for i in range(1, 17)}
    
    def set_bucket(self, position: int, config: BucketConfig):
        """Set a bucket configuration at a specific position.
        
        Args:
            position: Position of the bucket (1-16)
            config: BucketConfig object
        """
        if not 1 <= position <= 16:
            raise ValueError("Bucket position must be between 1 and 16")
        self.buckets[position] = Bucket(config)
    
    def get_bucket(self, position: int) -> Bucket:
        """Get a bucket state at a specific position."""
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

    def to_dict(self):
        """Convert layer state to a serializable dictionary."""
        return {
            str(pos): bucket.to_dict() for pos, bucket in self.buckets.items()
        }


class LayerCake:
    """
    A collection of layers forming the sorting machine.
    
    The LayerCake is the primary entry point for the sorting algorithm. It 
    manages the global state, handles piece matching across all layers, and 
    orchestrates dynamic bucket extensions.
    """
    
    def __init__(self):
        """Initialize a LayerCake with no layers."""
        self.layer_cake: List[Layer] = []
    
    def add_layer(self, layer: Layer):
        """Add a layer to the layer cake."""
        self.layer_cake.append(layer)
    
    def get_layer(self, index: int) -> Layer:
        """Get a layer at a specific index (0-based)."""
        return self.layer_cake[index]
    
    def layer_count(self) -> int:
        """Get the number of layers in the layer cake."""
        return len(self.layer_cake)
    
    def reset_quantities(self):
        """Reset all current quantities in the entire layer cake to 0."""
        for layer in self.layer_cake:
            layer.reset_quantities()
    
    def reset_layer_quantities(self, layer_num: int):
        """Reset current quantities for all buckets in a specific layer (1-based)."""
        self.get_layer(layer_num - 1).reset_quantities()

    def reset_bucket_quantities(self, layer_num: int, bucket_id: int):
        """Reset current quantities for a specific bucket in a specific layer."""
        self.get_layer(layer_num - 1).get_bucket(bucket_id).reset_quantities()
    
    def summarize(self) -> str:
        """
        Summarize the entire state of the LayerCake as a JSON string.
        
        This includes the configuration and current state (quantities, enabled status)
        of every bucket in every layer.
        """
        data = [layer.to_dict() for layer in self.layer_cake]
        return json.dumps(data, indent=2)

    def find_best_bucket(self, part_num: str, color_id: Optional[int] = None) -> Tuple[Optional[int], Optional[int], SortingStatus]:
        """
        Find the most appropriate bucket for a given part and color.
        
        The algorithm follows these priority rules:
        1. Specificity: The bucket with the most constraints in its criteria wins.
        2. Layer Priority: If specificity is tied, the bucket in the higher layer 
           (later in the list) wins.
        3. Maintenance: If the best match is disabled, it may fallback to a less 
           specific match or reject the piece entirely based on configuration.
        
        Returns:
            A tuple of (layer_num, bucket_id, status).
            Layer number is 1-based, bucket ID is 1-16.
        """

        # Resolve part and color metadata
        try:
            rb_part = RbParts(part_num)
        except ValueError:
            rb_part = None
            
        rb_col = None
        if color_id is not None:
            try:
                rb_col = RbColours(color_id)
            except ValueError:
                # If lookup fails, we pass the raw ID. The evaluator handles both.
                rb_col = color_id

        # STEP 1: Find the absolute best match (including disabled buckets).
        # We do this first because a disabled bucket might be the 'intended' 
        # destination, and we need to know that to decide whether to reject 
        # or fallback.
        abs_best_layer_idx = None
        abs_best_bucket_id = None
        abs_max_specificity = -1

        for l_idx, layer in enumerate(self.layer_cake):
            for b_id in range(1, 17):
                bucket = layer.get_bucket(b_id)
                specificity, _ = bucket.evaluate(rb_part, rb_col)
                
                # Tie-breaking: Higher layer index wins if specificity is equal.
                if specificity > abs_max_specificity:
                    abs_max_specificity = specificity
                    abs_best_layer_idx = l_idx
                    abs_best_bucket_id = b_id
                elif specificity == abs_max_specificity and specificity > -1:
                    if l_idx > abs_best_layer_idx:
                        abs_best_layer_idx = l_idx
                        abs_best_bucket_id = b_id

        if abs_best_layer_idx is None:
            return None, None, SortingStatus.NO_MATCH

        # STEP 2: Handle the 'Enabled' state of the best match.
        best_bucket = self.layer_cake[abs_best_layer_idx].get_bucket(abs_best_bucket_id)
        if not best_bucket.enabled:
            # If the best match is disabled, we check if fallback is allowed.
            if not best_bucket.config.allow_fallback_if_disabled:
                return None, None, SortingStatus.DISABLED_REJECTED
            
            # Fallback logic: Find the best match among ENABLED buckets only.
            best_layer_idx = None
            best_bucket_id = None
            best_criteria_idx = None
            max_specificity = -1

            for l_idx, layer in enumerate(self.layer_cake):
                for b_id in range(1, 17):
                    bucket = layer.get_bucket(b_id)
                    if not bucket.enabled:
                        continue
                        
                    specificity, criteria_idx = bucket.evaluate(rb_part, rb_col)
                    if specificity > max_specificity:
                        max_specificity = specificity
                        best_layer_idx = l_idx
                        best_bucket_id = b_id
                        best_criteria_idx = criteria_idx
                    elif specificity == max_specificity and specificity > -1:
                        if l_idx > best_layer_idx:
                            best_layer_idx = l_idx
                            best_bucket_id = b_id
                            best_criteria_idx = criteria_idx
            
            if best_layer_idx is None:
                return None, None, SortingStatus.NO_MATCH
        else:
            # The absolute best match is enabled, so we use it.
            _, best_criteria_idx = best_bucket.evaluate(rb_part, rb_col)
            best_layer_idx = abs_best_layer_idx
            best_bucket_id = abs_best_bucket_id

        # STEP 3: Finalize the match and handle side effects (incrementing, extension).
        if best_layer_idx is not None:
            best_bucket_state = self.layer_cake[best_layer_idx].get_bucket(best_bucket_id)
            best_bucket_state.increment_quantity(best_criteria_idx)
            
            # Check if the bucket is now full and needs to 'spill over' to a placeholder.
            if best_bucket_state.is_complete:
                self._handle_bucket_extension(best_bucket_state)
                
            return best_layer_idx + 1, best_bucket_id, SortingStatus.MATCH
            
        return None, None, SortingStatus.NO_MATCH

    def _handle_bucket_extension(self, completed_bucket: Bucket):
        """
        Find an available extension bucket and copy the configuration.
        
        This implements the 'spill-over' requirement, allowing the machine to 
        continue sorting specific parts even after the primary bucket is full.
        """
        for l_idx, layer in enumerate(self.layer_cake):
            for b_id in range(1, 17):
                target_bucket = layer.get_bucket(b_id)
                if target_bucket.config.available_for_extension:
                    # Found a placeholder!
                    # We copy the immutable config to the new bucket and reset its state.
                    target_bucket.config = completed_bucket.config
                    target_bucket.reset_quantities()
                    target_bucket.enabled = True
                    return # We only extend to the first available placeholder.

    @classmethod
    def from_json(cls, file_path: str) -> 'LayerCake':
        """
        Initialize a LayerCake from a JSON file.
        
        This factory method handles the complex parsing of the configuration DSL, 
        supporting both shorthand lists and detailed object notation.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        cake = cls()
        
        for layer_idx, layer_data in enumerate(data):
            layer = Layer()
            seen_positions = set()
            
            for pos_str, criteria_list_data in layer_data.items():
                # Parse positions (handle single int or comma-separated list like "1, 2, 3")
                try:
                    positions = [int(p.strip()) for p in pos_str.split(',')]
                except ValueError:
                    continue

                for position in positions:
                    if position in seen_positions:
                        raise ValueError(f"Bucket position {position} defined multiple times in layer {layer_idx+1}.")
                    seen_positions.add(position)

                    criteria_list = []
                    available_for_ext = False
                    allow_ext = False
                    name = None

                    if isinstance(criteria_list_data, list):
                        # Shorthand notation: just a list of criteria strings or objects.
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
                        # Detailed object notation: allows for directives like 'available_for_extension'.
                        name = criteria_list_data.get("name")
                        available_for_ext = criteria_list_data.get("available_for_extension", False)
                        allow_ext = criteria_list_data.get("allow_extension")
                        allow_fallback = criteria_list_data.get("allow_fallback_if_disabled", True)
                        
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
                        name=name,
                        criteria=tuple(criteria_list),
                        available_for_extension=available_for_ext,
                        allow_extension=allow_ext,
                        allow_fallback_if_disabled=allow_fallback if isinstance(criteria_list_data, dict) else True
                    )
                    layer.set_bucket(position, config)
            cake.add_layer(layer)
            
        return cake

    def __eq__(self, other):
        if not isinstance(other, LayerCake):
            return False
        return self.layer_cake == other.layer_cake

