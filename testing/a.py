import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heatmap.log'),
        logging.StreamHandler()
    ]
)

def create_heatmap(channel_num, time_decay_hours=24, resolution=(1920, 1080)):
    files = glob.glob(f"s3_results/channel{channel_num}_*_results.csv")
    heatmap = np.zeros(resolution)
    current_time = datetime.now()
    
    logging.info(f"Found {len(files)} files for channel {channel_num}")
    
    for file_path in files:
        if os.path.getsize(file_path) == 0:
            logging.info(f"Skipping empty file: {file_path}")
            continue
            
        try:
            filename = os.path.basename(file_path)
            timestamp_str = filename.split('_')[1]
            file_time = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
            
            hours_diff = (current_time - file_time).total_seconds() / 3600
            time_weight = np.exp(-hours_diff / time_decay_hours)
            
            logging.debug(f"Processing {filename} with time weight {time_weight:.4f}")
            
            # Read CSV
            df = pd.read_csv(file_path, header=None)
            if len(df.columns) != 6:
                logging.warning(f"Incorrect number of columns in {filename}: {len(df.columns)}")
                continue
                
            df.columns = ['frame', 'id', 'left', 'top', 'width', 'height']
            logging.debug(f"Found {len(df)} detections in {filename}")
            
            # Calculate center points of each detection
            centers_x = df['left'] + df['width'] / 2
            centers_y = df['top'] + df['height'] / 2
            
            # Add weighted points to heatmap
            for idx, (x, y) in enumerate(zip(centers_x, centers_y)):
                try:
                    if 0 <= x < resolution[0] and 0 <= y < resolution[1]:
                        # Calculate gaussian kernel size based on detection size
                        kernel_size = 20  # default size
                        y_idx, x_idx = np.ogrid[-kernel_size:kernel_size+1, -kernel_size:kernel_size+1]
                        gaussian = np.exp(-(x_idx*x_idx + y_idx*y_idx) / 100)
                        
                        # Calculate bounds for the gaussian
                        x_start = max(0, int(x) - kernel_size)
                        x_end = min(resolution[0], int(x) + kernel_size + 1)
                        y_start = max(0, int(y) - kernel_size)
                        y_end = min(resolution[1], int(y) + kernel_size + 1)
                        
                        # Get the actual sizes of the region we're updating
                        region_height = y_end - y_start
                        region_width = x_end - x_start
                        
                        # Crop gaussian to match the region size
                        gaussian_cropped = gaussian[:region_height, :region_width]
                        
                        # Update heatmap
                        heatmap[y_start:y_end, x_start:x_end] += gaussian_cropped * time_weight
                        
                except Exception as e:
                    logging.error(f"Error processing detection {idx} in {filename}: {e}")
                    logging.error(f"Detection details - x: {x}, y: {y}, bounds: ({x_start}:{x_end}, {y_start}:{y_end})")
                    continue
                    
        except Exception as e:
            logging.error(f"Error processing file {filename}: {e}")
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
        logging.info(f"Heatmap saved as {save_path}")
    
    plt.close()

def main():
    channel_num = 201
    time_decay_hours = 24
    
    logging.info("Starting heatmap generation...")
    
    try:
        heatmap = create_heatmap(channel_num, time_decay_hours)
        
        # Add some statistics about the heatmap
        logging.info(f"Heatmap statistics:")
        logging.info(f"Max value: {np.max(heatmap):.4f}")
        logging.info(f"Mean value: {np.mean(heatmap):.4f}")
        logging.info(f"Non-zero elements: {np.count_nonzero(heatmap)}")
        
        save_path = f'heatmap_channel_{channel_num}.png'
        plot_heatmap(heatmap, channel_num, save_path)
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise
    
    logging.info("Heatmap generation completed successfully")

if __name__ == "__main__":
    main()
