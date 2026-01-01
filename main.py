"""Main program for the Lego Sorter Algorithm."""

from lego_sorter import BucketConfig, BucketCriteria, Layer, LayerCake, CriteriaEvaluator


def main():
    """Demonstrate how to create and use a sorting machine."""
    print("Creating a Layer Cake (Sorting Machine)...\n")
    
    # Create a Layer Cake
    cake = LayerCake()
    
    # Create Layer 1
    print("Creating Layer 1:")
    layer1 = Layer()
    
    # Bucket 1: Red bricks
    config1 = BucketConfig(
        criteria=(
            BucketCriteria(CriteriaEvaluator("(RB_COL = Red) OR (RB_COL = Dark Red)"), required_quantity=10),
            BucketCriteria(CriteriaEvaluator("RB_PT = 3001"), required_quantity=10) # Brick 2x4
        )
    )
    layer1.set_bucket(1, config1)
    print(f"  Added Bucket at position 1 with criteria: {config1.criteria}")
    
    # Bucket 5: Blue plates
    config2 = BucketConfig(
        criteria=(
            BucketCriteria(CriteriaEvaluator("RB_COL = Blue"), required_quantity=20),
            BucketCriteria(CriteriaEvaluator("RB_PT = 3020"), required_quantity=20) # Plate 2x4
        )
    )
    layer1.set_bucket(5, config2)
    print(f"  Added Bucket at position 5 with criteria: {config2.criteria}")
    
    cake.add_layer(layer1)
    
    # Create Layer 2
    print("\nCreating Layer 2:")
    layer2 = Layer()
    
    # Bucket 3: Green pieces
    config3 = BucketConfig(
        criteria=(
            BucketCriteria(CriteriaEvaluator("RB_COL = Green"), required_quantity=5),
        )
    )
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
            bucket = layer.get_bucket(position)
            if not bucket.config.criteria:
                continue
            print(f"  Position {position}:")
            for idx, criteria in enumerate(bucket.config.criteria):
                current = bucket.current_quantities[idx]
                req_str = f" (Required: {criteria.required_quantity})" if criteria.required_quantity is not None else ""
                print(f"    - {criteria.evaluator.expression}{req_str} [Current: {current}]")
    
    print(f"\n{'='*60}")
    print("Sorting Demonstration:")
    print(f"{'='*60}")
    
    test_pieces = [
        ("3001", 4),  # Red 2x4 Brick -> Matches Bucket 1 (RB_COL=Red OR RB_COL=Dark Red)
        ("3001", 15), # White 2x4 Brick -> Matches Bucket 1 (RB_PT=3001)
        ("3020", 1),  # Blue 2x4 Plate -> Matches Bucket 5 (RB_COL=Blue)
        ("3020", 2),  # Green 2x4 Plate -> Matches Layer 2, Bucket 3 (RB_COL=Green) - Tie-break to higher layer
        ("9999", 2),  # Green Piece -> Matches Layer 2, Bucket 3 (RB_COL=Green)
        ("1234", 0),  # Black Piece -> No match
    ]
    
    # Color IDs: 4=Red, 15=White, 1=Blue, 2=Green, 0=Black
    
    for part_num, color_id in test_pieces:
        l_num, b_id, status = cake.find_best_bucket(part_num, color_id)
        print(f"Part {part_num}, Color {color_id} -> Status: {status.value}", end="")
        if l_num:
            print(f", Layer: {l_num}, Bucket: {b_id}")
        else:
            print()

    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
