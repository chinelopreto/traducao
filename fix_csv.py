#!/usr/bin/env python3
"""
fix_csv.py
----------
Fix the CSV parsing issues by handling the extra columns properly.
"""

import csv
import pandas as pd

def fix_csv_file(input_file="gmd1.csv", output_file="gmd1_fixed.csv"):
    """Fix CSV by reading line by line and handling extra columns."""
    
    print(f"Fixing {input_file}...")
    
    fixed_rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader)  # Read header
        print(f"Original header: {header}")
        
        # Expected header should be exactly 8 columns
        expected_header = ["#Index","Key","MsgJp","MsgEn","GmdPath","ArcPath","ArcName","ReadIndex"]
        
        fixed_rows.append(expected_header)
        
        for i, row in enumerate(csv_reader):
            if len(row) >= 8:
                # Take only first 8 columns and strip any trailing empty ones
                fixed_row = row[:8]
                # Remove trailing empty strings
                while len(fixed_row) > 8 and fixed_row[-1] == '':
                    fixed_row.pop()
                if len(fixed_row) == 8:
                    fixed_rows.append(fixed_row)
            elif len(row) > 0:  # Skip completely empty rows
                print(f"Skipping row {i+2} with {len(row)} fields: {row}")
    
    print(f"Fixed {len(fixed_rows)-1} data rows")
    
    # Write fixed CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerows(fixed_rows)
    
    print(f"Fixed CSV saved as {output_file}")
    
    # Verify the fixed file
    df = pd.read_csv(output_file, dtype=str, keep_default_na=False)
    print(f"Verification: {len(df)} rows, {len(df.columns)} columns")
    print("Sample:")
    print(df.head())

if __name__ == "__main__":
    fix_csv_file()