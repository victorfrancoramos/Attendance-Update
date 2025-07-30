"""
Script: Attendance Update Automation

Description:
------------
This script automates the process of updating attendance records by integrating data from a ZOOM attendance CSV file
and a Sabacloud roster CSV file.

Workflow:
---------
1. Load the ZOOM attendance CSV file (skipping initial metadata rows) containing columns such as "Name (original name)", "Email", etc.
2. Load the Sabacloud roster CSV file and process it by:
   - Combining the 'First Name' and 'Last Name' columns into a new "Full Name" column.
   - Renaming the "Audience Subtype" column to "Attendance Status" for tracking attendance.
3. Utilize fuzzy matching (using the rapidfuzz library) to map ZOOM attendee names to the roster's "Full Name" based on a defined threshold.
4. Log any unmatched ZOOM attendees to a text file, starting with the fuzzy matching threshold for later review.
5. Update the attendance status of students in the roster:
   - If a matching ZOOM record (or records) is found (via fuzzy matching) and the "Total duration (minutes)"
    is equal or greater than a defined threshold, the attendance status is set to "Successful".
   - If there is a match but the total duration is below the threshold, the status is set to "Unsuccessful".
   - If no matching ZOOM record is found, the status is set to "No Show".
6. Save the updated roster data back to a CSV file.

Dependencies:
-------------
- pandas
- rapidfuzz

Usage:
------
- Configure file paths and thresholds as needed.
- Run the script to process attendance automatically.

Author: Victor Franco
Date: 30-JUL-2025
Version: 1.4
"""
# ---------------------------
# Imported Modules
# ---------------------------
import pandas as pd
from rapidfuzz import process, fuzz  # using RapidFuzz for fuzzy matching

# ---------------------------
# Configuration / Constants
# ---------------------------
ZOOM_ATTENDANCE_FILE = 'zoom_attendance.csv'
ROSTER_FILE = 'sabacloud_roster.csv'
UPDATED_ROSTER_FILE = 'updated_sabacloud_roster.csv'
UNMATCHED_FILE = 'unmatched_attendees.txt'
SKIP_ROWS = 3                # Skip metadata rows in ZOOM CSV
FUZZY_THRESHOLD = 55         # Fuzzy matching threshold for comparing names
ATTENDANCE_THRESHOLD = 10    # Minimum total duration (minutes) to consider attendance Successful

# ---------------------------
# Helper Functions
# ---------------------------
def load_zoom_data(file: str, skip_rows: int) -> pd.DataFrame:
    """
    Load the ZOOM attendance CSV file, skipping initial metadata rows.
    Expected columns include "Name (original name)" and "Total duration (minutes)".
    """
    return pd.read_csv(file, skiprows=skip_rows)


def load_roster_data(file: str) -> pd.DataFrame:
    """
    Load the Sabacloud roster CSV file, combine 'First Name' and 'Last Name' into a new "Full Name" column,
    and rename 'Audience Subtype' to 'Attendance Status' for later updates.
    """
    df = pd.read_csv(file)
    df['Full Name'] = df['First Name'] + ' ' + df['Last Name']
    df.rename(columns={'Audience Subtype': 'Attendance Status'}, inplace=True)
    return df


def match_student(zoom_name: str, roster_names: list, threshold: int) -> str:
    """
    Use fuzzy matching to find a matching roster name for the given ZOOM name.
    Returns the matched roster name if the score meets/exceeds the threshold, else returns None.
    """
    match, score, _ = process.extractOne(zoom_name, roster_names, scorer=fuzz.token_sort_ratio)
    return match if score >= threshold else None


