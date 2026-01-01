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
    
    # Bucket 10: High value pieces
    config4 = BucketConfig(
        criteria=(
            BucketCriteria(CriteriaEvaluator("PT_VAL > 1.00"), required_quantity=5),
        )
    )
    layer2.set_bucket(10, config4)
    print(f"  Added Bucket at position 10 with criteria: {config4.criteria}")
    
    cake.add_layer(layer2)
    
    # Display the machine structure using the summarize_state method
    print(f"\n{'='*60}")
    print("Initial Layer Cake State (JSON):")
    print(f"{'='*60}")
    print(cake.summarize_state())
    
    print(f"\n{'='*60}")
    print("Sorting Demonstration:")
    print(f"{'='*60}")
    
    test_pieces = [
        ("3001", 4),  # Red 2x4 Brick -> Matches Bucket 1 (RB_COL=Red OR RB_COL=Dark Red)
        ("3001", 15), # White 2x4 Brick -> Matches Bucket 1 (RB_PT=3001)
        ("3020", 1),  # Blue 2x4 Plate -> Matches Bucket 5 (RB_COL=Blue)
        ("3020", 2),  # Green 2x4 Plate -> Matches Layer 2, Bucket 3 (RB_COL=Green) - Tie-break to higher layer
        ("9999", 2),  # Green Piece -> Matches Layer 2, Bucket 3 (RB_COL=Green)
        ("3001", 1),  # Blue 2x4 Brick -> Might match PT_VAL > 1.00 if in RB_partvalues.csv
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

    print(f"\n{'='*60}")
    print("Final Layer Cake State (JSON):")
    print(f"{'='*60}")
    print(cake.summarize_state())

    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
