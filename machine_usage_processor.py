import os
import glob
import json
import pandas as pd
from datetime import datetime, timedelta, date

class MachineUsageProcessor:
    def __init__(self, input_dir='input', output_file='input/machine-usage.json'):
        """
        Initialize the machine usage processor.
        
        Args:
            input_dir: Directory where camera CSV files are stored
            output_file: Path to the output JSON file
        """
        self.input_dir = input_dir
        self.output_file = output_file
        
        # Machine mapping
        self.machine_mapping = {
            '501': 'filter',
            '601': 'crusher',
            '701': 'filling'
        }
    
    def find_camera_csv_files(self, date_str=None):
        """
        Find all camera CSV files for the specified date or today if not specified.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses today's date.
            
        Returns:
            Dictionary mapping camera IDs to their CSV files
        """
        if date_str is None:
            date_str = date.today().strftime('%Y-%m-%d')
        
        # Define the patterns for finding camera files
        patterns = [
            f"{self.input_dir}/camera501_{date_str}.csv",
            f"{self.input_dir}/camera601_{date_str}.csv",
            f"{self.input_dir}/camera701_{date_str}.csv"
        ]
        
        # Find all matching files
        camera_files = {}
        for pattern in patterns:
            matching_files = glob.glob(pattern)
            for file_path in matching_files:
                # Extract camera ID from filename
                camera_id = os.path.basename(file_path).split('_')[0][6:]
                camera_files[camera_id] = file_path
        
        return camera_files
    
    def process_camera_file(self, camera_id, file_path):
        """
        Process a single camera CSV file to extract motion detection events.
        Each True value represents 90 seconds (1.5 minutes) of machine usage.
        
        Args:
            camera_id: Camera ID (e.g., '501', '601', '701')
            file_path: Path to the CSV file
            
        Returns:
            Dictionary with hourly counts of motion detections
        """
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Check if the file is empty
            if df.empty:
                print(f"Empty file: {file_path}")
                return {}
            
            # Expected format: channel601_20250222T001201,channel6,False,True,2025-02-22 01:01:03
            # Rename columns for clarity
            if len(df.columns) >= 5:
                df.columns = ['file_name', 'channel', 'motion_status1', 'motion_status2', 'timestamp'] + list(df.columns[5:])
            else:
                # Handle different column counts
                print(f"Warning: Unexpected column count in {file_path}: {len(df.columns)}")
                if len(df.columns) == 1:
                    # Try to parse comma-separated data in a single column
                    df = pd.DataFrame([row.split(',') for row in df.iloc[:, 0]], 
                                    columns=['file_name', 'channel', 'motion_status1', 'motion_status2', 'timestamp'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Filter out rows with invalid timestamps
            df = df.dropna(subset=['timestamp'])
            
            # Convert motion_status2 to boolean (True/False)
            df['motion_status2'] = df['motion_status2'].astype(str).str.lower() == 'true'
            
            # Group by hour and count True values
            df['hour'] = df['timestamp'].dt.floor('H')
            hourly_counts = df[df['motion_status2']].groupby('hour').size()
            
            # Convert counts to minutes of activity (90 seconds = 1.5 minutes per True value)
            hourly_minutes = {}
            for hour, count in hourly_counts.items():
                # Convert count to minutes (each True = 1.5 minutes, max 60 minutes per hour)
                minutes = min(count * 1.5, 60)  # 90 seconds = 1.5 minutes
                hourly_minutes[hour.strftime('%Y-%m-%dT%H:%M:%S')] = minutes
            
            return hourly_minutes
        
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
        return {}
    
    def load_existing_data(self):
        """
        Load existing machine usage data from the output file.
        
        Returns:
            Dictionary containing the existing data or a newly initialized structure
        """
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize new data structure
                return {
                    "last_updated": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    "interval": "hourly",
                    "data": []
                }
        except Exception as e:
            print(f"Error loading existing data: {str(e)}")
            # Return a new empty structure
            return {
                "last_updated": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "interval": "hourly",
                "data": []
            }
    
    def update_machine_data(self, existing_data, new_hourly_data):
        """
        Update existing machine data with new hourly data.
        
        Args:
            existing_data: Existing machine usage data
            new_hourly_data: Dictionary mapping machine types to hourly usage minutes
            
        Returns:
            Updated data structure
        """
        # Update last_updated timestamp
        existing_data["last_updated"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        # Get all timestamps from existing and new data
        existing_timestamps = {item["timestamp"] for item in existing_data["data"]}
        all_new_timestamps = set()
        for machine_type, hourly_data in new_hourly_data.items():
            all_new_timestamps.update(hourly_data.keys())
        
        # Add new timestamps to existing data
        for timestamp in all_new_timestamps:
            if timestamp not in existing_timestamps:
                existing_data["data"].append({
                    "timestamp": timestamp,
                    "total_count": 0,
                    "by_area": {
                        "filter": 0,
                        "crusher": 0,
                        "filling": 0
                    }
                })
        
        # Sort data by timestamp
        existing_data["data"].sort(key=lambda x: x["timestamp"])
        
        # Update existing data with new values
        for data_point in existing_data["data"]:
            timestamp = data_point["timestamp"]
            by_area = data_point["by_area"]
            
            for machine_type, hourly_data in new_hourly_data.items():
                if timestamp in hourly_data:
                    by_area[machine_type] = round(hourly_data[timestamp], 1)  # Round to 1 decimal place
            
            # Update total count
            data_point["total_count"] = round(sum(by_area.values()), 1)
        
        return existing_data
    
    def process_and_save(self, date_str=None):
        """
        Process all camera files for the specified date and update the machine usage JSON.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses today's date.
        """
        try:
            # Find all camera files
            camera_files = self.find_camera_csv_files(date_str)
            if not camera_files:
                print(f"No camera files found for date: {date_str or 'today'}")
                return
            
            print(f"Found {len(camera_files)} camera files: {list(camera_files.keys())}")
            
            # Process each camera file
            new_hourly_data = {}
            for camera_id, file_path in camera_files.items():
                if camera_id in self.machine_mapping:
                    machine_type = self.machine_mapping[camera_id]
                    hourly_minutes = self.process_camera_file(camera_id, file_path)
                    new_hourly_data[machine_type] = hourly_minutes
                    print(f"Processed {camera_id} ({machine_type}): {len(hourly_minutes)} hours of data")
            
            # Load existing data
            existing_data = self.load_existing_data()
            
            # Update with new data
            updated_data = self.update_machine_data(existing_data, new_hourly_data)
            
            # Save updated data
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            with open(self.output_file, 'w') as f:
                json.dump(updated_data, f, indent=2)
            
            print(f"Updated machine usage data saved to {self.output_file}")
            
        except Exception as e:
            print(f"Error in process_and_save: {str(e)}")
            import traceback
            print(traceback.format_exc())

# For direct execution
if __name__ == "__main__":
    processor = MachineUsageProcessor()
    processor.process_and_save()