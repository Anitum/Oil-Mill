import os
import pandas as pd
import glob
from pathlib import Path

def count_max_people_per_file(file_path):
    try:
        # Read CSV without headers
        df = pd.read_csv(file_path, header=None)
        
        if df.empty:
            return 0
        
        # Each row represents a detection, so count detections per frame
        # Frame number is in the first column (index 0)
        frame_people_counts = df.groupby(0)[1].nunique()
        
        # Return the maximum count
        return frame_people_counts.max() if not frame_people_counts.empty else 0
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def main():
    # Get all CSV files in the processing directory
    processing_dir = "../processing"    
    csv_files = glob.glob(os.path.join(processing_dir, "*.csv"))
    
    # Create a list to store results
    results = []
    
    # Process each file
    for file_path in csv_files:
        # Get file name and remove '_results.csv'
        file_name = os.path.basename(file_path)
        file_name = file_name.replace('_results.csv', '')
        max_people = count_max_people_per_file(file_path)
        results.append({"file_name": file_name, "count": max_people})
    
    # Create a dataframe from results
    results_df = pd.DataFrame(results)
    
    # Write to output file
    output_file = os.path.join("input", "file_counts.csv")    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save to CSV
    results_df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
