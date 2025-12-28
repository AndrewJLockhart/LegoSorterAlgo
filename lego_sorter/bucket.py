"""Bucket class for representing a sorting bucket."""

from .bucket_config import BucketConfig


class Bucket:
    """A bucket at a specific position with a configuration."""
    
    def __init__(self, position: int, config: BucketConfig = None):
        """Initialize a Bucket.
        
        Args:
            position: Position of the bucket (1-16)
            config: BucketConfig object defining what goes into this bucket
        
        Raises:
            ValueError: If position is not between 1 and 16
        """
        if not 1 <= position <= 16:
            raise ValueError("Bucket position must be between 1 and 16")
        
        self.position = position
        self.config = config if config is not None else BucketConfig()
    
    def __repr__(self):
        return f"Bucket(position={self.position}, config={self.config})"
    
    def __eq__(self, other):
        if not isinstance(other, Bucket):
            return False
        return self.position == other.position and self.config == other.config
