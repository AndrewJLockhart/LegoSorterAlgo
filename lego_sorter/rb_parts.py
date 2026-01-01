"""
Rebrickable part and category enumeration utilities.

This module provides the data structures and lookup mechanisms for Rebrickable 
part and category metadata, which is essential for REQ-1 (Match Pieces to Buckets).
"""

import csv
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

# Paths to the CSV files - used to load the source of truth for part and category data.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_CSV_PATH = os.path.join(BASE_DIR, "LegoData", "RB_parts.csv")
CATEGORIES_CSV_PATH = os.path.join(BASE_DIR, "LegoData", "RB_part_categories.csv")


@dataclass(frozen=True)
class RbPartCategory:
    """
    Immutable metadata for a Rebrickable part category.
    
    This class encapsulates the properties of a category (ID, Name) required 
    by the CriteriaEvaluator to perform specificity-based matching (REQ-1) 
    when using the RB_PT_CAT keyword.
    """
    id: int
    name: str

    def __repr__(self):
        return f"RbPartCategory(id={self.id}, name='{self.name}')"


@dataclass(frozen=True)
class RbPart:
    """
    Immutable metadata for a Rebrickable part.
    
    This class encapsulates the properties of a part (Part Number, Name, Category)
    required by the CriteriaEvaluator to perform specificity-based matching (REQ-1).
    It links a part to its category, enabling hierarchical matching rules.
    """
    part_num: str
    name: str
    category: RbPartCategory

    def __repr__(self):
        return f"RbPart(part_num='{self.part_num}', name='{self.name}', category={self.category.name})"


class RbParts:
    """
    Registry for Rebrickable parts and categories loaded from CSVs.
    
    This class acts as a singleton registry for part and category data sourced 
    from the Rebrickable database export (RB_parts.csv and RB_part_categories.csv). 
    It provides a factory-like interface to retrieve part objects using their 
    unique part number.
    
    Why we need this:
    - REQ-1: To resolve part numbers (e.g., '3001') into rich objects that 
      the CriteriaEvaluator can use for matching against part numbers and 
      categories.
    - Performance: Lazy-loading ensures the CSVs are only parsed when needed.
    """
    _parts_by_num: Dict[str, RbPart] = {}
    _categories_by_id: Dict[int, RbPartCategory] = {}
    _parts_by_category_id: Dict[int, List[RbPart]] = defaultdict(list)
    _initialized: bool = False

    @classmethod
    def _initialize(cls):
        """
        Load data from RB_part_categories.csv and RB_parts.csv if not already loaded.
        
        This method ensures data integrity by validating the CSV structure 
        and types during initialization. It enforces strict parsing and will 
        raise an error if the CSV data is malformed or inconsistent.
        """
        if cls._initialized:
            return

        # 1. Load Categories
        if not os.path.exists(CATEGORIES_CSV_PATH):
            raise FileNotFoundError(f"Rebrickable categories CSV not found at: {CATEGORIES_CSV_PATH}")

        with open(CATEGORIES_CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for line_num, row in enumerate(reader, start=2):
                try:
                    cat_id = int(row['id'])
                    cat_name = row['name']
                    
                    if cat_id in cls._categories_by_id:
                        raise ValueError(f"Duplicate category ID found: {cat_id}")
                        
                    cls._categories_by_id[cat_id] = RbPartCategory(cat_id, cat_name)
                except (ValueError, KeyError) as e:
                    raise ValueError(f"Error parsing RB_part_categories.csv at line {line_num}: {e}") from e

        # 2. Load Parts
        if not os.path.exists(PARTS_CSV_PATH):
            raise FileNotFoundError(f"Rebrickable parts CSV not found at: {PARTS_CSV_PATH}")

        with open(PARTS_CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for line_num, row in enumerate(reader, start=2):
                try:
                    part_num = row['part_num']
                    name = row['name']
                    cat_id = int(row['part_cat_id'])

                    # Resolve category
                    if cat_id not in cls._categories_by_id:
                        # It's possible RB_parts.csv references a category not in RB_part_categories.csv 
                        # if the files are out of sync, but we'll treat it as a fatal error for strictness.
                        raise ValueError(f"Unknown category ID {cat_id} for part {part_num}")
                    
                    if part_num in cls._parts_by_num:
                        raise ValueError(f"Duplicate part number found: {part_num}")

                    category = cls._categories_by_id[cat_id]
                    
                    part = RbPart(part_num, name, category)
                    
                    cls._parts_by_num[part_num] = part
                    cls._parts_by_category_id[cat_id].append(part)
                    
                except (ValueError, KeyError) as e:
                    # Fatal error on malformed rows to prevent incorrect sorting.
                    raise ValueError(f"Error parsing RB_parts.csv at line {line_num}: {e}") from e

        cls._initialized = True

    def __new__(cls, part_num: str) -> RbPart:
        """
        Factory method to get an RbPart instance by part_num.
        
        This allows the rest of the system to easily obtain part metadata 
        given a part number string (REQ-1).
        
        Args:
            part_num: The unique part number string (e.g. '3001').
            
        Returns:
            RbPart instance.
            
        Raises:
            ValueError: If the part is not found.
        """
        cls._initialize()
        
        # part_num in CSV is string. Even if user passes int, we convert to str.
        part_key = str(part_num)
        
        if part_key in cls._parts_by_num:
            return cls._parts_by_num[part_key]
        
        raise ValueError(f"Unknown Rebrickable part number: {part_num}")

    @classmethod
    def get_category(cls, cat_id: int) -> RbPartCategory:
        """
        Retrieve a category by its ID.
        
        Args:
            cat_id: The unique integer ID of the category.
            
        Returns:
            RbPartCategory instance.
        """
        cls._initialize()
        if cat_id in cls._categories_by_id:
            return cls._categories_by_id[cat_id]
        raise ValueError(f"Unknown category ID: {cat_id}")

    @classmethod
    def get_parts_in_category(cls, cat_id: int) -> List[RbPart]:
        """
        Retrieve all parts belonging to a specific category ID.
        
        Args:
            cat_id: The unique integer ID of the category.
            
        Returns:
            A list of RbPart instances belonging to the category.
        """
        cls._initialize()
        # Return a copy to prevent modification of internal list
        return list(cls._parts_by_category_id.get(cat_id, []))

    @classmethod
    def get_all_categories(cls) -> List[RbPartCategory]:
        """
        Return a list of all known categories.
        
        Useful for UI or debugging to see the full range of supported categories.
        """
        cls._initialize()
        return list(cls._categories_by_id.values())
