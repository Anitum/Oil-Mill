import os
import pandas as pd
from datetime import datetime

# Print current directory
print(f"Current directory: {os.getcwd()}")

# Check if input directory exists
input_dir = "input"
if not os.path.exists(input_dir):
    print(f"Input directory not found, creating it")
    os.makedirs(input_dir, exist_ok=True)

# List all files in input directory
print(f"Files in input directory:")
for file in os.listdir(input_dir):
    print(f"  - {file}")

# Try to read the CSV file directly
csv_file = os.path.join(input_dir, "camera501_2025-02-22.csv")
if os.path.exists(csv_file):
    print(f"Found CSV file: {csv_file}")
    try:
        df = pd.read_csv(csv_file)
        print(f"CSV content:")
        print(df.head())
        
        # Check column names
        print(f"Column names: {df.columns.tolist()}")
        
        # Check for True values in motion_status2
        if 'motion_status2' in df.columns:
            true_values = df[df['motion_status2'] == True]
            print(f"Found {len(true_values)} rows with motion_status2 = True")
        else:
            print("motion_status2 column not found!")
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
else:
    print(f"CSV file not found: {csv_file}")

# Try to import the processor
try:
    from machine_usage_processor import MachineUsageProcessor
    print("Successfully imported MachineUsageProcessor")
    
    # Create processor instance
    processor = MachineUsageProcessor()
    
    # Run the processor with verbose output
    print("Running processor...")
    result = processor.process_and_save()
    
    print("Processing complete. Result:")
    if result and 'data' in result:
        for entry in result['data']:
            timestamp = entry['timestamp']
            filter_usage = entry['by_area']['filter']
            crusher_usage = entry['by_area']['crusher']
            filling_usage = entry['by_area']['filling']
            
            if filter_usage > 0 or crusher_usage > 0 or filling_usage > 0:
                print(f"{timestamp}: filter={filter_usage}, crusher={crusher_usage}, filling={filling_usage}")
    
except ImportError as e:
    print(f"Error importing MachineUsageProcessor: {str(e)}")
except Exception as e:
    print(f"Error running processor: {str(e)}")
    import traceback
    traceback.print_exc()