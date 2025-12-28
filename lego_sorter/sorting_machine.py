"""SortingMachine class for representing the entire sorting machine state."""

from typing import List
from .layer import Layer


class SortingMachine:
    """A sorting machine made from a number of layers."""
    
    def __init__(self):
        """Initialize a SortingMachine with no layers."""
        self.layers: List[Layer] = []
    
    def add_layer(self, layer: Layer):
        """Add a layer to the sorting machine.
        
        Args:
            layer: Layer object to add
        """
        self.layers.append(layer)
    
    def get_layer(self, index: int) -> Layer:
        """Get a layer at a specific index.
        
        Args:
            index: Index of the layer (0-based)
        
        Returns:
            Layer at the specified index
        
        Raises:
            IndexError: If index is out of range
        """
        return self.layers[index]
    
    def remove_layer(self, index: int) -> Layer:
        """Remove a layer at a specific index.
        
        Args:
            index: Index of the layer to remove (0-based)
        
        Returns:
            Removed layer
        
        Raises:
            IndexError: If index is out of range
        """
        return self.layers.pop(index)
    
    def layer_count(self) -> int:
        """Get the number of layers in the sorting machine.
        
        Returns:
            Number of layers
        """
        return len(self.layers)
    
    def __repr__(self):
        return f"SortingMachine(layers={self.layers})"
    
    def __eq__(self, other):
        if not isinstance(other, SortingMachine):
            return False
        return self.layers == other.layers
