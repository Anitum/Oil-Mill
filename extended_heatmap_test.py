import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from datetime import datetime, timedelta
import cv2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('heatmap_generation.log')
    ]
)

def parse_timestamp(filename):
    """Extract timestamp from filename format: channel{XXX}_{YYYYMMDD}T{HHMMSS}_results.csv"""
    try:
        timestamp_str = filename.split('_')[1]
        return datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
    except Exception as e:
        logging.error(f"Error parsing timestamp from {filename}: {e}")
        return None

def get_channel_number(filename):
    """Extract channel number from filename"""
    try:
        return int(filename.split('_')[0].replace('channel', ''))
    except Exception as e:
        logging.error(f"Error extracting channel number from {filename}: {e}")
        return None

def load_background_image(channel_number, photo_path="Photo"):
    """Load background image for specific channel"""    
    image_path = os.path.join(photo_path, f"{channel_number}.jpg")
    if os.path.exists(image_path):
        img = cv2.imread(image_path)
        logging.info(f"Loaded background image for channel {channel_number} with shape {img.shape}")
        return img
    else:
        logging.warning(f"No image found for channel {channel_number} at {image_path}")
        return None

def is_valid_csv(file_path):
    """Check if CSV file is valid and has required columns"""
    try:
        df = pd.read_csv(file_path, header=None)
        if len(df.columns) != 6:
            logging.warning(f"Invalid column count in {file_path}: expected 6, got {len(df.columns)}")
            return False
        # Optional: Add additional validation if needed
        return True
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return False

def apply_gaussian_overlay(heatmap, x, y, resolution, weight, radius=40):  # Increased radius
    """
    Apply Gaussian overlay with enhanced intensity
    """
    try:
        x, y = int(x), int(y)
        
        # Create Gaussian kernel with higher intensity
        y_indices, x_indices = np.ogrid[-radius:radius+1, -radius:radius+1]
        gaussian = np.exp(-(x_indices*x_indices + y_indices*y_indices) / (2 * (radius/3)**2))  # Adjusted spread
        gaussian = gaussian * 1.5  # Increase intensity
        
        # Calculate valid ranges
        y_start = max(0, y - radius)
        y_end = min(resolution[1], y + radius + 1)
        x_start = max(0, x - radius)
        x_end = min(resolution[0], x + radius + 1)
        
        # Calculate corresponding ranges in Gaussian kernel
        g_y_start = max(0, radius - (y - y_start))
        g_y_end = min(gaussian.shape[0], gaussian.shape[0] - (max(0, (y + radius + 1) - y_end)))
        g_x_start = max(0, radius - (x - x_start))
        g_x_end = min(gaussian.shape[1], gaussian.shape[1] - (max(0, (x + radius + 1) - x_end)))
        
        # Get slices
        heatmap_slice = heatmap[y_start:y_end, x_start:x_end]
        gaussian_slice = gaussian[g_y_start:g_y_end, g_x_start:g_x_end]
        
        # Ensure shapes match
        min_y = min(heatmap_slice.shape[0], gaussian_slice.shape[0])
        min_x = min(heatmap_slice.shape[1], gaussian_slice.shape[1])
        
        # Apply overlay with increased weight
        heatmap[y_start:y_start+min_y, x_start:x_start+min_x] += (
            gaussian_slice[:min_y, :min_x] * (weight * 2.0)  # Doubled the weight
        )
        
    except Exception as e:
        logging.error(f"Error applying Gaussian overlay at ({x}, {y}): {e}")

