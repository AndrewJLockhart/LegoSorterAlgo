# LegoSorterAlgo

A algorithm for managing the state and logic of a multi-layered Lego sorting machine.

## Problem Statement

Sorting large collections of Lego pieces is a complex task that requires balancing specificity, capacity, and physical machine constraints. The `LegoSorterAlgo` solves this by providing a "LayerCake" architecture that allows users to define complex sorting rules across multiple physical layers of buckets.

The algorithm must:
1.  **Match Pieces to Buckets**: Given a part number and color, find the most specific bucket that matches.
2.  **Manage Capacity**: Track how many pieces are in each bucket and stop accepting pieces when a target quantity is reached.
3.  **Handle Dynamic Extensions**: Automatically "spill over" sorting rules to empty placeholder buckets when a primary bucket is full.
4.  **Support Maintenance**: Allow individual buckets to be disabled (e.g., for emptying) without stopping the entire machine, with the algorithm automatically falling back to the next best match.

## Core Concepts

### The LayerCake Architecture
The machine is organized into **Layers**. Each layer contains **16 Buckets** (indexed 1-16).
*   **Specificity**: The algorithm always chooses the most specific match first. Specificity is determined by the number of constraints in the criteria (e.g., `RB_COL = Red AND RB_PT = 3001` is more specific than just `RB_COL = Red`).
*   **Layer Priority**: If two buckets have the same specificity, the one in the higher layer (later in the list) is chosen.

### Bucket Configuration & State
We distinguish between the **Configuration** (the rules) and the **State** (the current count and status).
*   **BucketConfig**: Immutable rules defining what a bucket accepts.
*   **Bucket**: Mutable state tracking `current_quantities` and whether the bucket is `enabled`.

## JSON Configuration Support

The `LayerCake` can be initialized from a JSON file. The format supports both a high-level shorthand for simple setups and a detailed object notation for advanced features.

### Example JSON
```json
[
  {
    "1": ["RB_COL = Red"],
    "2, 3": {
      "criteria": [
        {"expression": "RB_PT = 3001", "required": 50},
        {"expression": "RB_PT = 3002", "required": 50}
      ],
      "allow_extension": true
    },
    "16": { "available_for_extension": true }
  }
]
```

### Parameter Reference

| Parameter | Type | Description |
| :--- | :--- | :--- |
| **`criteria`** | `List` | A list of rules for the bucket. Can be simple strings (expressions) or objects with `expression` and `required`. |
| **`expression`** | `String` | A DSL string (e.g., `RB_COL = Blue \| Red`) evaluated by the `CriteriaEvaluator`. |
| **`required`** | `Int` | The maximum number of pieces this criteria will accept. If omitted, the bucket has infinite capacity. |
| **`allow_extension`** | `Bool` | If `true`, when this bucket reaches its `required` capacity, the algorithm will look for a placeholder to copy these rules to. Defaults to `true` if criteria are present. |
| **`available_for_extension`** | `Bool` | Marks this bucket as a **Placeholder**. It has no rules of its own and cannot have any other state (like a name) set. It is available to receive rules from a full bucket. |
| **`allow_fallback_if_disabled`** | `Bool` | If `false`, when this bucket is the best match but is disabled, the algorithm will reject the part instead of looking for a less specific match. Defaults to `true`. This would allow the caller to then pause and not send any further bits into the sorter.|

## Operational Behavior

### 1. Specificity Matching
When a piece is processed, the algorithm evaluates all enabled buckets. It calculates a "specificity score" based on the number of conditions in the criteria. The piece is assigned to the bucket with the highest score.

### 2. Enabling/Disabling Buckets
Buckets can be disabled at runtime (e.g., `bucket.enabled = False`). When a bucket is disabled, the `find_best_bucket` logic will skip it and automatically find the next best match (the next highest specificity).

