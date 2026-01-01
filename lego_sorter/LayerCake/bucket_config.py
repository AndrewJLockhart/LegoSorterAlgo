"""Bucket configuration and state classes."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from .criteria_evaluator import CriteriaEvaluator


@dataclass(frozen=True)
class BucketCriteria:
    """
    A single criteria within a bucket configuration.
    
    Encapsulates the matching logic (evaluator) and the required_quantity.
    """
    evaluator: CriteriaEvaluator
    required_quantity: Optional[int] = None

    def __repr__(self):
        return f"BucketCriteria(expression='{self.evaluator.expression}', required={self.required_quantity})"

    def to_dict(self):
        """Convert criteria to a serializable dictionary."""
        return {
            "expression": self.evaluator.expression,
            "required": self.required_quantity
        }


@dataclass(frozen=True)
class BucketConfig:
    """
    Immutable configuration for a bucket.
    
    This class defines the 'rules of engagement' for a bucket. It is frozen to 
    ensure that once a configuration is defined, it cannot be accidentally 
    modified, which is critical for maintaining consistency across layers.
    """
    criteria: Tuple[BucketCriteria, ...] = field(default_factory=tuple)
    name: Optional[str] = None
    available_for_extension: bool = False   #When this is true, the bucket can serve as a source for extension. It must not have criteria.
    allow_extension: Optional[bool] = None  #When this is true, once the bucket is full, we will look
    allow_fallback_if_disabled: bool = True  #If the bucket is disabled, allow fallback to other buckets. 

    def __post_init__(self):
        """
        Validate mutual exclusivity of criteria and extension directives.
        
        This method ensures the configuration is logically sound before it's used.
        """
        # Set default value for allow_extension if not provided.
        # We default to True if there are criteria, as the most common use case 
        # for criteria is to eventually fill up and need more space.
        if self.allow_extension is None:
            default_val = bool(self.criteria) and not self.available_for_extension
            object.__setattr__(self, 'allow_extension', default_val)

        # Validation logic to prevent impossible states:
        if self.available_for_extension:
            if self.name is not None:
                raise ValueError("A placeholder bucket (available_for_extension) cannot have a name.")
            if self.criteria:
                raise ValueError("A placeholder bucket cannot have criteria.")
            if self.allow_extension:
                raise ValueError("A placeholder bucket cannot have allow_extension set to True.")
            if not self.allow_fallback_if_disabled:
                raise ValueError("A placeholder bucket cannot have allow_fallback_if_disabled set to False.")
            
        if self.allow_extension and not self.criteria:
            # You can't extend something that has no rules to copy.
            raise ValueError("BucketConfig must have criteria if allow_extension is set.")

        # Check for consistency of required_quantity.
        # We enforce 'all or nothing' for required quantities to avoid ambiguous 
        # capacity states where some parts are tracked and others are infinite.
        if self.criteria:
            has_required = [c.required_quantity is not None for c in self.criteria]
            if any(has_required) and not all(has_required):
                raise ValueError("All criteria must have a required_quantity, or none of them should.")

    def evaluate(self, rb_part, rb_col, current_quantities: List[int]) -> Tuple[int, int]:
        """
        Evaluate a piece against all criteria in this config.
        
        Returns:
            A tuple of (specificity_score, criteria_index).
            Specificity is the number of constraints in the matching expression.
            If no match is found, returns (-1, -1).
        """
        best_score = -1
        best_idx = -1

        for i, crit in enumerate(self.criteria):
            # Check if this specific criteria has reached its capacity limit.
            if crit.required_quantity is not None and current_quantities[i] >= crit.required_quantity:
                continue

            # Evaluate the DSL expression.
            if crit.evaluator.evaluate(rb_part, rb_col):
                # Specificity is used to ensure the 'most specific' rule wins.
                # e.g. "Red 2x4 Brick" wins over "Red Piece".
                score = crit.evaluator.specificity_score
                if score > best_score:
                    best_score = score
                    best_idx = i
        
        return best_score, best_idx

    def to_dict(self):
        """Convert configuration to a serializable dictionary."""
        return {
            "name": self.name,
            "criteria": [c.to_dict() for c in self.criteria],
            "available_for_extension": self.available_for_extension,
            "allow_extension": self.allow_extension,
            "allow_fallback_if_disabled": self.allow_fallback_if_disabled
        }
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
