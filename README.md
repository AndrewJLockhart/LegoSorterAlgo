# LegoSorterAlgo
Code to hold state of Lego Sorter Buckets and given a piece decide where it should go.

## Overview

This project provides shared code for describing the state of a Sorting Machine. The machine is composed of multiple layers, and each layer contains buckets at positions 1 to 16. Each bucket has a configuration that defines what should go into it using sorting criteria.

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

You can load the machine configuration from a JSON file:

```python
cake = LayerCake.from_json("config.json")
```

Example `config.json`:
```json
[
    {
        "1, 2": [
            {"expression": "RB_COL = Red", "required": 10},
            {"expression": "RB_PT = 3001"}
        ],
        "5": [
            {"expression": "RB_COL = Blue"}
        ]
    },
    {
        "3": [
            {"expression": "RB_COL = Green", "required": 5}
        ]
    }
]
```
- The outer list represents layers.
- Each object represents a layer, mapping bucket positions to criteria.
- Keys can be single positions ("1") or comma-separated lists ("1, 2") to apply the same configuration to multiple buckets.

For a complete example, see `example.py`.

## Running Tests

Run the test suite:
```bash
python -m unittest tests.test_lego_sorter -v
```

## Example

Run the example demonstration:
```bash
python example.py
```
