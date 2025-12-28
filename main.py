"""Main program for the Lego Sorter Algorithm."""

from lego_sorter import BucketConfig, Layer, LayerCake, CriteriaEvaluator


def main():
    """Demonstrate how to create and use a sorting machine."""
    print("Creating a Layer Cake (Sorting Machine)...\n")
    
    # Create a Layer Cake
    cake = LayerCake()
    
    # Create Layer 1
    print("Creating Layer 1:")
    layer1 = Layer()
    
    # Bucket 1: Red bricks
    # Criteria: (Evaluator, Required, Current)
    config1 = BucketConfig()
    config1.add_criteria(CriteriaEvaluator("RB_COL = Red"), required_quantity=10)
    config1.add_criteria(CriteriaEvaluator("RB_PT = 3001")) # Brick 2x4
    layer1.set_bucket(1, config1)
    print(f"  Added Bucket at position 1 with criteria: {config1.criteria}")
    
    # Bucket 5: Blue plates
    config2 = BucketConfig()
    config2.add_criteria(CriteriaEvaluator("RB_COL = Blue"))
    config2.add_criteria(CriteriaEvaluator("RB_PT = 3020")) # Plate 2x4
    layer1.set_bucket(5, config2)
    print(f"  Added Bucket at position 5 with criteria: {config2.criteria}")
    
    cake.add_layer(layer1)
    
    # Create Layer 2
    print("\nCreating Layer 2:")
    layer2 = Layer()
    
    # Bucket 3: Green pieces
    config3 = BucketConfig()
    config3.add_criteria(CriteriaEvaluator("RB_COL = Green"), required_quantity=5)
    layer2.set_bucket(3, config3)
    print(f"  Added Bucket at position 3 with criteria: {config3.criteria}")
    
    cake.add_layer(layer2)
    
    # Display the machine structure
    print(f"\n{'='*60}")
    print("Layer Cake State:")
    print(f"{'='*60}")
    print(f"Total layers: {cake.layer_count()}")
    
    for i in range(cake.layer_count()):
        layer = cake.get_layer(i)
        print(f"\nLayer {i + 1}:")
        for position in sorted(layer.buckets.keys()):
            bucket_config = layer.get_bucket(position)
            print(f"  Position {position}:")
            for criteria_tuple in bucket_config.criteria:
                evaluator, required, current = criteria_tuple
                req_str = f" (Required: {required})" if required is not None else ""
                print(f"    - {evaluator.expression}{req_str} [Current: {current}]")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