### 3. Automatic Extension
If a bucket has `allow_extension: true` and all its criteria have reached their `required` quantity, the `LayerCake` will:
1.  Search for the first bucket in the machine marked with `available_for_extension: true`.
2.  Copy the configuration from the full bucket to the placeholder.
3.  Reset the quantities in the new bucket to zero.
4.  The placeholder is now an active sorting bucket for those specific pieces.

## Criteria DSL

The `CriteriaEvaluator` supports a rich expression language:
*   **Keys**: 
    *   `RB_COL`: Color name or ID (e.g., `RB_COL = Red`, `RB_COL = 4`).
    *   `RB_PT`: Part number (e.g., `RB_PT = 3001`).
    *   `RB_PT_CAT`: Part Category name or ID (e.g., `RB_PT_CAT = Bricks`, `RB_PT_CAT = 11`).
    *   `PT_VAL`: Part value in dollars (e.g., `PT_VAL > 1.05`).
*   **Operators**: `=`, `!=`, `>`, `<`, `>=`, `<=`.
*   **Logic**: `AND`, `OR`, and the `|` shorthand for multiple values (e.g., `RB_COL = Red | Blue | Green`).
*   **Grouping**: Use parentheses `()` to define precedence.

## Data Setup

The algorithm relies on Rebrickable data stored in the `LegoData` folder.

### Rebrickable CSVs
Ensure the following files are present in `LegoData/`:
- `RB_colors.csv`
- `RB_elements.csv`
- `RB_parts.csv`
- `RB_part_categories.csv`
- ... (and other Rebrickable CSVs)

You can download these using the provided script:
```bash
python scripts/download_rebrickable_data.py
```

### Generating Part Values
To use the `PT_VAL` criteria, you need a `RB_partvalues.csv` file. You can generate a sample file with 100 random entries using:
```bash
python scripts/generate_part_values.py
```
This script creates a deterministic set of values for common parts and colors for testing purposes.

## Structure

The package consists of the following components:

### CriteriaEvaluator
Evaluates whether a Lego piece matches a specific criteria expression (e.g., "RB_COL = Red").

### BucketConfig
Defines the configuration for a bucket. Contains:
- A list of criteria tuples: `(CriteriaEvaluator, required_quantity, current_quantity)`
- Methods to update and track quantities.

### Layer
Represents a single layer in the sorting machine. Contains:
- A dictionary mapping positions (1-16) to `BucketConfig` objects.

### LayerCake
The main object representing the entire sorting machine state. Contains:
- A list of `Layer` objects.
- `find_best_bucket(part_num, color)`: Returns a tuple `(layer_num, bucket_id, status)`.

## Handling Results

The `find_best_bucket` method returns a `SortingStatus` to help the caller understand why a piece was assigned or rejected:

| Status | Description |
| :--- | :--- |
| `MATCH` | A suitable bucket was found and the piece should be sorted there. |
| `NO_MATCH` | No bucket in the entire machine matches the piece's criteria. |
| `DISABLED_REJECTED` | The best matching bucket is currently disabled, and `allow_fallback_if_disabled` is set to `false`. |

Example usage:
```python
layer_idx, bucket_id, status = cake.find_best_bucket("3001", "Red")

if status == SortingStatus.MATCH:
    print(f"Sort into Layer {layer_idx}, Bucket {bucket_id}")
elif status == SortingStatus.DISABLED_REJECTED:
    print("Best match is disabled and fallback is forbidden.")
else:
    print("No matching bucket found.")
```
- Methods to load configuration from JSON.

## Installation

Clone the repository:
```bash
git clone https://github.com/AndrewJLockhart/LegoSorterAlgo.git
cd LegoSorterAlgo
```

Optionally, install the package in development mode:
```bash
pip install -e .
```

## Data Setup

The algorithm relies on metadata from the Rebrickable database to resolve part numbers, colors, and categories.

### Downloading Rebrickable Data
Before running the algorithm, you must populate the `LegoData` directory with the latest CSV exports from Rebrickable. A script is provided to automate this:

