import pandas as pd
import numpy as np
import os
from pathlib import Path
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_cctv.log'),
        logging.StreamHandler()
    ]
)

def process_cctv_directory(directory_path):
    """
    Process CSV files and detect areas of interest
    Saves filenames to separate CSVs for each area
    """
    directory = Path(directory_path)
    input_dir = Path('input')
    
    # Create input directory if it doesn't exist
    if not input_dir.exists():
        logging.info(f"Creating input directory: {input_dir}")
        input_dir.mkdir(parents=True, exist_ok=True)
    
    if not directory.exists():
        raise ValueError(f"Directory not found: {directory}")
    
    logging.info(f"Starting processing of directory: {directory}")
    
    # Area definitions
    areas_df = pd.DataFrame({
        'channel': [701, 301, 601,601,601],
        'name': ['Oil_can_Filling', 'Pouring_raw_Material', 'Mill1-2','Mill2-3','Mill3-4'],
        'x1': [800,1750,580,350,160],
        'y1': [350,450,115,150,180],
        'x2': [1350,1980,680,500,300],
        'y2': [800,870,305,360,380]
    })

    # Dictionary to store results for each area
    area_results = {area: [] for area in areas_df['name']}
    file_counts = []
    n = 90
    
    csv_files = list(directory.glob('*.csv'))
    logging.info(f"Found {len(csv_files)} CSV files to process")
    
    processed_count = 0
    error_count = 0
    empty_count = 0
    
    for csv_path in csv_files:
        try:
            logging.debug(f"Processing file: {csv_path}")
            
            # Skip empty files
            if csv_path.stat().st_size == 0:
                logging.warning(f"Empty file found and will be deleted: {csv_path}")
                os.remove(str(csv_path))
                empty_count += 1
                continue
                
            # Read CSV file
            df = pd.read_csv(csv_path, header=None)
            
            if len(df) == 0:
                logging.warning(f"File with no data found and will be deleted: {csv_path}")
                os.remove(str(csv_path))
                empty_count += 1
                continue
            
            # Process file counts
            file_counts.append({
                'file_name': csv_path.name,
                'count': len(df) / n
            })
            
            # Calculate center points
            df['center_x'] = df[2] + (df[4] / 2)
            df['center_y'] = df[3] + (df[5] / 2)
            
            # Get channel number
            channel = int(csv_path.stem.split('_')[0].replace('channel', ''))
            logging.debug(f"Processing channel: {channel}")
            
            # Check each applicable area
            for _, area in areas_df[areas_df['channel'] == channel].iterrows():
                points_in_area = (
                    (df['center_x'] >= area['x1']) &
                    (df['center_x'] <= area['x2']) &
                    (df['center_y'] >= area['y1']) &
                    (df['center_y'] <= area['y2'])
                )
                
                if points_in_area.any():
                    area_results[area['name']].append(csv_path.name)
                    logging.debug(f"Activity detected in {area['name']}: {csv_path.name}")
            
            # Delete processed file
            os.remove(str(csv_path))
            processed_count += 1
            
            # Log progress every 100 files
            if processed_count % 100 == 0:
                logging.info(f"Processed {processed_count} files...")
            
        except Exception as e:
            logging.error(f"Error processing {csv_path}: {str(e)}")
            error_count += 1
            continue

    # Save results for each area (even if empty)
    for area_name in areas_df['name']:
        output_file = input_dir / f'{area_name}.csv'
        try:
            filenames = area_results.get(area_name, [])
            pd.DataFrame(filenames, columns=['Filename']).to_csv(
                output_file, index=False
            )
            logging.info(f"Saved {len(filenames)} detections to {output_file}")
        except Exception as e:
            logging.error(f"Error saving results for {area_name}: {str(e)}")

    # Save file counts
    if file_counts:
        try:
            counts_file = input_dir / 'file_counts.csv'
            pd.DataFrame(file_counts, columns=['file_name', 'count']).to_csv(
                counts_file, index=False
            )
            logging.info(f"Saved {len(file_counts)} entries to file_counts.csv")
        except Exception as e:
            logging.error(f"Error saving file counts: {str(e)}")

    # Log summary
    logging.info(f"""
    Processing Complete:
    - Total files processed: {processed_count}
    - Empty files removed: {empty_count}
    - Errors encountered: {error_count}
    - Results saved to: {input_dir}
    """)

    return area_results

if __name__ == "__main__":
    try:
        directory = r"/home/mridul/Oil-Mill/testing/s3_results/s3_results"
        logging.info(f"Starting script with directory: {directory}")
        
        results = process_cctv_directory(directory)
        
        logging.info("\nResults summary:")
        for area, filenames in results.items():
            logging.info(f"{area}: {len(filenames)} detections")
            
    except Exception as e:
        logging.error(f"Fatal error occurred: {str(e)}")