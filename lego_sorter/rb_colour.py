"""Rebrickable colour enumeration utilities."""

import csv
import os
from dataclasses import dataclass
from typing import Dict, Optional, Union

# Path to the RB_colors.csv file
COLORS_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "LegoData",
    "RB_colors.csv"
)

@dataclass(frozen=True)
class RbColour:
    """Immutable metadata for a Rebrickable colour entry."""
    id: int
    name: str
    is_trans: bool

    def __repr__(self):
        return f"RB_Color(id={self.id}, name='{self.name}', is_trans={self.is_trans})"

class RbColours:
    """
    Dynamic enumeration of Rebrickable colours loaded from CSV.
    
    This class acts as a singleton registry for color data sourced from the 
    Rebrickable database export (RB_colors.csv). It provides a factory-like 
    interface to retrieve color objects using either their unique integer ID 
    or their string name.
    
    The data is lazy-loaded upon the first request.
    """
    _by_id: Dict[int, RbColour] = {}
    _by_name: Dict[str, RbColour] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls):
        """
        Load data from the Rebrickable RB_colors.csv file if not already loaded.
        
        This method parses the CSV file and populates the internal dictionaries
        for ID and Name lookups. It enforces strict parsing and will raise
        an error if the CSV data is malformed.
        """
        if cls._initialized:
            return

        if not os.path.exists(COLORS_CSV_PATH):
            raise FileNotFoundError(f"Rebrickable colors CSV not found at: {COLORS_CSV_PATH}")

        with open(COLORS_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for line_num, row in enumerate(reader, start=2):  # start=2 accounts for header
                try:
                    c_id = int(row['id'])
                    c_name = row['name']
                    
                    # 'is_trans' handling:
                    # The CSV usually contains 'True' or 'False' strings.
                    # We convert this to a boolean.
                    is_trans_str = row['is_trans'].lower()
                    if is_trans_str not in ('true', 'false'):
                        raise ValueError(
                            f"Invalid boolean value for 'is_trans': '{row['is_trans']}'. "
                            f"Expected 'true' or 'false' (case-insensitive), but got '{is_trans_str}'"
                        )
                    c_is_trans = is_trans_str == 'true'
                    
                    color = RbColour(c_id, c_name, c_is_trans)
                    
                    cls._by_id[c_id] = color
                    # Store by name (case-insensitive for robust lookup)
                    cls._by_name[c_name.lower()] = color
                except (ValueError, KeyError) as e:
                    # Fatal error on malformed rows
                    raise ValueError(f"Error parsing RB_colors.csv at line {line_num}: {e}") from e
        
        cls._initialized = True

    def __new__(cls, value: Union[int, str]) -> RbColour:
        """
        Factory method to get an RB_Color instance by ID or Name.
        
        Args:
            value: Integer ID or String Name of the color.
            
        Returns:
            RB_Color instance.
            
        Raises:
            ValueError: If the color is not found.
        """
        cls._initialize()

        if isinstance(value, int):
            if value in cls._by_id:
                return cls._by_id[value]
            # Try string representation of int just in case
            raise ValueError(f"Unknown Rebrickable color ID: {value}")
        
        elif isinstance(value, str):
            # Check if string is a digit (ID passed as string)
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                int_val = int(value)
                if int_val in cls._by_id:
                    return cls._by_id[int_val]
            
            # Lookup by name
            lower_name = value.lower()
            if lower_name in cls._by_name:
                return cls._by_name[lower_name]
            
            raise ValueError(f"Unknown Rebrickable color Name: {value}")
        
        else:
            raise TypeError(f"Expected int or str, got {type(value)}")

    @classmethod
    def get_all(cls) -> Dict[int, RbColour]:
        """Return all loaded colors."""
        cls._initialize()
        return cls._by_id.copy()
