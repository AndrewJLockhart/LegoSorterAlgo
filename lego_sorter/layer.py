"""Layer class for representing a layer of buckets."""

from typing import Dict, Optional
from .bucket import Bucket


class Layer:
    """A layer containing buckets at positions 1 to 16."""
    
    def __init__(self):
        """Initialize a Layer with empty bucket positions."""
        self.buckets: Dict[int, Bucket] = {}
    
    def add_bucket(self, bucket: Bucket):
        """Add a bucket to the layer.
        
        Args:
            bucket: Bucket object to add
        
        Raises:
            ValueError: If bucket position is already occupied
        """
        if bucket.position in self.buckets:
            raise ValueError(f"Position {bucket.position} already has a bucket")
        self.buckets[bucket.position] = bucket
    
    def get_bucket(self, position: int) -> Optional[Bucket]:
        """Get a bucket at a specific position.
        
        Args:
            position: Position to retrieve (1-16)
        
        Returns:
            Bucket at the position, or None if no bucket exists
        """
        return self.buckets.get(position)
    
    def remove_bucket(self, position: int) -> Optional[Bucket]:
        """Remove a bucket at a specific position.
        
        Args:
            position: Position to remove (1-16)
        
        Returns:
            Removed bucket, or None if no bucket existed at that position
        """
        return self.buckets.pop(position, None)
    
    def __repr__(self):
        return f"Layer(buckets={list(self.buckets.values())})"
    
    def __eq__(self, other):
        if not isinstance(other, Layer):
            return False
        return self.buckets == other.buckets