```bash
python scripts/download_rebrickable_data.py
```

**What it does:**
- Connects to the Rebrickable CDN.
- Downloads compressed (`.csv.gz`) files for parts, colors, categories, and relationships.
- Decompresses them into the `LegoData` folder.

**Why it's needed:**
- **REQ-1 (Matching)**: The `CriteriaEvaluator` needs this data to know that part `3001` is a "Brick 2x4" and belongs to the "Bricks" category.
- **Offline Support**: By storing the data locally in `LegoData`, the algorithm can perform high-speed lookups without needing an active internet connection during sorting.

### Generating Part Values (Temporary)
A secondary script is used to generate sample market value data for parts:

```bash
python scripts/generate_part_values.py
```

**Current Status:**
- This script currently generates a **temporary** `RB_partvalues.csv` file with 100 hardcoded entries for common bricks and plates.
- It is used to simulate the presence of pricing data for the sorting algorithm.

**Future Plans:**
- This script will be updated to fetch real-time market data from the **BrickLink API** based on specific input parameters.

## Usage

```python
from lego_sorter import BucketConfig, Layer, LayerCake, CriteriaEvaluator

# Create a configuration
config = BucketConfig()
config.add_criteria(CriteriaEvaluator("RB_COL = Red"), required_quantity=10)

# Create a layer and add the bucket
layer = Layer()
layer.set_bucket(1, config)

# Create a LayerCake
cake = LayerCake()
cake.add_layer(layer)
```

### JSON Configuration

The `LayerCake` can be initialized from a JSON file, which defines the layers, buckets, and sorting criteria.

```python
cake = LayerCake.from_json("config.json")
```

#### JSON Structure
- **Outer List:** Represents the sequence of layers in the machine (Layer 1, Layer 2, etc.).
- **Layer Object:** A dictionary where keys are bucket positions (1-16) and values are lists of criteria.
- **Bucket Keys:** Can be a single integer (`"1"`) or a comma-separated list (`"1, 2, 3"`) to apply the same rules to multiple buckets.
- **Criteria Object:**
    - `expression`: A string defining the matching rule.
    - `required` (optional): An integer specifying how many items matching this rule should be collected before the rule is ignored.

#### Criteria Expressions
The `expression` string supports boolean logic and field comparisons:
- **Fields:** 
    - `RB_COL`: Color name or ID (e.g., `RB_COL = Red`, `RB_COL = 4`).
    - `RB_PT`: Part number (e.g., `RB_PT = 3001`).
    - `RB_PT_CAT`: Part Category name or ID (e.g., `RB_PT_CAT = Bricks`, `RB_PT_CAT = 11`).
    - `PT_VAL`: Part market value in dollars (e.g., `PT_VAL > 1.05`).
- **Operators:** 
    - Equality: `=`, `!=`.
    - Numeric: `>`, `<`, `>=`, `<=`.
- **Logic:** `AND`, `OR`, and parentheses `()` for grouping.
- **Shorthand (Pipe):** Use `|` to match multiple values in one field (e.g., `RB_COL = Red | Blue`).

#### Value-Based Sorting Examples
The `PT_VAL` field allows you to sort pieces based on their market value (loaded from `LegoData/RB_partvalues.csv`). If a piece is not found in the value database, it defaults to `0.0`.

- **High Value Sorting:** `PT_VAL > 2.00` (Collects pieces worth more than $2.00)
- **Bulk/Cheap Sorting:** `PT_VAL < 0.10` (Collects pieces worth less than 10 cents)
- **Value Range:** `PT_VAL >= 0.50 AND PT_VAL <= 1.50` (Collects mid-range pieces)
- **Specific High-Value Parts:** `RB_PT = 3001 AND PT_VAL > 1.00` (Collects 2x4 bricks only if they are valuable)

### Building Lego Sets (Inventory Sorting)