def plot_channel_heatmaps(channel_heatmaps, save_dir=None, alpha=0.7):
    """
    Plot heatmaps with enhanced visibility
    """
    for channel, (heatmap, background_image) in channel_heatmaps.items():
        plt.figure(figsize=(16, 9), frameon=False)
        
        # Enhance contrast of the heatmap
        if np.max(heatmap) > 0:
            # Apply stronger normalization
            heatmap = np.power(heatmap / np.max(heatmap), 0.7)  # Adjust gamma for better visibility
        
        # Darken the background slightly to make heatmap more visible
        darkened_bg = cv2.convertScaleAbs(background_image, alpha=0.7, beta=0)
        
        # Display darkened background
        plt.imshow(cv2.cvtColor(darkened_bg, cv2.COLOR_BGR2RGB))
        
        # Overlay heatmap with increased alpha and different colormap
        plt.imshow(heatmap, 
                  cmap='jet',  # Changed from 'hot' to 'jet' for better visibility
                  alpha=alpha,
                  extent=[0, background_image.shape[1], background_image.shape[0], 0])
        
        if save_dir:
            save_path = os.path.join(save_dir, f'heatmap_channel_{channel}.png')
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=300)  # Increased DPI
            
        plt.close()


def create_channel_heatmaps(hours_ago=None, start_time=None, end_time=None, time_decay=0.95):
    """
    Create heatmaps for each channel based on CSV data.
    """
    logging.info("Starting heatmap creation process")
    
    # Define all required channels
    REQUIRED_CHANNELS = ['101', '201', '301', '401', '501', '601', '701']
    
    # Initialize storage for heatmaps
    channel_heatmaps = {}
    
    # Get list of CSV files
    csv_files = glob.glob(os.path.join('Results', 'channel*_results.csv'))
    if not csv_files:
        logging.warning("No CSV files found in Results directory")
    
    # Process each channel
    for channel_str in REQUIRED_CHANNELS:
        channel = int(channel_str)
        logging.info(f"Processing channel {channel}")
        
        # Load background image
        background = load_background_image(channel)
        if background is None:
            logging.warning(f"No background image for channel {channel} - creating default background")
            # Create a default black background if image is missing
            background = np.zeros((720, 1280, 3), dtype=np.uint8)
            
        # Initialize heatmap with background image dimensions
        resolution = (background.shape[1], background.shape[0])  # width, height
        heatmap = np.zeros(resolution[::-1])  # height, width for the heatmap
        
        # Get all files for this channel
        channel_files = [f for f in csv_files if get_channel_number(os.path.basename(f)) == channel]
        
        if not channel_files:
            logging.warning(f"No CSV files found for channel {channel}")
        
        # Process each file
        for file_path in sorted(channel_files):
            if not is_valid_csv(file_path):
                continue
                
            file_timestamp = parse_timestamp(os.path.basename(file_path))
            if not file_timestamp:
                continue
                
            # Check if file is within time range
            if hours_ago is not None:
                cutoff_time = datetime.now() - timedelta(hours=hours_ago)
                if file_timestamp < cutoff_time:
                    continue
            elif start_time and end_time:
                if not (start_time <= file_timestamp <= end_time):
                    continue
            
            # Calculate time-based weight
            if hours_ago is not None:
                time_diff = (datetime.now() - file_timestamp).total_seconds() / 3600
                weight = time_decay ** time_diff
            else:
                weight = 1.0
            
            try:
                # Read and process the CSV file
                df = pd.read_csv(file_path, header=None)
                
                # Process detections
                for _, row in df.iterrows():
                    x1, y1, x2, y2 = row[0:4]
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    apply_gaussian_overlay(heatmap, center_x, center_y, resolution, weight)
                    
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                continue
        
        # Store the heatmap and background for this channel
        channel_heatmaps[channel] = (heatmap, background)
        logging.info(f"Completed processing for channel {channel}")
    
    return channel_heatmaps

if __name__ == "__main__":
    logging.info("Starting heatmap generation script")
    
    # Create output directory if it doesn't exist
    output_dir = 'app/heatmap_outputs'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create heatmaps for all channels
    channel_heatmaps = create_channel_heatmaps(
        hours_ago=100,
        time_decay=0.95
    )
    
    # Plot and save the heatmaps
    plot_channel_heatmaps(channel_heatmaps, save_dir=output_dir, alpha=0.6)
    
    logging.info("Completed heatmap generation")