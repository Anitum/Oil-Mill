import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from datetime import datetime

def create_heatmap(channel_num, time_decay_hours=24, resolution=(1920, 1080)):
    # Get all files for specified channel
    files = glob.glob(f"s3_results/channel{channel_num}_*_results.csv")
    
    # Initialize heatmap matrix
    heatmap = np.zeros(resolution)
    
    current_time = datetime.now()
    
    for file_path in files:
        # Skip empty files
        if os.path.getsize(file_path) == 0:
            continue
            
        # Extract timestamp from filename
        try:
            # Get just the filename without path
            filename = os.path.basename(file_path)
            # Split by underscore and get the timestamp part
            timestamp_str = filename.split('_')[1]  # Gets '20241229T074802'
            file_time = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
        except Exception as e:
            print(f"Error parsing timestamp from {filename}: {e}")
            continue
        
        # Calculate time weight (newer files have higher weight)
        hours_diff = (current_time - file_time).total_seconds() / 3600
        time_weight = np.exp(-hours_diff / time_decay_hours)  # exponential decay
        
        try:
            # Read CSV
            df = pd.read_csv(file_path, header=None)
            if len(df.columns) != 6:
                continue
                
            # Rename columns for clarity
            df.columns = ['frame', 'id', 'left', 'top', 'width', 'height']
            
            # Calculate center points of each detection
            centers_x = df['left'] + df['width'] / 2
            centers_y = df['top'] + df['height'] / 2
            
            # Add weighted points to heatmap
            for x, y in zip(centers_x, centers_y):
                if 0 <= x < resolution[0] and 0 <= y < resolution[1]:
                    # Add Gaussian blur around each point
                    y_idx, x_idx = np.ogrid[-20:21, -20:21]
                    gaussian = np.exp(-(x_idx*x_idx + y_idx*y_idx) / 100)
                    
                    # Calculate bounds for the gaussian
                    x_start = max(0, int(x) - 20)
                    x_end = min(resolution[0], int(x) + 21)
                    y_start = max(0, int(y) - 20)
                    y_end = min(resolution[1], int(y) + 21)
                    
                    # Add weighted gaussian to heatmap
                    heatmap[y_start:y_end, x_start:x_end] += gaussian[:y_end-y_start, :x_end-x_start] * time_weight
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    return heatmap

def plot_heatmap(heatmap, channel_num, save_path=None):
    plt.figure(figsize=(15, 8))
    plt.imshow(heatmap, cmap='hot')
    plt.colorbar(label='Detection Density')
    plt.title(f'Detection Heatmap for Channel {channel_num}')
    plt.xlabel('X coordinate')
    plt.ylabel('Y coordinate')
    
    if save_path:
        plt.savefig(save_path)
        print(f"Heatmap saved as {save_path}")
    
    # Close the figure to free memory
    plt.close()

def main():
    # Example usage
    channel_num = 201
    time_decay_hours = 24  # Adjust this value to control how quickly old detections fade
    
    # Create and plot heatmap
    print("Creating heatmap...")
    heatmap = create_heatmap(channel_num, time_decay_hours)
    
    # Save the heatmap
    save_path = f'heatmap_channel_{channel_num}.png'
    plot_heatmap(heatmap, channel_num, save_path)
    
    print("Done! Check the saved heatmap image.")

if __name__ == "__main__":
    main()
