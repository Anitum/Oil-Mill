import pandas as pd
import numpy as np
import os
from pathlib import Path
import time

def process_cctv_directory(directory_path):
    """
    Process all CSV files in a directory and detect areas of interest with timestamps
    Also counts lines in each file, divides by n=90, and saves to a separate CSV
    Then deletes the processed files including empty ones
    
    Parameters:
    directory_path (str): Path to directory containing CSV files
    
    Returns:
    list: List of tuples containing (area_name, timestamp) for each detection
    """
    # Convert string path to Path object
    directory = Path(directory_path)
    input_dir = Path('input')
    
    if not directory.exists():
        raise ValueError(f"Directory not found: {directory}")
    
    # Create a DataFrame with area definitions
    areas_df = pd.DataFrame({
        'channel': [701, 301, 601,601,601],
        'name': ['Oil can Filling', 'Pouring raw Material', 'Mill1-2','Mill2-3','Mill3-4'],
        'x1': [800,1750,580,350,160],
        'y1': [350,450,115,150,180],
        'x2': [1350,1980,680,500,300],
        'y2': [800,870,305,360,380]
    })
    
    results = []
    file_counts = []
    n = 90
    
    # Get all CSV files
    csv_files = list(directory.glob('*.csv'))
    
    
    for csv_path in csv_files:
        try:
            # Force close any open file handles
            try:
                os.close(os.open(str(csv_path), os.O_RDONLY))
            except:
                pass
            
            # Check if file is empty
            if csv_path.stat().st_size == 0:
                print(f"Attempting to delete empty file: {csv_path}")
                try:
                    os.chmod(str(csv_path), 0o777)  # Change permissions
                    os.remove(str(csv_path))
                    time.sleep(0.1)  # Small delay after deletion
                except Exception as e:
                    print(f"Failed to delete empty file {csv_path}: {str(e)}")
                continue
            
            # Read CSV file
            df = pd.read_csv(csv_path, header=None)
            
            if len(df) == 0:
                print(f"Attempting to delete file with no data: {csv_path}")
                try:
                    os.chmod(str(csv_path), 0o777)
                    os.remove(str(csv_path))
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Failed to delete empty file {csv_path}: {str(e)}")
                continue
            
            # Process file counts
            line_count = len(df) / n
            file_counts.append({
                'file_name': csv_path.name,
                'count': line_count
            })
            
            # Calculate center points
            df['center_x'] = df[2] + (df[4] / 2)
            df['center_y'] = df[3] + (df[5] / 2)
            
            # Extract channel and timestamp
            filename_parts = csv_path.stem.split('_')
            channel = int(filename_parts[0].replace('channel', ''))
            timestamp = filename_parts[1][1:]
            
            # Get area information
            area = areas_df[areas_df['channel'] == channel].iloc[0] if not areas_df[areas_df['channel'] == channel].empty else None
            
            if area is not None:
                # Check points in area
                points_in_area = (
                    (df['center_x'] >= area['x1']) &
                    (df['center_x'] <= area['x2']) &
                    (df['center_y'] >= area['y1']) &
                    (df['center_y'] <= area['y2'])
                )
                
                if points_in_area.any():
                    results.append((area['name'], timestamp))
            
            # Delete processed file
            print(f"Attempting to delete processed file: {csv_path}")
            try:
                df = None  # Release DataFrame
                os.chmod(str(csv_path), 0o777)  # Ensure write permissions
                os.remove(str(csv_path))
                time.sleep(0.1)  # Small delay after deletion
            except Exception as e:
                print(f"First deletion attempt failed: {str(e)}")
                try:
                    time.sleep(0.5)  # Longer delay before second attempt
                    csv_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Second deletion attempt failed: {str(e)}")
                    
        except Exception as e:
            print(f"Error processing file {csv_path}: {str(e)}")
            continue
    
    # Save results
    if results:
        output_df = pd.DataFrame(results, columns=['Area', 'Time'])
        output_df.to_csv(input_dir / 'hue_activity_time.csv', index=False)
    
    # Save file counts
    if file_counts:
        counts_df = pd.DataFrame(file_counts)
        if Path('file_counts.csv').exists():
            counts_df.to_csv(input_dir / 'file_counts.csv', mode='a', header=False, index=False)
        else:
            counts_df.to_csv(input_dir / 'file_counts.csv', index=False)
    
    return results

# Test the function
if __name__ == "__main__":
    try:
        directory = r"/home/mridul/Oil-Mill/testing/s3_results/s3_results"
        print(f"Processing directory: {directory}")
        
        detections = process_cctv_directory(directory)
        
        if detections:
            print("\nResults saved to 'hue_activity_time.csv'")
            print("File counts saved to 'file_counts.csv'")
            print("\nDetections found:")
            for area_name, timestamp in detections:
                print(f"{area_name}, {timestamp}")
        else:
            print("No detections found in areas of interest")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")