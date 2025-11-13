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
    """Process all relevant files and count activities by resource_id - Memory optimized"""

    # Convert target dates to timezone-aware UTC datetime objects
    target_start = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    target_end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)

    print(f"Target date range (UTC): {target_start} to {target_end}")

    # We'll use a dictionary to count activities to avoid storing all data in memory
    activity_counts = {}
    total_rows_processed = 0
    total_matching_rows = 0

    # Only read the columns we actually need
    usecols = ['timestamp', 'name', 'last_resource_id']

    for file_path in file_list:
        try:
            print(f"Processing file: {os.path.basename(file_path)}")
            file_size = os.path.getsize(file_path) / (1024**3)  # Size in GB
            print(f"  File size: {file_size:.2f} GB")

            # Get sample to understand data
            print("  Sampling data structure...")
            try:
                sample_df = pd.read_csv(file_path, nrows=5, usecols=usecols)
                print(f"  Sample 'name' values: {sample_df['name'].unique()}")
                print(f"  Sample timestamps: {sample_df['timestamp'].head(2).tolist()}")
            except Exception as e:
                print(f"  Could not sample file: {e}")

            # Process file in chunks
            chunk_size = 50000  # Smaller chunks for large files
            chunk_counter = 0

            for chunk in pd.read_csv(file_path, chunksize=chunk_size, usecols=usecols):
                chunk_counter += 1
                total_rows_processed += len(chunk)

                if chunk_counter % 20 == 0:  # Print progress every 20 chunks
                    print(f"  Processed {chunk_counter} chunks ({total_rows_processed:,} total rows)...")

                # Convert timestamp efficiently
                chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], format='mixed', utc=True)

                # Filter by name and date range
                mask = (chunk['name'] == activity_name) & \
                       (chunk['timestamp'] >= target_start) & \
                       (chunk['timestamp'] <= target_end)

                filtered_chunk = chunk[mask]

                if not filtered_chunk.empty:
                    total_matching_rows += len(filtered_chunk)

                    # Count activities by last_resource_id
                    for resource_id in filtered_chunk['last_resource_id']:
                        if pd.notna(resource_id):  # Skip NaN values
                            activity_counts[resource_id] = activity_counts.get(resource_id, 0) + 1

                # Force garbage collection every few chunks
                if chunk_counter % 50 == 0:
                    import gc
                    gc.collect()

            print(f"  Finished file: processed {chunk_counter} chunks, {total_rows_processed:,} total rows")
  
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nTotal processing summary:")
    print(f"  Rows processed: {total_rows_processed:,}")
    print(f"  Matching rows found: {total_matching_rows:,}")
    print(f"  Unique resources with activities: {len(activity_counts):,}")

    # Convert counts dictionary to DataFrame
    if activity_counts:
        results_df = pd.DataFrame(list(activity_counts.items()), columns=['last_resource_id', 'count'])
        return results_df.sort_values('count', ascending=False)
    else:
        return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description='Count activities by resource from CSV files - Memory optimized')
    parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('end_date', help='End date (YYYY-MM-DD)')
    parser.add_argument('activity_name', help='Name of activity to count')
    parser.add_argument('--directory', default='.', help='Directory containing CSV files (default: current directory)')
    parser.add_argument('--output', default='activity_counts.csv', help='Output CSV filename (default: activity_counts.csv)')
    parser.add_argument('--chunk-size', type=int, default=50000, help='Chunk size for processing (default: 50000)')

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
    print(f"Chunk size: {args.chunk_size}")
    print()

    # Get relevant files
    relevant_files = get_relevant_files(args.directory, args.start_date, args.end_date)

    if not relevant_files:
        print("No relevant CSV files found for the specified date range.")
        sys.exit(1)

    print(f"\nFound {len(relevant_files)} relevant file(s) to process")

    # Process files
    print("Processing files... (this may take a while for large files)")
    results = process_files(relevant_files, args.start_date, args.end_date, args.activity_name)

    if results.empty:
        print("No matching activities found.")
        sys.exit(0)

    # Save results to CSV
    results.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")

    # Print summary to console
    print(f"\nSummary: {args.activity_name} activities by resource")
    print("=" * 60)
    top_results = results.head(20)  # Show top 20 to avoid console spam
    for _, row in top_results.iterrows():
        print(f"{row['last_resource_id']} {args.activity_name} {row['count']} times")

    if len(results) > 20:
        print(f"... and {len(results) - 20} more resources")

    print(f"\nTotal unique resources: {len(results):,}")
    print(f"Total activities: {results['count'].sum():,}")


if __name__ == "__main__":
    main()
