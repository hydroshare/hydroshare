#!/usr/bin/env python3
"""
Git Commit Time Analyzer
Analyzes the time of day and day of week for commits by specific contributors or all contributors.
Handles multiple usernames/emails for the same person.
"""

import subprocess
import sys
import re
from datetime import datetime
from collections import defaultdict
import argparse
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional, Set, Union

def normalize_author_name(name: str) -> str:
    """
    Normalize author names for better matching.
    Converts to lowercase, removes extra spaces, and applies common patterns.
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip
    normalized = name.lower().strip()
    
    # Remove common prefixes/suffixes
    normalized = re.sub(r'^\s*[a-z]\.\s*', '', normalized)  # Remove "J. " prefix
    normalized = re.sub(r'\s+', ' ', normalized)  # Collapse multiple spaces
    
    return normalized

def extract_username_from_email(email: str) -> str:
    """Extract username from email address."""
    if '@' in email:
        return email.split('@')[0].lower()
    return email.lower()

def is_same_person(name1: str, email1: str, name2: str, email2: str) -> bool:
    """
    Heuristic to determine if two author entries likely refer to the same person.
    Returns True if they appear to be the same person.
    """
    # Check email similarity
    if email1 and email2:
        email1_lower = email1.lower()
        email2_lower = email2.lower()
        
        # Same email
        if email1_lower == email2_lower:
            return True
        
        # Check if emails have same local part
        if '@' in email1_lower and '@' in email2_lower:
            user1 = email1_lower.split('@')[0]
            user2 = email2_lower.split('@')[0]
            
            # Common patterns for same person with different emails
            if user1 == user2:
                return True
            
            # Check for common email variations
            if user1.startswith(user2) or user2.startswith(user1):
                return True
            
            # Check for no-reply GitHub emails vs personal emails
            if 'noreply' in email1_lower or 'noreply' in email2_lower:
                # Extract GitHub username from noreply email
                github_match1 = re.search(r'(\d+\+)?([^\+]+)@users\.noreply\.github\.com', email1_lower)
                github_match2 = re.search(r'(\d+\+)?([^\+]+)@users\.noreply\.github\.com', email2_lower)
                
                if github_match1 and github_match2:
                    github_user1 = github_match1.group(2)
                    github_user2 = github_match2.group(2)
                    if github_user1 == github_user2:
                        return True
    
    # Check name similarity
    if name1 and name2:
        name1_norm = normalize_author_name(name1)
        name2_norm = normalize_author_name(name2)
        
        # Same normalized name
        if name1_norm == name2_norm:
            return True
        
        # Check if one name contains the other
        if name1_norm in name2_norm or name2_norm in name1_norm:
            return True
        
        # Check initials
        words1 = name1_norm.split()
        words2 = name2_norm.split()
        
        if len(words1) > 0 and len(words2) > 0:
            # Check if first names match
            if words1[0] == words2[0]:
                return True
            
            # Check if last names match
            if len(words1) > 1 and len(words2) > 1 and words1[-1] == words2[-1]:
                return True
    
    return False

def group_contributors(author_entries: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, str]]]:
    """
    Group author entries that likely refer to the same person.
    
    Args:
        author_entries: List of (name, email) tuples
    
    Returns:
        Dictionary mapping primary name to list of (name, email) tuples for that person
    """
    if not author_entries:
        return {}
    
    # First pass: group by exact match
    exact_groups = defaultdict(list)
    for name, email in author_entries:
        key = f"{normalize_author_name(name)}|{email.lower()}" if email else normalize_author_name(name)
        exact_groups[key].append((name, email))
    
    # Convert to list of unique entries
    unique_entries = []
    for entries in exact_groups.values():
        # Take the most complete name from each exact group
        primary_name = max(entries, key=lambda x: len(x[0]))[0]
        # Collect all unique emails
        emails = {email for _, email in entries if email}
        unique_entries.append((primary_name, emails))
    
    # Second pass: merge similar entries
    merged = []
    used_indices = set()
    
    for i, (name1, emails1) in enumerate(unique_entries):
        if i in used_indices:
            continue
        
        current_name = name1
        current_emails = set(emails1)
        
        for j, (name2, emails2) in enumerate(unique_entries[i+1:], i+1):
            if j in used_indices:
                continue
            
            # Check if these entries might be the same person
            is_same = False
            
            # Check email similarity
            for email1 in current_emails:
                for email2 in emails2:
                    if is_same_person(current_name, email1, name2, email2):
                        is_same = True
                        break
                if is_same:
                    break
            
            # Check name similarity if no email match found
            if not is_same and current_name and name2:
                if is_same_person(current_name, "", name2, ""):
                    is_same = True
            
            if is_same:
                used_indices.add(j)
                # Merge names (use the longer/more complete one)
                if len(name2) > len(current_name):
                    current_name = name2
                # Merge emails
                current_emails.update(emails2)
        
        merged.append((current_name, current_emails))
        used_indices.add(i)
    
    # Convert to final grouped format
    grouped = {}
    for name, emails in merged:
        entries = [(name, email) for email in emails] if emails else [(name, "")]
        grouped[name] = entries
    
    return grouped

def get_all_commits(repo_path: str, contributors: List[str] = None, emails: List[str] = None) -> List[Tuple[datetime, str, str, str]]:
    """
    Get all commits from all branches and remotes.
    
    Args:
        repo_path: Path to git repository
        contributors: List of contributor names to filter by (optional)
        emails: List of emails to filter by (optional)
    
    Returns:
        List of tuples (commit_datetime, commit_hash, author_name, author_email)
    """
    try:
        # Build git log command to get ALL commits from ALL refs
        cmd = ['git', 'log', '--all', '--pretty=format:%H|%cd|%aN|%aE', '--date=local']
        
        # If contributors are specified, build author filter
        if contributors:
            author_filters = []
            for contributor in contributors:
                author_filters.append(f'--author={contributor}')
            
            # Add email filters if provided
            if emails:
                for email in emails:
                    author_filters.append(f'--author={email}')
            
            # Use multiple --author flags (git supports this)
            cmd.extend(author_filters)
        
        # Execute git command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)
        
        if result.returncode != 0:
            print(f"Error running git command: {result.stderr}")
            return []
        
        commits = []
        seen_hashes = set()  # To avoid duplicate commits
        
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 4:
                    commit_hash, date_str, author_name, author_email = parts[0], parts[1], parts[2], parts[3]
                    
                    # Skip duplicates
                    if commit_hash in seen_hashes:
                        continue
                    seen_hashes.add(commit_hash)
                    
                    try:
                        # Parse the date string
                        for fmt in ['%a %b %d %H:%M:%S %Y', '%Y-%m-%d %H:%M:%S']:
                            try:
                                commit_date = datetime.strptime(date_str.strip(), fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            # If none of the formats work, try a more flexible approach
                            commit_date = datetime.fromisoformat(date_str.replace(' ', 'T'))
                        
                        commits.append((commit_date, commit_hash, author_name, author_email))
                    except ValueError as e:
                        print(f"Warning: Could not parse date '{date_str}': {e}")
        
        return commits
    
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_commits_for_multiple_contributors(repo_path: str, contributor_names: List[str]) -> List[Tuple[datetime, str, str, str]]:
    """
    Get commits for multiple contributors, handling different names/emails for the same person.
    
    Args:
        repo_path: Path to git repository
        contributor_names: List of contributor names to include
    
    Returns:
        List of commits from all specified contributors
    """
    # First, get all unique authors in the repo
    all_commits = get_all_commits(repo_path)
    all_authors = set((name, email) for _, _, name, email in all_commits)
    
    # Group authors that are likely the same person
    grouped_authors = group_contributors(list(all_authors))
    
    # Find which groups match our contributor names
    matched_entries = set()
    for name in contributor_names:
        name_lower = normalize_author_name(name)
        for primary_name, entries in grouped_authors.items():
            primary_lower = normalize_author_name(primary_name)
            
            # Check if this group matches our contributor name
            if (name_lower in primary_lower or 
                primary_lower in name_lower or
                any(name_lower in normalize_author_name(e[0]) for e in entries) or
                any(normalize_author_name(e[0]) in name_lower for e in entries)):
                
                matched_entries.update(entries)
    
    # If no matches found with grouping, try direct matching
    if not matched_entries:
        for name in contributor_names:
            name_lower = normalize_author_name(name)
            for author_name, author_email in all_authors:
                if name_lower in normalize_author_name(author_name):
                    matched_entries.add((author_name, author_email))
    
    # Collect all names and emails from matched entries
    contributor_names_list = []
    contributor_emails_list = []
    
    for name, email in matched_entries:
        if name:
            contributor_names_list.append(name)
        if email:
            contributor_emails_list.append(email)
    
    # Get commits for all matched names/emails
    return get_all_commits(repo_path, contributor_names_list, contributor_emails_list)

def analyze_commit_times(commits: List[Tuple[datetime, str, str, str]]) -> Dict:
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
    year_counts = defaultdict(int)
    author_counts = defaultdict(int)
    email_counts = defaultdict(int)
    
    # Day names for display
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Count commits
    for commit_date, _, author_name, author_email in commits:
        hour = commit_date.hour
        weekday = commit_date.weekday()  # Monday=0
        month = commit_date.month
        year = commit_date.year
        
        hour_counts[hour] += 1
        weekday_counts[weekday] += 1
        hour_weekday_counts[hour][weekday] += 1
        month_counts[month] += 1
        year_counts[year] += 1
        author_counts[author_name] += 1
        if author_email:
            email_counts[author_email] += 1
    
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
        'year_counts': dict(year_counts),
        'author_counts': dict(author_counts),
        'email_counts': dict(email_counts),
        'hour_percentages': hour_percentages,
        'weekday_percentages': weekday_percentages,
        'day_names': day_names
    }

def print_statistics(stats: Dict, contributors: Union[str, List[str]] = "All Contributors"):
    """Print commit statistics in a readable format."""
    if isinstance(contributors, list):
        contributor_str = ", ".join(contributors)
    else:
        contributor_str = contributors
    
    print("\n" + "="*80)
    print(f"COMMIT ANALYSIS FOR: {contributor_str}")
    print("="*80)
    print(f"Total commits: {stats['total_commits']}")
    
    if stats['total_commits'] == 0:
        print("No commits found.")
        return
    
    # Show contributor breakdown
    if stats['author_counts']:
        print(f"\n--- Contributor Breakdown ({len(stats['author_counts'])} unique names) ---")
        sorted_authors = sorted(stats['author_counts'].items(), key=lambda x: x[1], reverse=True)
        for i, (author, count) in enumerate(sorted_authors, 1):
            percentage = (count / stats['total_commits']) * 100
            print(f"  {i:2d}. {author[:40]:40} {count:6d} commits ({percentage:5.1f}%)")
    
    # Show email breakdown if we have multiple emails
    if len(stats['email_counts']) > 1:
        print(f"\n--- Email Breakdown ({len(stats['email_counts'])} unique emails) ---")
        sorted_emails = sorted(stats['email_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (email, count) in enumerate(sorted_emails, 1):
            percentage = (count / stats['total_commits']) * 100
            print(f"  {i:2d}. {email[:40]:40} {count:6d} commits ({percentage:5.1f}%)")
    
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
    
    # Show year distribution if we have multiple years
    if len(stats['year_counts']) > 1:
        print("\n--- By Year ---")
        for year in sorted(stats['year_counts'].keys()):
            count = stats['year_counts'][year]
            percentage = (count / stats['total_commits']) * 100
            print(f"  {year}: {count:4d} commits ({percentage:5.1f}%)")
    
    # Find busiest hour and day
    if stats['hour_counts']:
        busiest_hour = max(stats['hour_counts'].items(), key=lambda x: x[1])
        print(f"\nBusiest hour: {busiest_hour[0]:02d}:00 ({busiest_hour[1]} commits)")
    
    if stats['weekday_counts']:
        busiest_day_idx = max(stats['weekday_counts'].items(), key=lambda x: x[1])[0]
        print(f"Busiest day: {stats['day_names'][busiest_day_idx]}")

def plot_histograms(stats: Dict, contributors: Union[str, List[str]], output_file: str = None):
    """Create visualization of commit patterns."""
    if stats['total_commits'] == 0:
        print("No data to plot.")
        return
    
    if isinstance(contributors, list):
        title = f"Combined Analysis for: {', '.join(contributors)}"
    else:
        title = f"Commit Patterns for {contributors}"
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{title}\nTotal commits: {stats["total_commits"]}', fontsize=16)
    
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

def list_contributors(repo_path: str, group_similar: bool = True):
    """List all contributors in the repository with optional grouping."""
    try:
        # Get all commits
        all_commits = get_all_commits(repo_path)
        
        if not all_commits:
            print("No commits found in repository.")
            return
        
        # Collect all unique authors
        author_entries = []
        for _, _, author_name, author_email in all_commits:
            if author_name or author_email:
                author_entries.append((author_name, author_email))
        
        unique_authors = set(author_entries)
        
        if group_similar:
            print(f"\nFound {len(unique_authors)} unique author entries (grouped by similarity):")
            print("=" * 100)
            
            # Group similar authors
            grouped_authors = group_contributors(list(unique_authors))
            
            # Count commits per group
            group_counts = {}
            for primary_name, entries in grouped_authors.items():
                count = 0
                for name, email in entries:
                    count += sum(1 for _, _, an, ae in all_commits 
                                if (an == name and (not email or ae == email)))
                group_counts[primary_name] = (count, entries)
            
            # Sort by commit count
            sorted_groups = sorted(group_counts.items(), key=lambda x: x[1][0], reverse=True)
            
            for i, (primary_name, (count, entries)) in enumerate(sorted_groups, 1):
                percentage = (count / len(all_commits)) * 100
                print(f"\n{i:3d}. {primary_name:30} {count:6d} commits ({percentage:5.1f}%)")
                for name, email in sorted(entries):
                    indent = " " * 6
                    if email:
                        print(f"{indent}• {name:25} <{email}>")
                    else:
                        print(f"{indent}• {name}")
        else:
            print(f"\nFound {len(unique_authors)} unique author entries (ungrouped):")
            print("=" * 100)
            
            # Count commits per author entry
            author_counts = {}
            for name, email in unique_authors:
                count = sum(1 for _, _, an, ae in all_commits if an == name and ae == email)
                author_counts[(name, email)] = count
            
            # Sort by commit count
            sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
            
            for i, ((name, email), count) in enumerate(sorted_authors, 1):
                percentage = (count / len(all_commits)) * 100
                if email:
                    print(f"{i:3d}. {name:30} <{email:40}> {count:6d} commits ({percentage:5.1f}%)")
                else:
                    print(f"{i:3d}. {name:30} {' ' * 40} {count:6d} commits ({percentage:5.1f}%)")
        
        print(f"\nTotal commits in repository: {len(all_commits)}")
        print("\nTip: Use --no-group to see ungrouped list")
        print("Tip: For multiple contributors, use: --contributors 'Name1' 'Name2' 'Name3'")
        
    except Exception as e:
        print(f"Error listing contributors: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze commit times for specific contributors or all contributors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s . --list-contributors
  %(prog)s . --list-contributors --no-group
  %(prog)s . --all-contributors
  %(prog)s . --contributors "John Doe"
  %(prog)s . --contributors "Scott Black" "sblack-usu"
  %(prog)s . --contributors "john" --email "john@example.com"
  %(prog)s . --all-contributors --plot
  %(prog)s . --contributors "John Doe" --plot
  %(prog)s . --contributors "Scott Black" "sblack-usu" --output-plot combined.png
        """
    )
    
    parser.add_argument('repository', help='Path to git repository')
    
    # Contributor selection
    contributor_group = parser.add_mutually_exclusive_group()
    contributor_group.add_argument('--contributors', nargs='+', 
                                  help='One or more contributor names (handles multiple aliases)')
    contributor_group.add_argument('--all-contributors', action='store_true', 
                                  help='Analyze ALL commits from ALL contributors')
    
    # Other arguments
    parser.add_argument('--email', help='Contributor email (optional, single email only)')
    parser.add_argument('--plot', action='store_true', help='Generate visualization plot')
    parser.add_argument('--output-plot', help='Output file for plot (e.g., plot.png)')
    parser.add_argument('--list-contributors', action='store_true', 
                       help='List all contributors in the repository with commit counts')
    parser.add_argument('--no-group', action='store_true',
                       help='Do not group similar names/emails when listing contributors')
    
    args = parser.parse_args()
    
    # List contributors if requested
    if args.list_contributors:
        list_contributors(args.repository, group_similar=not args.no_group)
        return
    
    # Analyze all contributors if requested
    if args.all_contributors:
        print("Analyzing ALL commits from ALL contributors...")
        commits = get_all_commits(args.repository)
        
        if not commits:
            print("No commits found in repository.")
            return
        
        stats = analyze_commit_times(commits)
        print_statistics(stats, "All Contributors")
        
        # Generate plot if requested
        if args.plot or args.output_plot:
            try:
                # Create a simple plot for all contributors
                plot_histograms(stats, "All Contributors", args.output_plot)
            except ImportError:
                print("\nMatplotlib not installed. Install with: pip install matplotlib")
            except Exception as e:
                print(f"\nError generating plot: {e}")
        return
    
    # Check if contributors are provided
    if not args.contributors:
        print("Error: Either specify contributors with --contributors or use --all-contributors")
        print("\nUse --list-contributors to see available contributors")
        print("Example: python git_commit_analyzer.py /path/to/repo --list-contributors")
        sys.exit(1)
    
    # Get commits for multiple contributors
    print(f"Analyzing commits for contributors: {', '.join(args.contributors)}")
    if args.email:
        print(f"With additional email: {args.email}")
    
    # Get commits for the specified contributors
    commits = get_commits_for_multiple_contributors(args.repository, args.contributors)
    
    # If single email provided, also get commits for that email
    if args.email:
        email_commits = get_all_commits(args.repository, emails=[args.email])
        # Merge commits, avoiding duplicates
        seen_hashes = set(hash for _, hash, _, _ in commits)
        for commit in email_commits:
            if commit[1] not in seen_hashes:
                commits.append(commit)
                seen_hashes.add(commit[1])
    
    if not commits:
        print(f"\nNo commits found for contributors: {', '.join(args.contributors)}")
        if args.email:
            print(f"With email: {args.email}")
        
        # Try to suggest similar names
        print("\nAvailable contributors (grouped):")
        list_contributors(args.repository, group_similar=True)
        return
    
    # Analyze commit times
    stats = analyze_commit_times(commits)
    
    # Print statistics
    print_statistics(stats, args.contributors)
    
    # Generate plot if requested
    if args.plot or args.output_plot:
        try:
            plot_histograms(stats, args.contributors, args.output_plot)
        except ImportError:
            print("\nMatplotlib not installed. Install with: pip install matplotlib")
        except Exception as e:
            print(f"\nError generating plot: {e}")

if __name__ == '__main__':
    main()

# Example usage:
# # List contributors with smart grouping (default)
# ./git_commit_analyzer.py . --list-contributors

# # List contributors without grouping
# ./git_commit_analyzer.py . --list-contributors --no-group

# # Analyze multiple contributors (handles different names/emails for same person)
# ./git_commit_analyzer.py . --contributors "Scott Black" "sblack-usu"

# # Analyze single contributor with email
# ./git_commit_analyzer.py . --contributors "John" --email "john@example.com"

# # Analyze all contributors
# ./git_commit_analyzer.py . --all-contributors

# # Generate plot for multiple contributors
# ./git_commit_analyzer.py . --contributors "Scott Black" "sblack-usu" --plot