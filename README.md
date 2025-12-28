# LegoSorterAlgo
Code to hold state of Lego Sorter Buckets and given a piece decide where it should go.

## Overview

This project provides shared code for describing the state of a Sorting Machine. The machine is composed of multiple layers, and each layer contains buckets at positions 1 to 16. Each bucket has a configuration that defines what should go into it using sorting criteria.

## Structure

The package consists of the following components:

### LegoCriteria
A class that represents a single criterion for sorting. Each criterion contains:
- A numeric value (`number`)
- A string value (`string`)

### BucketConfig
Defines the configuration for a bucket. Contains:
- A list of `LegoCriteria` objects that define what pieces should go into the bucket

### Bucket
Represents a single bucket in the sorting machine. Contains:
- A position (1-16) indicating where the bucket is located in a layer
- A `BucketConfig` object defining its sorting criteria

### Layer
Represents a single layer in the sorting machine. Contains:
- Multiple buckets at positions 1 to 16

### SortingMachine
The main object representing the entire sorting machine state. Contains:
- Multiple layers

## Installation

Clone the repository:
```bash
git clone https://github.com/AndrewJLockhart/LegoSorterAlgo.git
cd LegoSorterAlgo
```

## Usage

```python
from lego_sorter import LegoCriteria, BucketConfig, Bucket, Layer, SortingMachine

# Create a sorting machine
machine = SortingMachine()

# Create a layer
layer = Layer()

# Create a bucket with criteria
config = BucketConfig()
config.add_criteria(LegoCriteria(1, "red"))
config.add_criteria(LegoCriteria(2, "brick"))
bucket = Bucket(1, config)

# Add bucket to layer
layer.add_bucket(bucket)

# Add layer to machine
machine.add_layer(layer)
```

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
