"""
Script: Attendance Update Automation

Description:
------------
This script automates the process of updating attendance records by integrating data from a Zoom attendance CSV file and a Sabacloud roster CSV file.

Workflow:
---------
1. Load the Zoom attendance CSV file (skipping initial metadata rows) containing columns such as "Name (original name)", "Email", etc.
2. Load the Sabacloud roster CSV file and process it by:
   - Combining the 'First Name' and 'Last Name' columns into a new "Full Name" column.
   - Renaming the "Audience Subtype" column to "Attendance Status" for tracking attendance.
3. Utilize fuzzy matching (using the rapidfuzz library) to map Zoom attendee names to the roster's "Full Name" based on a defined threshold.
4. Log any unmatched Zoom attendees to a text file, starting with the fuzzy matching threshold for later review.
5. Update the attendance status of matched students in the roster to 'Successful'.
6. Save the updated roster data back to a CSV file.

Dependencies:
-------------
- pandas
- rapidfuzz

Usage:
------
- Configure file paths and the fuzzy matching threshold as needed.
- Run the script to process attendance automatically.

Author: Victor Franco
Date: 29-JUL-2025
"""

import pandas as pd
from rapidfuzz import process, fuzz  # using RapidFuzz for fuzzy matching

# ---------------------------
# Configuration / Constants
# ---------------------------
ZOOM_ATTENDANCE_FILE = 'zoom_attendance.csv'
ROSTER_FILE = 'sabacloud_roster.csv'
UPDATED_ROSTER_FILE = 'updated_sabacloud_roster.csv'
UNMATCHED_FILE = 'unmatched_attendees.txt'
SKIP_ROWS = 3          # Zoom CSV attendance file: skip the first 3 lines
FUZZY_THRESHOLD = 50   # Fuzzy matching threshold


# ---------------------------
# Helper Functions
# ---------------------------
def load_zoom_data(file: str, skip_rows: int) -> pd.DataFrame:
    """
    Load the Zoom attendance CSV file, skipping initial rows.
    """
    return pd.read_csv(file, skiprows=skip_rows)


def load_roster_data(file: str) -> pd.DataFrame:
    """
    Load the Sabacloud roster CSV file, combine first and last names into 'Full Name',
    and rename the 'Audience Subtype' column to 'Attendance Status'.
    """
    df = pd.read_csv(file)
    df['Full Name'] = df['First Name'] + ' ' + df['Last Name']
    df.rename(columns={'Audience Subtype': 'Attendance Status'}, inplace=True)
    return df


def match_student(zoom_name: str, roster_names: list, threshold: int) -> str:
    """
    Use fuzzy matching to find a matching roster name for the given Zoom name.
    Returns the matched name if the score is above the threshold, else returns None.
    """
    match, score, _ = process.extractOne(zoom_name, roster_names, scorer=fuzz.token_sort_ratio)
    return match if score >= threshold else None


def process_attendance(zoom_df: pd.DataFrame, roster_df: pd.DataFrame, threshold: int):
    """
    Process Zoom attendance: fuzzy match each Zoom attendee against the roster.
    Returns a dictionary of matched students and a list of unmatched Zoom attendees.
    """
    roster_names = roster_df['Full Name'].tolist()
    matched_students = {}
    unmatched_attendees = []

    for name in zoom_df['Name (original name)']:
        match = match_student(name, roster_names, threshold)
        if match:
            matched_students[name] = match
        else:
            print(f"⚠️ Could not match Zoom attendee '{name}' to any roster student.")
            unmatched_attendees.append(name)

    return matched_students, unmatched_attendees


def write_unmatched_attendees(unmatched: list, threshold: int, file: str):
    """
    Write the fuzzy matching threshold and list of unmatched Zoom attendees to a text file.
    """
    with open(file, "w", encoding="utf-8") as f:
        f.write(f"Fuzzy Matching Threshold: {threshold}\n\n")
        f.write("Unmatched Zoom Attendees:\n")
        for attendee in unmatched:
            f.write(f"{attendee}\n")
    print(f"✅ Unmatched attendees have been saved to '{file}'.")


def update_attendance_status(roster_df: pd.DataFrame, matched: dict, status: str = 'Successful') -> pd.DataFrame:
    """
    Update the attendance status for each matched student in the roster dataframe.
    """
    for _, roster_name in matched.items():
        index_list = roster_df.index[roster_df['Full Name'] == roster_name].tolist()
        if index_list:
            roster_df.loc[index_list, 'Attendance Status'] = status
        else:
            print(f"❌ Could not find roster entry for matched name '{roster_name}'.")
    return roster_df


# ---------------------------
# Main Execution
# ---------------------------
def main():
    # Load data
    zoom_df = load_zoom_data(ZOOM_ATTENDANCE_FILE, SKIP_ROWS)
    roster_df = load_roster_data(ROSTER_FILE)

    # Process attendance with fuzzy matching
    matched_students, unmatched_attendees = process_attendance(zoom_df, roster_df, FUZZY_THRESHOLD)
    write_unmatched_attendees(unmatched_attendees, FUZZY_THRESHOLD, UNMATCHED_FILE)

    # Update attendance status for matched students
    updated_roster_df = update_attendance_status(roster_df, matched_students)

    # Save updated roster to CSV file
    updated_roster_df.to_csv(UPDATED_ROSTER_FILE, index=False)
    print(f"✅ Updated roster saved to '{UPDATED_ROSTER_FILE}'.")


if __name__ == "__main__":
    main()