def process_attendance(zoom_df: pd.DataFrame, roster_df: pd.DataFrame, threshold: int):
    """
    Process ZOOM attendance:
      - Fuzzy match each ZOOM attendee to a roster entry.
      - Returns a dictionary of matched students and a list of unmatched Zoom attendees.
      - Prints the matched and unmatched students, specifying the ones that do not comply with the attendance threshold
    
    Returns:
      matched_duration: dict mapping roster names to the session duration.
      unmatched_attendees: list of ZOOM attendee names that could not be matched.
    """
    roster_names = roster_df['Full Name'].tolist()
    matched_duration = {}    # Dict to store total duration for each roster name that is matched
    unmatched_attendees = [] # List of ZOOM names with no match

    for _, row in zoom_df.iterrows():
        zoom_name = row['Name (original name)']
        # Convert duration to float; defaulting to 0 if missing
        duration = float(row.get('Total duration (minutes)', 0))
        matched = match_student(zoom_name, roster_names, threshold)
        if matched and duration >= ATTENDANCE_THRESHOLD:
            print(f"  ✅ {zoom_name} > {matched}")
            matched_duration[matched] = duration
        elif matched and duration < ATTENDANCE_THRESHOLD:
            print(f"  ❌ {zoom_name} > {matched} (Duration: {duration})")
            matched_duration[matched] = duration
        else:
            print(f"  ⚠️ {zoom_name} ⚠️")
            unmatched_attendees.append(zoom_name)
    return matched_duration, unmatched_attendees


def write_unmatched_attendees(unmatched: list, threshold: int, file: str):
    """
    Write the fuzzy matching threshold and the list of unmatched ZOOM attendee names to a text file.
    """
    # Sort the unmatched attendees alphabetically in a case-insensitive manner
    unmatched_sorted = sorted(unmatched, key=str.lower)
    with open(file, "w", encoding="utf-8") as f:
        f.write(f"Fuzzy Matching Threshold: {threshold}\n\n")
        f.write("Unmatched ZOOM Attendees:\n")
        for attendee in unmatched_sorted:
            f.write(f"{attendee}\n")
    print(f"💾 Unmatched attendees saved to '{file}'.")


def update_attendance_status(roster_df: pd.DataFrame, matched_duration: dict, threshold: float) -> pd.DataFrame:
    """
    Update the "Attendance Status" for each roster entry based on the ZOOM attendance duration:
      - Set to "Successful" if the total duration is >= the attendance threshold.
      - Set to "Unsuccessful" if a match exists but the total duration is below the threshold.
      - Set to "No Show" if no matching Zoom record is found.
    """
    for idx, row in roster_df.iterrows():
        roster_name = row['Full Name']
        if roster_name in matched_duration:
            total_duration = matched_duration[roster_name]
            if total_duration >= threshold:
                roster_df.at[idx, 'Attendance Status'] = "Successful"
            else:
                roster_df.at[idx, 'Attendance Status'] = "Unsuccessful"
        else:
            roster_df.at[idx, 'Attendance Status'] = "No Show"
    return roster_df


# ---------------------------
# Main Execution
# ---------------------------
def main():
    # Load input data from CSV files.
    zoom_df = load_zoom_data(ZOOM_ATTENDANCE_FILE, SKIP_ROWS)
    roster_df = load_roster_data(ROSTER_FILE)

    # Process Zoom attendance and match to roster entries using fuzzy matching.
    print(f"🔄 Matching ZOOM attendance to roster (Fuzzy threshold {FUZZY_THRESHOLD}):")
    matched_duration, unmatched_attendees = process_attendance(zoom_df, roster_df, FUZZY_THRESHOLD)
    write_unmatched_attendees(unmatched_attendees, FUZZY_THRESHOLD, UNMATCHED_FILE)

    # Update each roster entry with the appropriate Attendance Status.
    updated_roster_df = update_attendance_status(roster_df, matched_duration, ATTENDANCE_THRESHOLD)

    # Save the updated roster with new attendance statuses to CSV.
    updated_roster_df.to_csv(UPDATED_ROSTER_FILE, index=False)
    print(f"💾 Updated roster saved to '{UPDATED_ROSTER_FILE}'.")


if __name__ == "__main__":
    main()
