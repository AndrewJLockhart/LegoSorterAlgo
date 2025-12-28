"""LegoCriteria class for defining sorting criteria."""


class LegoCriteria:
    """A single criterion containing a number and a string."""
    
    def __init__(self, number: int, string: str):
        """Initialize a LegoCriteria.
        
        Args:
            number: A numeric value for the criteria
            string: A string value for the criteria
        """
        self.number = number
        self.string = string
    
    def __repr__(self):
        return f"LegoCriteria(number={self.number}, string='{self.string}')"
    
    def __eq__(self, other):
        if not isinstance(other, LegoCriteria):
            return False
        return self.number == other.number and self.string == other.string
