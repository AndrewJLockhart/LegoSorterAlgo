"""Script to generate a sample RB_partvalues.csv file in LegoData."""

import csv
import os

# Path to the LegoData directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGO_DATA_DIR = os.path.join(BASE_DIR, "LegoData")
OUTPUT_FILE = os.path.join(LEGO_DATA_DIR, "RB_partvalues.csv")

def generate_sample_data():
    """
    Generates a sample list of 100 Lego parts (bricks and plates) 
    with hardcoded values for demonstration.
    """
    data = []
    
    # Common part numbers for Bricks and Plates
    # 3001: Brick 2x4, 3002: Brick 2x3, 3003: Brick 2x2, 3004: Brick 1x2, 3005: Brick 1x1
    # 3020: Plate 2x4, 3021: Plate 2x3, 3022: Plate 2x2, 3023: Plate 1x2, 3024: Plate 1x1
    bricks = [("3001", "Brick 2x4"), ("3002", "Brick 2x3"), ("3003", "Brick 2x2"), ("3004", "Brick 1x2"), ("3005", "Brick 1x1")]
    plates = [("3020", "Plate 2x4"), ("3021", "Plate 2x3"), ("3022", "Plate 2x2"), ("3023", "Plate 1x2"), ("3024", "Plate 1x1")]
    
    # Common Color IDs: 0: Black, 1: Blue, 2: Green, 4: Red, 14: Yellow, 15: White
    colors = [(0, "Black"), (1, "Blue"), (2, "Green"), (4, "Red"), (14, "Yellow"), (15, "White")]
    
    # Generate 100 entries (alternating bricks and plates across colors)
    for i in range(100):
        # Cycle through parts and colors to keep it deterministic but varied
        if i % 2 == 0:
            part_num, part_desc = bricks[(i // 2) % len(bricks)]
        else:
            part_num, part_desc = plates[(i // 2) % len(plates)]
            
        color_id, color_name = colors[i % len(colors)]
        
        # Hardcoded dollar value (e.g., $0.05 to $0.50 based on index)
        dollar_value = round(0.05 + (i % 10) * 0.05, 2)
        description = f"{color_name} {part_desc}"
        
        data.append({
            "part_num": part_num,
            "color_id": color_id,
            "DollarValue": dollar_value,
            "Description": description
        })
        
    return data

def main():
    """Main function to create the CSV file."""
    print(f"Generating sample data for {OUTPUT_FILE}...")
    
    if not os.path.exists(LEGO_DATA_DIR):
        print(f"Creating directory: {LEGO_DATA_DIR}")
        os.makedirs(LEGO_DATA_DIR)
        
    sample_data = generate_sample_data()
    
    fieldnames = ["part_num", "color_id", "DollarValue", "Description"]
    
    try:
        with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_data)
        print(f"Successfully created {OUTPUT_FILE} with {len(sample_data)} entries.")
    except Exception as e:
        print(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    main()
