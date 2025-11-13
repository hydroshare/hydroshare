import pandas as pd
import glob
import os
import sys
from datetime import datetime
import argparse
import re
from datetime import timezone

def parse_date_from_filename(filename):
    """Extract start and end dates from filename using regex"""
    try:
        # Look for the pattern _YYYY-MM-DD_YYYY-MM-DD.csv at the end of filename
        pattern = r'_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$'
        match = re.search(pattern, filename)
        
        if match:
            start_str = match.group(1)
            end_str = match.group(2)
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            return start_date, end_date
    except (ValueError, IndexError, AttributeError):
        pass
    return None, None

def get_relevant_files(directory, start_date, end_date):
    """Get all CSV files that overlap with the given date range"""
    relevant_files = []
    
    # Convert string dates to datetime objects
    target_start = datetime.strptime(start_date, '%Y-%m-%d').date()
    target_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    
    print(f"Found {len(csv_files)} CSV file(s) in directory:")
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        file_start, file_end = parse_date_from_filename(filename)
        
        if file_start and file_end:
            print(f"  {filename} -> Date range: {file_start} to {file_end}")
            # Check if date ranges overlap
            if not (file_end < target_start or file_start > target_end):
                relevant_files.append(file_path)
                print(f"    -> OVERLAPS with target range: {target_start} to {target_end}")
            else:
                print(f"    -> NO OVERLAP with target range: {target_start} to {target_end}")
        else:
            print(f"  {filename} -> Could not parse date range")
    
    return relevant_files

def process_files(file_list, start_date, end_date, activity_name):
    """Process all relevant files and count activities by resource_id"""
    all_data = []
    
    # Convert target dates to timezone-aware UTC datetime objects
    target_start = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    target_end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
    
    print(f"Target date range (UTC): {target_start} to {target_end}")
    
    for file_path in file_list:
        try:
            print(f"Reading file: {os.path.basename(file_path)}")
            
            # First, let's examine the first few rows to understand the data
            print("  Sampling first few rows to understand data structure...")
            sample_df = pd.read_csv(file_path, nrows=5)
            print(f"  Columns: {list(sample_df.columns)}")
            print(f"  Sample 'name' values: {sample_df['name'].unique() if 'name' in sample_df.columns else 'name column not found'}")
            if 'timestamp' in sample_df.columns:
                print(f"  Sample timestamps: {sample_df['timestamp'].head(3).tolist()}")
            
            # Read in chunks to handle large files
            chunk_size = 100000
            chunk_list = []
            total_rows_processed = 0
            total_matching_rows = 0
            
            for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
                total_rows_processed += len(chunk)
                print(f"  Processing chunk {i+1} with {len(chunk)} rows...")
                
                # Use pandas to_datetime with format='mixed' to handle both formats
                chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], format='mixed', utc=True)
                
                # Debug: Check what names and dates we have in this chunk
                unique_names = chunk['name'].unique()
                min_timestamp = chunk['timestamp'].min()
                max_timestamp = chunk['timestamp'].max()
                
                print(f"    Timestamp range in chunk: {min_timestamp} to {max_timestamp}")
                print(f"    Unique 'name' values in chunk: {unique_names}")
                
                # Filter by name and date range
                name_mask = (chunk['name'] == activity_name)
                date_mask = (chunk['timestamp'] >= target_start) & (chunk['timestamp'] <= target_end)
                
                print(f"    Rows with name '{activity_name}': {name_mask.sum()}")
                print(f"    Rows in date range: {date_mask.sum()}")
                
                mask = name_mask & date_mask
                filtered_chunk = chunk[mask]
                
                if not filtered_chunk.empty:
                    chunk_list.append(filtered_chunk)
                    total_matching_rows += len(filtered_chunk)
                    print(f"    Found {len(filtered_chunk)} matching rows in this chunk")
                else:
                    print(f"    No matching rows in this chunk")
                
            print(f"  Total rows processed: {total_rows_processed}")
            print(f"  Total matching rows found: {total_matching_rows}")
                
            if chunk_list:
                filtered_df = pd.concat(chunk_list, ignore_index=True)
                print(f"  Total filtered rows from this file: {len(filtered_df)}")
                all_data.append(filtered_df)
            else:
                print(f"  No matching rows found in this file")
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            import traceback
            traceback.print_exc()
    
    if not all_data:
        return pd.DataFrame()
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Total combined rows after filtering: {len(combined_df)}")
    
    # Count activities by last_resource_id
    activity_counts = combined_df['last_resource_id'].value_counts().reset_index()
    activity_counts.columns = ['last_resource_id', 'count']
    
    return activity_counts

def main():
    parser = argparse.ArgumentParser(description='Count activities by resource from CSV files')
    parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('end_date', help='End date (YYYY-MM-DD)')
    parser.add_argument('activity_name', help='Name of activity to count')
    parser.add_argument('--directory', default='.', help='Directory containing CSV files (default: current directory)')
    parser.add_argument('--output', default='activity_counts.csv', help='Output CSV filename (default: activity_counts.csv)')
    
    args = parser.parse_args()
    
    # Validate dates
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    print(f"Searching for files in: {args.directory}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Activity name: {args.activity_name}")
    print()
    
    # Get relevant files
    relevant_files = get_relevant_files(args.directory, args.start_date, args.end_date)
    
    if not relevant_files:
        print("No relevant CSV files found for the specified date range.")
        sys.exit(1)
    
    print(f"\nFound {len(relevant_files)} relevant file(s) to process")
    
    # Process files
    print("Processing files...")
    results = process_files(relevant_files, args.start_date, args.end_date, args.activity_name)
    
    if results.empty:
        print("No matching activities found.")
        sys.exit(0)
    
    # Save results to CSV
    results.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")
    
    # Print summary to console
    print(f"\nSummary: {args.activity_name} activities by resource")
    print("=" * 50)
    for _, row in results.iterrows():
        print(f"{row['last_resource_id']} {args.activity_name} {row['count']} times")
    
    print(f"\nTotal unique resources: {len(results)}")
    print(f"Total activities: {results['count'].sum()}")

if __name__ == "__main__":
    main()