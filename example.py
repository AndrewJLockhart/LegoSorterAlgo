"""Example usage of the Lego Sorter Algorithm package."""

from lego_sorter import LegoCriteria, BucketConfig, Bucket, Layer, SortingMachine


def main():
    """Demonstrate how to create and use a sorting machine."""
    print("Creating a Sorting Machine...\n")
    
    # Create a sorting machine
    machine = SortingMachine()
    
    # Create Layer 1
    print("Creating Layer 1:")
    layer1 = Layer()
    
    # Bucket 1: Red bricks
    config1 = BucketConfig()
    config1.add_criteria(LegoCriteria(1, "red"))
    config1.add_criteria(LegoCriteria(2, "brick"))
    bucket1 = Bucket(1, config1)
    layer1.add_bucket(bucket1)
    print(f"  Added Bucket at position 1 with criteria: {config1.criteria}")
    
    # Bucket 5: Blue plates
    config2 = BucketConfig([LegoCriteria(10, "blue"), LegoCriteria(11, "plate")])
    bucket2 = Bucket(5, config2)
    layer1.add_bucket(bucket2)
    print(f"  Added Bucket at position 5 with criteria: {config2.criteria}")
    
    # Bucket 10: Green tiles
    config3 = BucketConfig([LegoCriteria(20, "green"), LegoCriteria(21, "tile")])
    bucket3 = Bucket(10, config3)
    layer1.add_bucket(bucket3)
    print(f"  Added Bucket at position 10 with criteria: {config3.criteria}")
    
    machine.add_layer(layer1)
    
    # Create Layer 2
    print("\nCreating Layer 2:")
    layer2 = Layer()
    
    # Bucket 3: Yellow pieces
    config4 = BucketConfig([LegoCriteria(30, "yellow")])
    bucket4 = Bucket(3, config4)
    layer2.add_bucket(bucket4)
    print(f"  Added Bucket at position 3 with criteria: {config4.criteria}")
    
    # Bucket 16: White pieces
    config5 = BucketConfig([LegoCriteria(40, "white")])
    bucket5 = Bucket(16, config5)
    layer2.add_bucket(bucket5)
    print(f"  Added Bucket at position 16 with criteria: {config5.criteria}")
    
    machine.add_layer(layer2)
    
    # Display the machine structure
    print(f"\n{'='*60}")
    print("Sorting Machine State:")
    print(f"{'='*60}")
    print(f"Total layers: {machine.layer_count()}")
    
    for i in range(machine.layer_count()):
        layer = machine.get_layer(i)
        print(f"\nLayer {i + 1}:")
        for position in sorted(layer.buckets.keys()):
            bucket = layer.get_bucket(position)
            print(f"  Position {position}:")
            for criteria in bucket.config.criteria:
                print(f"    - {criteria}")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
