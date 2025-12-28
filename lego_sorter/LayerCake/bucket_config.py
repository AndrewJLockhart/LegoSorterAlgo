"""BucketConfig class for defining bucket configuration."""

from typing import List, Optional, Tuple
from .criteria_evaluator import CriteriaEvaluator


class BucketConfig:
    """Configuration for a bucket containing a list of criteria to match."""
    
    def __init__(self, criteria: Optional[List[Tuple[CriteriaEvaluator, Optional[int], int]]] = None):
        """Initialize a BucketConfig.
        
        Args:
            criteria: List of tuples (CriteriaEvaluator, RequiredQuantity, CurrentQuantity). 
                      Defaults to empty list if not provided.
        """
        self.criteria = criteria if criteria is not None else []
    
    def add_criteria(self, evaluator: CriteriaEvaluator, required_quantity: Optional[int] = None):
        """Add a criteria to the bucket config.
        
        Args:
            evaluator: CriteriaEvaluator object to add
            required_quantity: Optional quantity required for this criteria
        """
        # Initialize current_quantity to 0
        self.criteria.append((evaluator, required_quantity, 0))
    
    def update_current_quantity(self, index: int, quantity: int):
        """Update the current quantity for a specific criteria.
        
        Args:
            index: Index of the criteria to update
            quantity: New quantity value
            
        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < len(self.criteria):
            raise IndexError("Criteria index out of range")
            
        evaluator, required, _ = self.criteria[index]
        self.criteria[index] = (evaluator, required, quantity)
    
    def increment_quantity(self, index: int):
        """Increment the current quantity for a specific criteria by 1.
        
        Args:
            index: Index of the criteria to update
            
        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < len(self.criteria):
            raise IndexError("Criteria index out of range")
            
        evaluator, required, current = self.criteria[index]
        self.criteria[index] = (evaluator, required, current + 1)
    
    def reset_quantities(self):
        """Reset the current quantity for all criteria to 0."""
        self.criteria = [(evaluator, required, 0) for evaluator, required, _ in self.criteria]
    
    def __repr__(self):
        return f"BucketConfig(criteria={self.criteria})"
    
    def __eq__(self, other):
        if not isinstance(other, BucketConfig):
            return False
        
        if len(self.criteria) != len(other.criteria):
            return False
        
        for i, (eval1, req1, cur1) in enumerate(self.criteria):
            (eval2, req2, cur2) = other.criteria[i]
            # Compare expressions since CriteriaEvaluator instances might differ
            if eval1.expression != eval2.expression: 
                return False
            if req1 != req2 or cur1 != cur2:
                return False
        
        return True
