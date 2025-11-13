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


def estimate_total_chunks(file_path, chunk_size):
    """Estimate total number of chunks in a file using line count"""
    try:
        # Count lines in file (faster and more accurate than parsing CSV)
        with open(file_path, 'rb') as f:
            line_count = 0
            chunk = f.read(8192)
            while chunk:
                line_count += chunk.count(b'\n')
                chunk = f.read(8192)

        # Subtract 1 for header row, then divide by chunk_size
        estimated_chunks = max(1, (line_count - 1) // chunk_size + 1)
        return estimated_chunks
    except Exception as e:
        print(f"Error estimating chunks for file {file_path}: {e}")
        return None


def process_files(file_list, start_date, end_date, activity_name, chunk_size=50000):
    """Process all relevant files and count activities by resource_id - Memory optimized"""

    # Convert target dates to timezone-aware UTC datetime objects
    target_start = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    target_end = (
        datetime.strptime(end_date, '%Y-%m-%d')
        .replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
    )

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
            file_size_gb = os.path.getsize(file_path) / (1024**3)  # Size in GB
            print(f"  File size: {file_size_gb:.2f} GB")

            # Estimate total chunks for progress tracking
            total_chunks_estimate = estimate_total_chunks(file_path, chunk_size)
            if total_chunks_estimate:
                print(f"  Estimated total chunks: {total_chunks_estimate}")

            # Process file in chunks
            chunk_counter = 0
            file_rows_processed = 0
            file_matching_rows = 0

            for chunk in pd.read_csv(file_path, chunksize=chunk_size, usecols=usecols):
                chunk_counter += 1
                chunk_rows = len(chunk)
                file_rows_processed += chunk_rows
                total_rows_processed += chunk_rows

                if total_chunks_estimate:
                    percentage = min(100, int((chunk_counter / total_chunks_estimate) * 100))
                    progress_msg = (
                        f"  Processing chunk {chunk_counter} "
                        f"(out of ~{total_chunks_estimate} chunks, {percentage}%) "
                        f"with {chunk_rows} rows..."
                    )
                else:
                    progress_msg = f"  Processing chunk {chunk_counter} with {chunk_rows} rows..."

                if (
                    chunk_counter <= 5
                    or chunk_counter % 20 == 0
                    or (total_chunks_estimate and chunk_counter >= total_chunks_estimate - 5)
                    or chunk_counter == 1
                ):
                    print(progress_msg)
                elif chunk_counter % 10 == 0 and total_chunks_estimate and chunk_counter <= total_chunks_estimate:
                    print(f"  ... chunk {chunk_counter}/{total_chunks_estimate} ({percentage}%)")

                chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], format='mixed', utc=True)

                # Filter by name and date range
                mask = (chunk['name'] == activity_name) & \
                       (chunk['timestamp'] >= target_start) & \
                       (chunk['timestamp'] <= target_end)

                filtered_chunk = chunk[mask]

                if not filtered_chunk.empty:
                    file_matching_rows += len(filtered_chunk)
                    total_matching_rows += len(filtered_chunk)

                    # Count activities by last_resource_id
                    for resource_id in filtered_chunk['last_resource_id']:
                        if pd.notna(resource_id):  # Skip NaN values
                            activity_counts[resource_id] = activity_counts.get(resource_id, 0) + 1

                # Force garbage collection every 20 chunks
                if chunk_counter % 20 == 0:
                    import gc
                    gc.collect()

            print(f"  Finished file: processed {chunk_counter} chunks, {file_rows_processed:,} total rows")
            print(f"  Matching rows in this file: {file_matching_rows:,}")

            # If our estimate was way off, show the actual vs estimated
            if total_chunks_estimate and abs(chunk_counter - total_chunks_estimate) > 10:
                print(f"  Note: Actual chunks ({chunk_counter}) differed from estimate ({total_chunks_estimate})")

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            import traceback
            traceback.print_exc()

    print("\nTotal processing summary:")
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
    parser.add_argument(
        'activity_name',
        nargs='?',
        default='download',
        help='Name of activity to count (default: download)'
    )
    parser.add_argument('--directory', default='.', help='Directory containing CSV files (default: current directory)')
    parser.add_argument(
        '--output', default='activity_counts.csv',
        help='Output CSV filename (default: activity_counts.csv)'
    )
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
    results = process_files(relevant_files, args.start_date, args.end_date, args.activity_name, args.chunk_size)

    if results.empty:
        print("No matching activities found.")
        sys.exit(0)

    # Save results to CSV
    results.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")

    print(f"\nSummary: {args.activity_name} activities by resource")
    print("=" * 60)
    top_results = results.head(20)  # Show top 20 results
    for _, row in top_results.iterrows():
        print(f"{row['last_resource_id']} {args.activity_name} {row['count']} times")

    if len(results) > 20:
        print(f"... and {len(results) - 20} more resources")

    print(f"\nTotal unique resources: {len(results):,}")
    print(f"Total activities: {results['count'].sum():,}")


if __name__ == "__main__":
    main()
