#!/usr/bin/env python3
"""
Git Commit Time Analyzer
Analyzes the time of day and day of week for commits by a specific contributor.
"""

import subprocess
import sys
from datetime import datetime
from collections import defaultdict
import argparse
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_commits_for_contributor(repo_path: str, contributor: str = None, email: str = None) -> List[Tuple[datetime, str]]:
    """
    Get all commits from a specific contributor.
    
    Args:
        repo_path: Path to git repository
        contributor: Contributor name to filter by (optional)
        email: Optional email to filter by (if provided, ORs with name)
    
    Returns:
        List of tuples (commit_datetime, commit_hash)
    """
    try:
        # Build git log command
        cmd = ['git', 'log', '--all', '--pretty=format:%H|%cd', '--date=local']
        
        # If contributor is specified, add author filter
        if contributor:
            author_filter = f'--author={contributor}'
            if email:
                author_filter = f'--author={contributor}|{email}'
            cmd.append(author_filter)
        
        # Execute git command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)
        
        if result.returncode != 0:
            print(f"Error running git command: {result.stderr}")
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) == 2:
                    commit_hash, date_str = parts
                    try:
                        # Parse the date string (format depends on git version)
                        # Try multiple common formats
                        for fmt in ['%a %b %d %H:%M:%S %Y', '%Y-%m-%d %H:%M:%S']:
                            try:
                                commit_date = datetime.strptime(date_str.strip(), fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            # If none of the formats work, try a more flexible approach
                            commit_date = datetime.fromisoformat(date_str.replace(' ', 'T'))
                        
                        commits.append((commit_date, commit_hash))
                    except ValueError as e:
                        print(f"Warning: Could not parse date '{date_str}': {e}")
        
        return commits
    
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def analyze_commit_times(commits: List[Tuple[datetime, str]]) -> Dict:
    """
    Analyze commit times and return statistics.
    
    Returns:
        Dictionary with hour, weekday, and combined statistics
    """
    # Initialize counters
    hour_counts = defaultdict(int)  # 0-23
    weekday_counts = defaultdict(int)  # 0-6 (Monday=0)
    hour_weekday_counts = defaultdict(lambda: defaultdict(int))  # hour -> weekday -> count
    month_counts = defaultdict(int)  # 1-12
    
    # Day names for display
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Count commits
    for commit_date, _ in commits:
        hour = commit_date.hour
        weekday = commit_date.weekday()  # Monday=0
        month = commit_date.month
        
        hour_counts[hour] += 1
        weekday_counts[weekday] += 1
        hour_weekday_counts[hour][weekday] += 1
        month_counts[month] += 1
    
    # Calculate percentages
    total_commits = len(commits)
    
    hour_percentages = {hour: (count/total_commits*100) for hour, count in hour_counts.items()}
    weekday_percentages = {day_names[weekday]: (count/total_commits*100) 
                          for weekday, count in weekday_counts.items()}
    
    return {
        'total_commits': total_commits,
        'hour_counts': dict(hour_counts),
        'weekday_counts': dict(weekday_counts),
        'hour_weekday_counts': {h: dict(d) for h, d in hour_weekday_counts.items()},
        'month_counts': dict(month_counts),
        'hour_percentages': hour_percentages,
        'weekday_percentages': weekday_percentages,
        'day_names': day_names
    }

def print_statistics(stats: Dict, contributor: str):
    """Print commit statistics in a readable format."""
    print("\n" + "="*60)
    print(f"COMMIT ANALYSIS FOR: {contributor}")
    print("="*60)
    print(f"Total commits: {stats['total_commits']}")
    
    if stats['total_commits'] == 0:
        print("No commits found for this contributor.")
        return
    
    print("\n--- By Hour of Day ---")
    for hour in sorted(stats['hour_counts'].keys()):
        count = stats['hour_counts'][hour]
        percentage = stats['hour_percentages'][hour]
        print(f"  {hour:02d}:00 - {hour:02d}:59: {count:4d} commits ({percentage:5.1f}%)")
    
    print("\n--- By Day of Week ---")
    for weekday in sorted(stats['weekday_counts'].keys()):
        day_name = stats['day_names'][weekday]
        count = stats['weekday_counts'][weekday]
        percentage = (count / stats['total_commits']) * 100
        print(f"  {day_name:9}: {count:4d} commits ({percentage:5.1f}%)")
    
    print("\n--- By Month ---")
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month in sorted(stats['month_counts'].keys()):
        count = stats['month_counts'][month]
        percentage = (count / stats['total_commits']) * 100
        print(f"  {month_names[month-1]:3}: {count:4d} commits ({percentage:5.1f}%)")
    
    # Find busiest hour and day
    if stats['hour_counts']:
        busiest_hour = max(stats['hour_counts'].items(), key=lambda x: x[1])
        print(f"\nBusiest hour: {busiest_hour[0]:02d}:00 ({busiest_hour[1]} commits)")
    
    if stats['weekday_counts']:
        busiest_day_idx = max(stats['weekday_counts'].items(), key=lambda x: x[1])[0]
        print(f"Busiest day: {stats['day_names'][busiest_day_idx]}")

def plot_histograms(stats: Dict, contributor: str, output_file: str = None):
    """Create visualization of commit patterns."""
    if stats['total_commits'] == 0:
        print("No data to plot.")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Commit Patterns for {contributor}\nTotal commits: {stats["total_commits"]}', fontsize=16)
    
    # Plot 1: Hour of day histogram
    ax1 = axes[0, 0]
    hours = sorted(stats['hour_counts'].keys())
    hour_values = [stats['hour_counts'][h] for h in hours]
    ax1.bar(hours, hour_values, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Hour of Day (0-23)')
    ax1.set_ylabel('Number of Commits')
    ax1.set_title('Commits by Hour of Day')
    ax1.set_xticks(range(0, 24, 2))
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Day of week histogram
    ax2 = axes[0, 1]
    weekdays = sorted(stats['weekday_counts'].keys())
    day_labels = [stats['day_names'][d][:3] for d in weekdays]
    weekday_values = [stats['weekday_counts'][d] for d in weekdays]
    ax2.bar(day_labels, weekday_values, color='lightgreen', edgecolor='black')
    ax2.set_xlabel('Day of Week')
    ax2.set_ylabel('Number of Commits')
    ax2.set_title('Commits by Day of Week')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Heatmap (hour vs weekday)
    ax3 = axes[1, 0]
    heatmap_data = np.zeros((24, 7))
    for hour in range(24):
        for weekday in range(7):
            heatmap_data[hour, weekday] = stats['hour_weekday_counts'].get(hour, {}).get(weekday, 0)
    
    im = ax3.imshow(heatmap_data, aspect='auto', cmap='YlOrRd')
    ax3.set_xlabel('Day of Week')
    ax3.set_ylabel('Hour of Day')
    ax3.set_title('Commit Heatmap (Hour vs Day)')
    ax3.set_xticks(range(7))
    ax3.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax3.set_yticks(range(0, 24, 2))
    plt.colorbar(im, ax=ax3, label='Number of Commits')
    
    # Plot 4: Month histogram
    ax4 = axes[1, 1]
    months = sorted(stats['month_counts'].keys())
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_values = [stats['month_counts'].get(m, 0) for m in range(1, 13)]
    ax4.bar(month_labels, month_values, color='lightcoral', edgecolor='black')
    ax4.set_xlabel('Month')
    ax4.set_ylabel('Number of Commits')
    ax4.set_title('Commits by Month')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved to: {output_file}")
    else:
        plt.show()

def list_contributors(repo_path: str):
    """List all contributors in the repository."""
    try:
        cmd = ['git', 'log', '--all', '--format=%aN|%aE', '--date=short']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)
        
        contributors = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                if '|' in line:
                    name, email = line.split('|')
                    contributors.add((name.strip(), email.strip()))
        
        print(f"\nFound {len(contributors)} unique contributor(s):")
        print("-" * 60)
        
        # Sort by name
        for name, email in sorted(contributors, key=lambda x: x[0].lower()):
            print(f"{name:30} <{email}>")
        
        print("\nTip: Use partial names for matching (e.g., 'John' instead of 'John Doe')")
        
    except Exception as e:
        print(f"Error listing contributors: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze commit times for a specific contributor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s . --list-contributors
  %(prog)s . "John Doe"
  %(prog)s . "john" --email "john@example.com"
  %(prog)s . "John Doe" --plot
  %(prog)s . "John" --output-plot commits.png
        """
    )
    
    parser.add_argument('repository', help='Path to git repository')
    parser.add_argument('contributor', nargs='?', default=None,
                       help='Contributor name (can be partial, optional for --list-contributors)')
    parser.add_argument('--email', help='Contributor email (optional)')
    parser.add_argument('--plot', action='store_true', help='Generate visualization plot')
    parser.add_argument('--output-plot', help='Output file for plot (e.g., plot.png)')
    parser.add_argument('--list-contributors', action='store_true', 
                       help='List all contributors in the repository')
    
    args = parser.parse_args()
    
    # List contributors if requested
    if args.list_contributors:
        list_contributors(args.repository)
        return
    
    # Check if contributor is provided when not listing
    if not args.contributor:
        print("Error: Contributor name is required when not using --list-contributors")
        print("\nUse --list-contributors to see available contributors")
        print("Example: python git_commit_analyzer.py /path/to/repo --list-contributors")
        sys.exit(1)
    
    # Get commits for the specified contributor
    print(f"Analyzing commits for contributor: {args.contributor}")
    if args.email:
        print(f"With email: {args.email}")
    
    commits = get_commits_for_contributor(args.repository, args.contributor, args.email)
    
    if not commits:
        print(f"\nNo commits found for contributor: {args.contributor}")
        if args.email:
            print(f"With email: {args.email}")
        
        # Try to suggest similar names
        print("\nAvailable contributors:")
        list_contributors(args.repository)
        return
    
    # Analyze commit times
    stats = analyze_commit_times(commits)
    
    # Print statistics
    print_statistics(stats, args.contributor)
    
    # Generate plot if requested
    if args.plot or args.output_plot:
        try:
            plot_histograms(stats, args.contributor, args.output_plot)
        except ImportError:
            print("\nMatplotlib not installed. Install with: pip install matplotlib")
        except Exception as e:
            print(f"\nError generating plot: {e}")

if __name__ == '__main__':
    main()