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

def apply_gaussian_overlay(heatmap, x, y, resolution, weight, radius=20):
    """Apply Gaussian overlay at specified position with boundary handling"""
    try:
        x, y = int(x), int(y)
        
        # Log position and boundary information
        logging.debug(f"Applying Gaussian at position ({x}, {y}) with resolution {resolution}")
        
        # Create full Gaussian kernel
        y_indices, x_indices = np.ogrid[-radius:radius+1, -radius:radius+1]
        gaussian = np.exp(-(x_indices*x_indices + y_indices*y_indices) / 100)
        
        # Calculate valid ranges for both source and target
        x_start = max(0, x - radius)
        x_end = min(resolution[0], x + radius + 1)
        y_start = max(0, y - radius)
        y_end = min(resolution[1], y + radius + 1)
        
        # Calculate corresponding ranges in the Gaussian kernel
        g_x_start = max(0, radius - (x - x_start))
        g_x_end = gaussian.shape[1] - max(0, (x + radius + 1) - x_end)
        g_y_start = max(0, radius - (y - y_start))
        g_y_end = gaussian.shape[0] - max(0, (y + radius + 1) - y_end)
        
        # Log array shapes and ranges
        logging.debug(f"Heatmap slice range: y[{y_start}:{y_end}], x[{x_start}:{x_end}]")
        logging.debug(f"Gaussian slice range: y[{g_y_start}:{g_y_end}], x[{g_x_start}:{g_x_end}]")
        
        # Get the slices
        heatmap_slice = heatmap[y_start:y_end, x_start:x_end]
        gaussian_slice = gaussian[g_y_start:g_y_end, g_x_start:g_x_end]
        
        # Verify shapes match
        if heatmap_slice.shape != gaussian_slice.shape:
            logging.warning(
                f"Shape mismatch at position ({x}, {y}): "
                f"heatmap_slice {heatmap_slice.shape} vs "
                f"gaussian_slice {gaussian_slice.shape}"
            )
            # Adjust slices to match smaller dimension
            min_y = min(heatmap_slice.shape[0], gaussian_slice.shape[0])
            min_x = min(heatmap_slice.shape[1], gaussian_slice.shape[1])
            heatmap_slice = heatmap_slice[:min_y, :min_x]
            gaussian_slice = gaussian_slice[:min_y, :min_x]
            
        # Apply the overlay
        heatmap[y_start:y_start+heatmap_slice.shape[0], 
                x_start:x_start+heatmap_slice.shape[1]] += gaussian_slice * weight
        
    except Exception as e:
        logging.error(f"Error applying Gaussian overlay at ({x}, {y}): {e}")

def create_channel_heatmaps(start_time=None, end_time=None, hours_ago=None, 
                          time_decay=0.9, photo_path="/home/ubuntu/Oil-Mill/Photo", results_path="/home/ubuntu/processing"):
    """Create heatmaps for each channel using data from specified time period"""
    logging.info("Starting heatmap creation process")
    
    # Set time range
    current_time = datetime.now()
    if start_time and end_time:
        cutoff_start = start_time
        cutoff_end = end_time
    elif hours_ago is not None:
        cutoff_start = current_time - timedelta(hours=hours_ago)
        cutoff_end = current_time
    else:
        raise ValueError("Must provide either start_time and end_time, or hours_ago")
    
    logging.info(f"Time range: {cutoff_start} to {cutoff_end}")
    
    # Get and group files by channel
    files = glob.glob(os.path.join(results_path, "*_results.csv"))
    if not files:
        logging.warning("No result files found in Results directory")
        return {}
    
    logging.info(f"Found {len(files)} CSV files")
    
    channel_files = {}
    for file_path in files:
        if not is_valid_csv(file_path):
            continue
            
        filename = os.path.basename(file_path)
        channel = get_channel_number(filename)
        timestamp = parse_timestamp(filename)
        
        if channel is None or timestamp is None:
            continue
            
        if cutoff_start <= timestamp <= cutoff_end:
            if channel not in channel_files:
                channel_files[channel] = []
            channel_files[channel].append((file_path, timestamp))
    
    logging.info(f"Processing {len(channel_files)} channels: {list(channel_files.keys())}")
    
    # Create heatmaps for each channel
    channel_heatmaps = {}
    total_duration = (cutoff_end - cutoff_start).total_seconds()
    
    for channel, files_with_timestamps in channel_files.items():
        logging.info(f"Processing channel {channel}")
        
        # Load background image for this channel
        background_image = load_background_image(channel, photo_path)
        if background_image is None:
            continue
            
        resolution = (background_image.shape[1], background_image.shape[0])
        heatmap = np.zeros(resolution)
        valid_detections = 0
        total_points = 0
        
        # Sort files by timestamp
        files_with_timestamps.sort(key=lambda x: x[1], reverse=True)
        
        for file_path, timestamp in files_with_timestamps:
# Update this part in create_channel_heatmaps function
            try:
                df = pd.read_csv(file_path, header=None)
                if len(df) == 0:
                    logging.warning(f"Empty file: {file_path}")
                    continue

                # Update column names to match your actual format
                df.columns = ['frame_number', 'track_id', 'x', 'y', 'width', 'height']

                # Calculate center points (keep this part the same)
                base_x = df['x'] + df['width'] / 2  
                base_y = df['y'] + df['height']

    # Rest of the code remains the same...
                
                # Calculate time-based weight
                time_diff = (cutoff_end - timestamp).total_seconds()
                time_weight = time_decay ** (time_diff / 3600)  # Decay per hour
                
                points_in_file = 0
                for x, y in zip(base_x, base_y):
                    total_points += 1
                    if 0 <= x < resolution[0] and 0 <= y < resolution[1]:
                        points_in_file += 1
                        apply_gaussian_overlay(heatmap, x, y, resolution, time_weight)
                
                if points_in_file > 0:
                    valid_detections += 1
                    logging.info(f"Processed {points_in_file}/{len(df)} points from {file_path}")
                else:
                    logging.warning(f"No valid points in {file_path}")
                        
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                continue
        
        if valid_detections > 0:
            logging.info(f"Channel {channel}: Processed {valid_detections} files with {total_points} total points")
            channel_heatmaps[channel] = (heatmap, background_image)
        else:
            logging.warning(f"No valid detections for channel {channel}")
    
    return channel_heatmaps

def plot_channel_heatmaps(channel_heatmaps, save_dir=None, alpha=0.6):
    """Plot heatmaps for each channel"""
    if not channel_heatmaps:
        logging.warning("No heatmaps to plot")
        return
        
    logging.info(f"Plotting heatmaps for {len(channel_heatmaps)} channels")
    
    for channel, (heatmap, background_image) in channel_heatmaps.items():
        logging.info(f"Plotting heatmap for channel {channel}")
        plt.close('all')
        
        fig = plt.figure(frameon=False)
        fig.set_size_inches(16, 9)
        
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        
        ax.imshow(cv2.cvtColor(background_image, cv2.COLOR_BGR2RGB),
                 aspect='auto',
                 extent=[0, heatmap.shape[1], heatmap.shape[0], 0])
        
        im = ax.imshow(heatmap,
                      cmap='hot',
                      alpha=alpha,
                      aspect='auto',
                      extent=[0, heatmap.shape[1], heatmap.shape[0], 0])
        
        cbar_ax = fig.add_axes([0.95, 0.15, 0.02, 0.7])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label(f'Detection Density - Channel {channel}', color='white')
        cbar.ax.yaxis.set_tick_params(colors='white')
        
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f'heatmap_channel_{channel}.png')
            plt.savefig(save_path,
                       bbox_inches='tight',
                       pad_inches=0,
                       dpi='figure')
            logging.info(f"Saved heatmap for channel {channel} to {save_path}")
        
        plt.show()

# Example usage
if __name__ == "__main__":
    logging.info("Starting heatmap generation script")
    
    # For specific time range
    start_time = datetime(2024, 12, 29, 7, 0)  # 29/12/24 7:00 AM
    end_time = datetime(2024, 12, 29, 8, 0)    # 29/12/24 8:00 AM

    channel_heatmaps = create_channel_heatmaps(
        hours_ago=10,
        time_decay=0.95
    )
    
    plot_channel_heatmaps(channel_heatmaps, save_dir='/home/ubuntu/Oil-Mill/app/heatmap_outputs')