The multi-criteria system allows you to use a single bucket to collect all the parts needed for a specific Lego set or MOC (My Own Creation). By defining multiple criteria with specific `required` quantities, the bucket acts as an automated kit-builder.

**Example: Building a Small Kit**
If you want to collect the parts for a small set that requires:
- 5x Red 2x4 Bricks (Part 3001, Color 4)
- 2x Blue 2x2 Plates (Part 3022, Color 1)

You can define a bucket like this in your configuration:
```json
{
  "1": [
    { "expression": "RB_PT = 3001 AND RB_COL = 4", "required": 5 },
    { "expression": "RB_PT = 3022 AND RB_COL = 1", "required": 2 },
  ]
}
```

**How it works:**
1.  **Parallel Collection:** The bucket will accept any of these four parts/categories simultaneously.
2.  **Individual Limits:** Once it has 5 Red Bricks, it will stop accepting them for this bucket (allowing them to fall back to a general "Red" or "Bricks" bucket elsewhere).
3.  **Completion:** The bucket is only marked as "Full" (and eligible for automatic extension/spillover) once **every single criteria** in the list has reached its `required` quantity. This allows you to ensure a bucket contains a complete set of parts before the machine moves on to a new placeholder.

#### Detailed Example (`config.json`)
```json
[
    {
        "1, 2": [
            {
                "expression": "RB_COL = Red | Dark Red",
                "required": 50
            },
            {
                "expression": "RB_PT = 3001 AND RB_COL = White",
                "required": 10
            }
        ],
        "5": [
            {
                "expression": "RB_PT_CAT = Bricks OR RB_PT_CAT = Plates"
            }
        ]
    },
    {
        "16": [
            {
                "expression": "RB_COL != Black | White | Gray",
                "required": 100
            }
        ]
    }
]
```

In this example:
- **Layer 1:**
    - Buckets 1 and 2 will collect up to 50 Red or Dark Red pieces AND up to 10 White 2x4 Bricks (Part 3001). The bucket will continue to accept pieces for either criteria until its specific limit is reached, but the bucket is only considered "full" (triggering automatic extension) once **both** independent limits are met.
    - Bucket 5 will collect any piece that is categorized as either a "Brick" or a "Plate".
- **Layer 2:**
    - Bucket 16 will collect up to 100 pieces that are NOT Black, White, or Gray.

### Finding the Best Bucket
The `LayerCake` provides a method to determine where a piece should go based on the current state:

```python
# Returns (layer_num, bucket_id, status)
layer, bucket, status = cake.find_best_bucket(part_num="3001", color_id=4)

if status == SortingStatus.MATCH:
    print(f"Piece goes to Layer {layer}, Bucket {bucket}")
elif status == SortingStatus.DISABLED_REJECTED:
    print("Best match is currently disabled for maintenance.")
else:
    print("No matching bucket found.")
```

The algorithm selects the bucket based on:
1. **Highest Specificity:** The rule with the most constraints wins.
2. **Highest Layer:** If specificity is tied, the bucket further down the machine is chosen.
3. **Quantity Limits:** Rules that have reached their `required` quantity are ignored.

### Resetting State
You can clear the collected quantities at different levels:

```python
cake.reset_quantities()                    # Reset everything
cake.reset_layer_quantities(1)             # Reset Layer 1
cake.reset_bucket_quantities(1, 5)         # Reset Bucket 5 in Layer 1
```

### Summarizing State
You can retrieve the current state of the entire machine (including configurations, quantities, and enabled status) as a JSON string. There are two levels of detail available:

```python
# Get full state including all criteria configurations
full_summary = cake.summarize()

# Get concise state (only bucket names, quantities, and status)
state_summary = cake.summarize_state()
```

## Running Tests

Run the test suite:
```bash
python -m unittest tests.test_lego_sorter -v
```

## Example

Run the example demonstration:
```bash
python main.py
```
