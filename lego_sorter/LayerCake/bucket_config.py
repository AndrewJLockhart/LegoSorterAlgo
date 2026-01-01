"""Bucket configuration and state classes."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
from .criteria_evaluator import CriteriaEvaluator


@dataclass(frozen=True)
class BucketCriteria:
    """A single criteria within a bucket configuration."""
    evaluator: CriteriaEvaluator
    required_quantity: Optional[int] = None

    def __repr__(self):
        return f"BucketCriteria(expression='{self.evaluator.expression}', required={self.required_quantity})"


@dataclass(frozen=True)
class BucketConfig:
    """Immutable configuration for a bucket, containing multiple criteria or extension directives."""
    criteria: Tuple[BucketCriteria, ...] = field(default_factory=tuple)
    available_for_extension: bool = False
    allow_extension: Optional[bool] = None

    def __post_init__(self):
        """Validate mutual exclusivity of criteria and extension directives."""
        # Set default value for allow_extension if not provided
        if self.allow_extension is None:
            # Default to True if there are criteria and not available_for_extension
            # Otherwise default to False
            default_val = bool(self.criteria) and not self.available_for_extension
            object.__setattr__(self, 'allow_extension', default_val)

        if self.available_for_extension and self.allow_extension:
            raise ValueError("available_for_extension and allow_extension are mutually exclusive.")
        
        if self.available_for_extension and self.criteria:
            raise ValueError("BucketConfig cannot have criteria if available_for_extension is set.")
            
        if self.allow_extension and not self.criteria:
            raise ValueError("BucketConfig must have criteria if allow_extension is set.")

        # Check for consistency of required_quantity
        if self.criteria:
            has_required = [c.required_quantity is not None for c in self.criteria]
            if any(has_required) and not all(has_required):
                raise ValueError("All criteria must have a required_quantity, or none of them should.")

    def evaluate(self, rb_part, rb_col, current_quantities: List[int]) -> Tuple[int, int]:
        """
        Evaluate a part and color against all criteria in this bucket.
        
        Args:
            rb_part: RbParts object or None
            rb_col: RbColours object, int ID, or None
            current_quantities: List of current quantities corresponding to self.criteria
            
        Returns:
            A tuple of (specificity, criteria_index).
            Specificity is -1 if no criteria matches or if the matching criteria is full.
            criteria_index is the index of the matching criteria in self.criteria.
        """
        for i, crit in enumerate(self.criteria):
            # Check if this criteria is already full
            if crit.required_quantity is not None and current_quantities[i] >= crit.required_quantity:
                continue
                
            if crit.evaluator.evaluate(rb_part, rb_col):
                return crit.evaluator.specificity, i
                
        return -1, -1

    def __repr__(self):
        return f"BucketConfig(criteria={self.criteria})"
