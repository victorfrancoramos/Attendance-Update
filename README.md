# Attendance-Update

## Description

This script automates the process of updating attendance records by integrating data from a Zoom attendance CSV file and a Sabacloud roster CSV file. It performs the following operations:

- Loads a Zoom attendance CSV file (skipping initial metadata rows) containing columns such as "Name (original name)", "Email", "Total duration (minutes)", etc.
- Loads the Sabacloud roster CSV file and processes it by:
  - Combining the 'First Name' and 'Last Name' columns into a new "Full Name" column.
  - Renaming the "Audience Subtype" column to "Attendance Status" for tracking attendance updates.
- Uses fuzzy matching (with the RapidFuzz library) to map Zoom attendee names to the roster's "Full Name" based on a configurable matching threshold.
- Logs any unmatched Zoom attendees to a text file, including the fuzzy matching threshold used for review.
- Updates the attendance status of matched students to "Successful" in the roster.
- Saves the updated roster to a new CSV file.

## Workflow

1. **Data Loading:**
   - **Zoom Data:** Reads the Zoom attendance CSV file while skipping the first few metadata rows.
   - **Roster Data:** Reads the Sabacloud roster CSV file, combines name fields, and renames the relevant status column.

2. **Fuzzy Matching:**
   - Compares each Zoom attendee’s name with the list of roster "Full Name" entries.
   - Uses a configurable fuzzy matching threshold to determine a match.
   - Stores matched students and logs unmatched attendees.

3. **Attendance Update:**
   - Updates the attendance status for matched students in the roster.
   - Saves the updated roster back to a CSV file.

4. **Logging:**
   - Generates a text file listing all unmatched Zoom attendees along with the fuzzy matching threshold used.

## Dependencies

- [pandas](https://pandas.pydata.org/)
- [rapidfuzz](https://github.com/maxbachmann/RapidFuzz)
