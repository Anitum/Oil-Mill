import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
from datetime import datetime
import cv2

def create_heatmap(n_points=5, time_decay=0.9, photo_path="Photo", results_path="Results"):
    # Previous create_heatmap implementation remains the same
    background_image = None
    for img_file in os.listdir(photo_path):
        if img_file.endswith(('.jpg', '.png', '.jpeg')):
            background_image = cv2.imread(os.path.join(photo_path, img_file))
            break
            
    if background_image is None:
        raise Exception("No image found in Photo directory")
        
    resolution = (background_image.shape[1], background_image.shape[0])
    heatmap = np.zeros(resolution)
    files = glob.glob(os.path.join(results_path, "*_results.csv"))
    
    if not files:
        raise Exception("No result files found in Results directory")
    
    files.sort(reverse=True)
    
    for i, file_path in enumerate(files[:n_points]):
        try:
            df = pd.read_csv(file_path, header=None)
            if len(df.columns) != 6:
                continue
            
            df.columns = ['track_id', 'frame_id', 'x', 'y', 'width', 'height']
            base_x = df['x'] + df['width'] / 2
            base_y = df['y'] + df['height']
            time_weight = time_decay ** i
            
            for x, y in zip(base_x, base_y):
                if 0 <= x < resolution[0] and 0 <= y < resolution[1]:
                    y_idx, x_idx = np.ogrid[-20:21, -20:21]
                    gaussian = np.exp(-(x_idx*x_idx + y_idx*y_idx) / 100)
                    x_start = max(0, int(x) - 20)
                    x_end = min(resolution[0], int(x) + 21)
                    y_start = max(0, int(y) - 20)
                    y_end = min(resolution[1], int(y) + 21)
                    heatmap[y_start:y_end, x_start:x_end] += gaussian[:y_end-y_start, :x_end-x_start] * time_weight
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
            
    return heatmap, background_image

def plot_heatmap(heatmap, background_image, save_path=None, alpha=0.6):
    # Close any existing plots
    plt.close('all')
    
    # Create figure without any padding
    fig = plt.figure(frameon=False)
    fig.set_size_inches(16, 9)
    
    # Create axes that cover the entire figure
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    
    # Display background image with extent to fill the axes
    ax.imshow(cv2.cvtColor(background_image, cv2.COLOR_BGR2RGB),
              aspect='auto',
              extent=[0, heatmap.shape[1], heatmap.shape[0], 0])
    
    # Overlay heatmap with same extent
    im = ax.imshow(heatmap,
                   cmap='hot',
                   alpha=alpha,
                   aspect='auto',
                   extent=[0, heatmap.shape[1], heatmap.shape[0], 0])
    
    # Add colorbar
    cbar_ax = fig.add_axes([0.95, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label('Detection Density', color='white')
    cbar.ax.yaxis.set_tick_params(colors='white')
    
    # Maximize window
    manager = plt.get_current_fig_manager()
    try:
        manager.full_screen_toggle()  # works on qt backend
    except AttributeError:
        try:
            manager.window.showMaximized()
        except AttributeError:
            try:
                manager.frame.Maximize(True)  # works on wx backend
            except AttributeError:
                try:
                    manager.resize(*manager.window.maxsize())  # works on tk backend
                except:
                    pass
    
    if save_path:
        plt.savefig(save_path, 
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi='figure')
    
    plt.show()

# Example usage
n_points = 50  # Number of most recent results to use
time_decay = 0.9  # Decay factor (0-1), higher means slower decay

# Create and plot heatmap
heatmap, background = create_heatmap(n_points=n_points, time_decay=time_decay)
plot_heatmap(heatmap, background, save_path='heatmap_output.png')