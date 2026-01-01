"""Rebrickable part value utilities."""

import csv
import os
from typing import Dict, Tuple

# Path to the RB_partvalues.csv file
PART_VALUES_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "LegoData",
    "RB_partvalues.csv"
)

class RbPartValues:
    """
    Registry for part values loaded from RB_partvalues.csv.
    
    This class provides a lookup for the dollar value of a part based on its 
    part number and color ID.
    """
    _values: Dict[Tuple[str, int], float] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls):
        """Load data from RB_partvalues.csv if not already loaded."""
        if cls._initialized:
            return

        if not os.path.exists(PART_VALUES_CSV_PATH):
            # If the file doesn't exist, we just initialize with empty data.
            # This allows the system to run even if the temporary script hasn't been run.
            cls._initialized = True
            return

        with open(PART_VALUES_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for line_num, row in enumerate(reader, start=2):
                try:
                    part_num = row['part_num']
                    color_id = int(row['color_id'])
                    value = float(row['DollarValue'])
                    
                    cls._values[(part_num, color_id)] = value
                except (ValueError, KeyError) as e:
                    # Log error or raise? For now, let's be strict.
                    raise ValueError(f"Error parsing RB_partvalues.csv at line {line_num}: {e}") from e
        
        cls._initialized = True

    @classmethod
    def get_value(cls, part_num: str, color_id: int) -> float:
        """
        Get the dollar value for a specific part and color.
        
        Returns 0.0 if the part/color combination is not found.
        """
        cls._initialize()
        return cls._values.get((part_num, color_id), 0.0)
