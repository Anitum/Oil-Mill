import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from datetime import datetime

def create_gaussian_kernel(size=41):
    """Create a 2D Gaussian kernel."""
    x, y = np.meshgrid(np.linspace(-2, 2, size), np.linspace(-2, 2, size))
    d = np.sqrt(x*x + y*y)
    sigma = 1.0
    g = np.exp(-(d**2 / (2.0 * sigma**2)))
    return g / g.sum()

def create_heatmap(channel_num, time_decay_hours=24, resolution=(1920, 1080)):
    # Get all files for specified channel
    files = glob.glob(f"s3_results/channel{channel_num}_*_results.csv")
    
    # Initialize heatmap matrix
    heatmap = np.zeros(resolution)
    
    # Create Gaussian kernel once
    kernel_size = 41
    gaussian_kernel = create_gaussian_kernel(kernel_size)
    kernel_radius = kernel_size // 2
    
    current_time = datetime.now()
    
    for file_path in files:
        # Skip empty files
        if os.path.getsize(file_path) == 0:
            continue
            
        try:
            # Get just the filename without path
            filename = os.path.basename(file_path)
            # Split by underscore and get the timestamp part
            timestamp_str = filename.split('_')[1]
            file_time = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
        except Exception as e:
            print(f"Error parsing timestamp from {filename}: {e}")
            continue
        
        # Calculate time weight
        hours_diff = (current_time - file_time).total_seconds() / 3600
        time_weight = np.exp(-hours_diff / time_decay_hours)
        
        try:
            # Read CSV
            df = pd.read_csv(file_path, header=None)
            if len(df.columns) != 6:
                continue
                
            # Rename columns
            df.columns = ['frame', 'id', 'left', 'top', 'width', 'height']
            
            # Calculate center points
            centers_x = df['left'] + df['width'] / 2
            centers_y = df['top'] + df['height'] / 2
            
            # Add weighted points to heatmap
            for x, y in zip(centers_x, centers_y):
                x, y = int(x), int(y)
                
                # Calculate boundaries for the kernel
                y_start = max(0, y - kernel_radius)
                y_end = min(resolution[1], y + kernel_radius + 1)
                x_start = max(0, x - kernel_radius)
                x_end = min(resolution[0], x + kernel_radius + 1)
                
                # Calculate kernel boundaries
                k_y_start = kernel_radius - (y - y_start)
                k_y_end = kernel_radius + (y_end - y)
                k_x_start = kernel_radius - (x - x_start)
                k_x_end = kernel_radius + (x_end - x)
                
                # Add the appropriate section of the kernel to the heatmap
                kernel_section = gaussian_kernel[k_y_start:k_y_end, k_x_start:k_x_end]
                heatmap[y_start:y_end, x_start:x_end] += kernel_section * time_weight
                
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
    
    plt.close()

def main():
    channel_num = 201
    time_decay_hours = 24
    
    print("Creating heatmap...")
    heatmap = create_heatmap(channel_num, time_decay_hours)
    
    save_path = f'heatmap_channel_{channel_num}.png'
    plot_heatmap(heatmap, channel_num, save_path)
    
    print("Done! Check the saved heatmap image.")

if __name__ == "__main__":
    main()
