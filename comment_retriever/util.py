import locale
import time
from datetime import datetime, date
import pandas as pd


def get_date_difference(time_values_c):
    print(time_values_c)
    # Define possible date formats for string inputs
    date_formats = [
        '%Y-%m-%d %I:%M:%S %p',  # e.g., 2024-09-11 12:00:00 AM
        '%d/%b/%y',  # e.g., 18/Dec/20
        '%m/%d/%y'  # e.g., 2/19/18
    ]

    # Convert inputs to date objects
    dates = []
    for t in time_values_c:
        if isinstance(t, (datetime, date)):
            # If it's already a datetime or date, extract the date part
            dates.append(t.date() if isinstance(t, datetime) else t)
        else:
            # Assume it's a string and try parsing
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(t.split(' ')[0], fmt.split(' ')[0]).date()
                    dates.append(parsed_date)
                    break
                except (ValueError, AttributeError):
                    continue

    # Check if dates list is empty
    if not dates:
        return '-', '-', 0
        # raise ValueError("No valid dates could be parsed from the input.")

    # Find min and max dates
    min_date = min(dates)
    max_date = max(dates)

    # Calculate difference
    date_diff = max_date - min_date

    min_date_str = min_date.strftime('%d %B, %Y')
    max_date_str = max_date.strftime('%d %B, %Y')

    return min_date_str, max_date_str, date_diff.days


def process_comments(csv_file_path, filter_by_round='', filter_by_round_exist='', filter_by_team_name='', filter_by_team_name_present=True, drop_text_na=True, drop_date_na=False):
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Group by project
    grouped = df.groupby('project')

    # Dictionary to store results
    results_comments = {}
    results_time = {}
    # List to store filtered groups
    filtered_groups = []

    # Process each project group
    for project_name, group in grouped:
        # Start with the entire group
        filtered_group = group

        # Apply round exist filter if provided
        if len(filter_by_round_exist) >= 1:
            round_exist = int(filter_by_round_exist)
            # Get comment_ids that have at least one row with the specified round
            valid_comment_ids = group[group['round'] == round_exist]['comment_id'].unique()
            # Filter group to keep only rows with valid comment_ids
            filtered_group = filtered_group[filtered_group['comment_id'].isin(valid_comment_ids)]

        # Apply round filter if provided
        if '-' in filter_by_round:
            split_round_value = filter_by_round.split('-')
            smallest_round = int(split_round_value[0])
            if len(split_round_value) == 2:
                try:
                    largest_round = int(split_round_value[1])
                except:
                    largest_round = df['round'].max()
                filtered_group = filtered_group[
                    (filtered_group['round'] >= smallest_round) & (filtered_group['round'] <= largest_round)]
            else:
                filtered_group = filtered_group[filtered_group['round'] == smallest_round]
        elif len(filter_by_round) >= 1:
            filtered_group = filtered_group[filtered_group['round'] == int(filter_by_round)]

        # Apply team filter if provided, on the filtered group
        if len(filter_by_team_name) >= 1:
            print(f"filter_by_team_name: {filter_by_team_name}, filter_by_team_name_present: {filter_by_team_name_present}")
            if filter_by_team_name_present:
                filtered_group = filtered_group[
                    filtered_group['comment_id'].str.lower().str.contains(filter_by_team_name.lower(), na=False)]
            else:
                filtered_group = filtered_group[
                    ~filtered_group['comment_id'].str.lower().str.contains(filter_by_team_name.lower(), na=False)]

        # Append filtered group to list
        filtered_groups.append(filtered_group)

        # Extract comments and times from the final filtered group
        if drop_text_na:
            round_comments = filtered_group['comment_text'].dropna().tolist()
        else:
            round_comments = filtered_group['comment_text'].tolist()
        if drop_date_na:
            round_time = filtered_group['date_received'].dropna().tolist()
        else:
            round_time = filtered_group['date_received'].tolist()

        results_comments[project_name] = round_comments
        results_time[project_name] = round_time

    return results_comments, results_time


def extract_numbered_points_simple(file_path, expected_count=5):
    """
    Simple extraction: find first occurrence of "1." and capture from there.
    Removes empty strings from the result.
    """
    with open(file_path, 'r') as rf:
        content = rf.read()

    # Find the position where "1." first appears at the start of a line
    lines = content.split('\n')
    start_idx = -1

    for i, line in enumerate(lines):
        if line.strip().startswith('1.'):
            start_idx = i
            break

    if start_idx == -1:
        return []

    # Collect lines from that point onward until we have expected_count points
    result_lines = []
    point_count = 0

    for i in range(start_idx, len(lines)):
        line = lines[i].strip()

        # Check if this is a new numbered point
        if line and line[0].isdigit() and '.' in line[:3]:
            try:
                num = int(line.split('.')[0])
                point_count = num
                if point_count <= expected_count:
                    result_lines.append(lines[i])
                else:
                    break
            except ValueError:
                result_lines.append(lines[i])
        elif result_lines and line:  # Continuation of previous point (only if not empty)
            result_lines.append(lines[i])

        # Stop if we've processed all expected points and hit a blank line
        if point_count >= expected_count and not line:
            break

    # Remove empty strings and strip whitespace
    result_lines = [line for line in result_lines if line.strip()]

    return result_lines