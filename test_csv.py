"""
Test script to analyze CSV files and determine their structure.
This can be run locally to debug file format issues.

Usage:
1. Save this script as test_csv.py
2. Run: python test_csv.py path/to/your/file.csv
"""

import sys
import os
import csv
import pandas as pd
import chardet

def analyze_file(filepath):
    """Analyze a CSV file and print detailed information about its format."""
    print(f"\n{'='*60}")
    print(f"Analyzing file: {filepath}")
    print(f"{'='*60}")
    
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} does not exist")
        return
    
    # Get file size
    file_size = os.path.getsize(filepath)
    print(f"File size: {file_size} bytes")
    
    # Read raw file content
    with open(filepath, 'rb') as f:
        raw_content = f.read()
    
    # Detect encoding
    detection = chardet.detect(raw_content)
    print(f"Detected encoding: {detection['encoding']} (confidence: {detection['confidence']})")
    
    # Try to decode with detected encoding
    try:
        content = raw_content.decode(detection['encoding'])
        print("Successfully decoded the file")
    except UnicodeDecodeError:
        print("Failed to decode with detected encoding, trying utf-8...")
        try:
            content = raw_content.decode('utf-8')
            print("Successfully decoded as utf-8")
        except UnicodeDecodeError:
            print("Failed to decode as utf-8, trying latin-1...")
            try:
                content = raw_content.decode('latin-1')
                print("Successfully decoded as latin-1")
            except:
                print("Could not decode file with common encodings")
                return
    
    # Count line endings
    newlines = content.count('\n')
    carriage_returns = content.count('\r')
    print(f"Line endings: {newlines} newlines, {carriage_returns} carriage returns")
    
    # Count potential delimiters
    delimiters = [',', '\t', ';', '|']
    counts = {d: content.count(d) for d in delimiters}
    print("Delimiter counts:")
    for d, count in counts.items():
        print(f"  '{d if d != '\t' else '\\t'}': {count}")
    
    # Determine most likely delimiter
    best_delimiter = max(counts.items(), key=lambda x: x[1])[0]
    if counts[best_delimiter] == 0:
        print("No common delimiter found, checking if space-delimited...")
        space_count = content.count(' ')
        print(f"Space count: {space_count}")
        if space_count > 0:
            best_delimiter = ' '
            print("File might be space-delimited")
        else:
            print("Could not determine delimiter")
            return
    else:
        print(f"Most likely delimiter: '{best_delimiter if best_delimiter != '\t' else '\\t'}'")
    
    # Try to parse with csv module
    try:
        lines = content.splitlines()
        reader = csv.reader(lines, delimiter=best_delimiter)
        rows = list(reader)
        
        if rows:
            header = rows[0]
            print(f"\nFound {len(rows)} rows with {len(header)} columns")
            print(f"Header: {header}")
            
            if len(rows) > 1:
                print(f"\nFirst data row: {rows[1]}")
            
            # Check for inconsistent row lengths
            row_lengths = [len(row) for row in rows]
            unique_lengths = set(row_lengths)
            if len(unique_lengths) > 1:
                print(f"\nWarning: Inconsistent row lengths detected!")
                print(f"Row length counts: {[(length, row_lengths.count(length)) for length in unique_lengths]}")
        else:
            print("No rows found in the file")
            
    except Exception as e:
        print(f"Error parsing with csv module: {str(e)}")
    
    # Try with pandas
    print("\nTrying to parse with pandas...")
    try:
        df = pd.read_csv(filepath, delimiter=best_delimiter, encoding=detection['encoding'], engine='python', error_bad_lines=False)
        print(f"Successfully parsed with pandas: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Column names: {df.columns.tolist()}")
        
        if not df.empty:
            print("\nSample data (first 2 rows):")
            print(df.head(2))
            
    except Exception as e:
        print(f"Error parsing with pandas: {str(e)}")
        
        # Try alternate approach
        print("\nTrying alternative pandas approaches...")
        
        # Try delim_whitespace
        try:
            df = pd.read_csv(filepath, delim_whitespace=True, encoding=detection['encoding'], engine='python', error_bad_lines=False)
            print(f"Successfully parsed with delim_whitespace=True: {df.shape[0]} rows, {df.shape[1]} columns")
        except Exception as e:
            print(f"Error parsing with delim_whitespace: {str(e)}")
            
        # Try other encodings
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            if encoding != detection['encoding']:
                try:
                    df = pd.read_csv(filepath, delimiter=best_delimiter, encoding=encoding, engine='python', error_bad_lines=False)
                    print(f"Successfully parsed with encoding '{encoding}': {df.shape[0]} rows, {df.shape[1]} columns")
                    break
                except Exception as e:
                    print(f"Error parsing with encoding '{encoding}': {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_csv.py path/to/your/file.csv")
        sys.exit(1)
        
    filepath = sys.argv[1]
    analyze_file(filepath)