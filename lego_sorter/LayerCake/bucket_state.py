"""Bucket state class for tracking quantities."""

from typing import List, Optional, Tuple
from .bucket_config import BucketConfig


class Bucket:
    """Mutable state for a bucket, tracking quantities against a BucketConfig."""
    
    def __init__(self, config: Optional[BucketConfig] = None):
        """Initialize bucket state with a configuration."""
        self.config = config or BucketConfig()
        self.current_quantities = [0] * len(self.config.criteria)
        self.enabled = True
    
    def evaluate(self, rb_part, rb_col) -> Tuple[int, int]:
        """Evaluate against the config using current state."""
        return self.config.evaluate(rb_part, rb_col, self.current_quantities)
    
    def increment_quantity(self, criteria_idx: int):
        """Increment the quantity for a specific criteria."""
        if 0 <= criteria_idx < len(self.current_quantities):
            self.current_quantities[criteria_idx] += 1
            
    def reset_quantities(self):
        """Reset all current quantities to 0."""
        self.current_quantities = [0] * len(self.config.criteria)

    @property
    def is_complete(self) -> bool:
        """
        Check if the bucket is complete.
        A bucket is complete if it allows extension and all its criteria 
        have reached their required quantities.
        """
        if not self.config.criteria or not self.config.allow_extension:
            return False
            
        # If criteria exist, they either all have required_quantity or none do.
        if self.config.criteria[0].required_quantity is None:
            return False
            
        for i, crit in enumerate(self.config.criteria):
            if self.current_quantities[i] < crit.required_quantity:
                return False
        return True

    def __repr__(self):
        return f"BucketState(config={self.config}, quantities={self.current_quantities})"

    def __eq__(self, other):
        if not isinstance(other, Bucket):
            return False
        return self.config == other.config and self.current_quantities == other.current_quantities
