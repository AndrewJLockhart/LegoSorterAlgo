"""BucketConfig class for defining bucket configuration."""

from typing import List
from .lego_criteria import LegoCriteria


class BucketConfig:
    """Configuration for a bucket containing a list of criteria to match."""
    
    def __init__(self, criteria: List[LegoCriteria] = None):
        """Initialize a BucketConfig.
        
        Args:
            criteria: List of LegoCriteria objects. Defaults to empty list if not provided.
        """
        self.criteria = criteria if criteria is not None else []
    
    def add_criteria(self, criteria: LegoCriteria):
        """Add a criteria to the bucket config.
        
        Args:
            criteria: LegoCriteria object to add
        """
        self.criteria.append(criteria)
    
    def __repr__(self):
        return f"BucketConfig(criteria={self.criteria})"
    
    def __eq__(self, other):
        if not isinstance(other, BucketConfig):
            return False
        return self.criteria == other.criteria
