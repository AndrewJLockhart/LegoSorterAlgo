"""Bucket state class for tracking quantities."""

from typing import Optional, Tuple
from .bucket_config import BucketConfig


class Bucket:
    """
    Mutable state for a bucket.
    
    While BucketConfig is immutable, the Bucket class tracks the changing state 
    of the physical bucket, such as how many pieces it currently holds and 
    whether it is currently enabled for sorting.
    """
    
    def __init__(self, config: Optional[BucketConfig] = None):
        """Initialize bucket state with a configuration."""
        self.config = config or BucketConfig()
        # We track quantities in a list corresponding to the criteria in the config.
        self.current_quantities = [0] * len(self.config.criteria)
        self.enabled = True
    
    def evaluate(self, rb_part, rb_col) -> Tuple[int, int]:
        """
        Evaluate against the config using current state.
        
        This delegates the matching logic to the config while providing the 
        current quantity state to check against capacity limits.
        """
        return self.config.evaluate(rb_part, rb_col, self.current_quantities)
    
    def increment_quantity(self, criteria_idx: int):
        """
        Increment the quantity for a specific criteria.
        
        This is called when a piece is successfully sorted into this bucket.
        """
        if 0 <= criteria_idx < len(self.current_quantities):
            self.current_quantities[criteria_idx] += 1
        else:
            pass
            
    def reset_quantities(self):
        """
        Reset all current quantities to 0.
        
        Typically called when a bucket is emptied or when a placeholder 
        receives a new configuration.
        """
        self.current_quantities = [0] * len(self.config.criteria)

    @property
    def is_complete(self) -> bool:
        """
        Check if the bucket is complete (full).
        
        A bucket is considered 'complete' if it allows extension and ALL of its 
        defined criteria have reached their required quantities. This state 
        triggers the automatic extension logic in the LayerCake.
        """
        if not self.config.criteria or not self.config.allow_extension:
            # If it doesn't allow extension, it's never 'complete' in the sense 
            # of triggering a spill-over.
            return False
            
        # If criteria exist, they either all have required_quantity or none do.
        # If they don't have required_quantity, the bucket has infinite capacity.
        if self.config.criteria[0].required_quantity is None:
            return False
            
        for i, crit in enumerate(self.config.criteria):
            if self.current_quantities[i] < crit.required_quantity:
                # Still has room for at least one type of piece.
                return False
        
        return True

    def to_dict(self):
        """Convert bucket state to a serializable dictionary."""
        return {
            "config": self.config.to_dict(),
            "current_quantities": self.current_quantities,
            "enabled": self.enabled,
            "is_complete": self.is_complete
        }

    def __repr__(self):
        return f"BucketState(config={self.config}, quantities={self.current_quantities})"

    def __eq__(self, other):
        if not isinstance(other, Bucket):
            return False
        return self.config == other.config and self.current_quantities == other.current_quantities
