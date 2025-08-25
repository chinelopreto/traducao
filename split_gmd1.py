#!/usr/bin/env python3
"""
split_gmd1.py
--------------
Split the large gmd1.csv file into smaller block files for translation processing.
Creates gmd1_block_1.csv through gmd1_block_7.csv.
"""

import os
import pandas as pd
import csv

def split_gmd1_csv(input_file="gmd1.csv", num_blocks=7):
    """Split gmd1.csv into num_blocks smaller files."""
    
    print(f"Reading {input_file}...")
    # Read CSV with error handling for extra columns
    try:
        df = pd.read_csv(input_file, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL)
    except pd.errors.ParserError as e:
        print(f"Parser error: {e}")
        print("Trying with on_bad_lines='skip'...")
        df = pd.read_csv(input_file, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL, on_bad_lines='skip')
    
    # Keep only required columns if extra columns exist
    required_cols = ["#Index","Key","MsgJp","MsgEn","GmdPath","ArcPath","ArcName","ReadIndex"]
    if all(col in df.columns for col in required_cols):
        df = df[required_cols]
    
    print(f"Total rows: {len(df)}")
    
    # Calculate rows per block
    rows_per_block = len(df) // num_blocks
    remainder = len(df) % num_blocks
    
    print(f"Splitting into {num_blocks} blocks (~{rows_per_block} rows each)")
    
    start_idx = 0
    for block_num in range(1, num_blocks + 1):
        # Add one extra row to first 'remainder' blocks to distribute evenly
        block_size = rows_per_block + (1 if block_num <= remainder else 0)
        end_idx = start_idx + block_size
        
        block_df = df.iloc[start_idx:end_idx].copy()
        output_file = f"gmd1_block_{block_num}.csv"
        
        print(f"Creating {output_file} with {len(block_df)} rows (rows {start_idx+1}-{end_idx})")
        block_df.to_csv(output_file, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
        
        start_idx = end_idx
    
    print("Split complete!")

if __name__ == "__main__":
    split_gmd1_csv()