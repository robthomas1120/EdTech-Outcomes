import pandas as pd
import re

def fix_program_outcome_format(text, format_pattern):
    """
    Fix the format of program outcomes to match the specified pattern.
    
    Args:
        text (str): The text to fix
        format_pattern (str): The expected format pattern
        
    Returns:
        str: The fixed text
    """
    if pd.isna(text) or text == '' or not format_pattern:
        return text
        
    # Get prefix from pattern (e.g., 'BC' from 'BC_#')
    prefix = format_pattern.split('_')[0] if '_#' in format_pattern else format_pattern
    
    # Split by common separators (comma, space, dot)
    items = re.split(r'[,\s.]+', str(text))
    items = [item.strip() for item in items if item.strip()]
    
    fixed_items = []
    for item in items:
        # Remove all spaces and underscores
        cleaned = item.replace(' ', '').replace('_', '')
        
        # Extract numbers from the string
        numbers = re.findall(r'\d+', cleaned)
        if not numbers:
            continue
            
        number = numbers[0]  # Take the first number found
        
        # Handle special cases based on format pattern
        if '_#' in format_pattern:
            fixed = f"{prefix}_{number}"
        else:
            # For non-numbered patterns, use the pattern as is
            fixed = format_pattern
            
        fixed_items.append(fixed)
    
    # Join items with comma and space
    return ', '.join(fixed_items) if fixed_items else text

def validate_and_fix_format(text, format_pattern):
    """
    Validate and fix the format of outcomes.
    
    Args:
        text (str): The text to validate and fix
        format_pattern (str): The expected format pattern
        
    Returns:
        tuple: (fixed_text, list of errors found, has_format_error)
    """
    if pd.isna(text):
        return text, [], False
    
    # Fix the format
    fixed_text = fix_program_outcome_format(text, format_pattern)
    
    # Validate the fixed text
    errors = []
    has_error = False
    
    if fixed_text != text:
        errors.append(f"Fixed '{text}' to '{fixed_text}'")
    
    # Check if the fixed text matches the pattern
    items = fixed_text.split(', ')
    
    for item in items:
        if '_#' in format_pattern:
            prefix = format_pattern.split('_')[0]
            if not re.match(f'^{prefix}_\\d+$', item):
                errors.append(f"Unable to fix '{item}' to match pattern {format_pattern}")
                has_error = True
        else:
            if item != format_pattern:
                errors.append(f"Unable to fix '{item}' to match pattern {format_pattern}")
                has_error = True
    
    return fixed_text, errors, has_error

def read_file(filepath):
    """Read a file and return a pandas DataFrame."""
    if filepath.endswith('.csv'):
        return pd.read_csv(filepath)
    elif filepath.endswith('.xlsx'):
        return pd.read_excel(filepath, sheet_name='ALL')
    else:
        raise ValueError('Unsupported file type')

def validate_format(df, pattern):
    """Validate the format of Program Outcomes column."""
    errors = []
    if 'Program Outcomes' not in df.columns:
        return ['Program Outcomes column not found in file']
    
    # Check if pattern contains '_#'
    is_number_pattern = '_#' in pattern
    prefix = pattern.split('_')[0] if is_number_pattern else pattern
    
    for idx, value in enumerate(df['Program Outcomes']):
        if pd.isna(value) or value == '':
            continue
            
        # Split by comma and process each entry
        entries = [entry.strip() for entry in str(value).split(',')]
        
        for entry in entries:
            if is_number_pattern:
                # For patterns like 'BC_#', 'PHA_#', etc.
                if not (entry.startswith(prefix + '_') and 
                       len(entry) > len(prefix) + 1 and 
                       entry[len(prefix)+1:].isdigit() and 
                       ' ' not in entry):
                    errors.append(f'Row {idx + 1}: "{entry}" does not match format {pattern}. '
                                f'Format should be {prefix}_ followed by a number, with no spaces.')
            else:
                # For other patterns, must match exactly including spaces and case
                if entry != pattern:
                    errors.append(f'Row {idx + 1}: "{entry}" does not match format {pattern}')
    
    return errors

def process_file(filepath, format_pattern=None):
    """
    Process the uploaded file and return preview data.
    
    Args:
        filepath (str): Path to the uploaded file
        format_pattern (str): Expected format pattern
        
    Returns:
        dict: Dictionary containing preview data and unique values
    """
    try:
        df = read_file(filepath)
        
        # Define columns for display in preview
        display_columns = ['Program Outcomes', 'Course Outcomes']
        
        # Store the full dataframe for download
        full_df = df.copy()
        
        # Validate and fix Program Outcomes format if pattern is provided
        format_errors = []
        error_rows = []  # Track rows with format errors
        if format_pattern:
            # Apply validation and fixing to both display and full dataframes
            for idx, row in df.iterrows():
                if 'Program Outcomes' in df.columns:
                    fixed_text, errors, has_error = validate_and_fix_format(
                        row['Program Outcomes'], format_pattern
                    )
                    df.at[idx, 'Program Outcomes'] = fixed_text
                    full_df.at[idx, 'Program Outcomes'] = fixed_text
                    format_errors.extend([f"Row {idx + 1}: {err}" for err in errors])
                    if has_error:
                        error_rows.append(idx)

        # Create preview data with only display columns
        preview_df = df[display_columns].copy()
        
        # Get unique values for display columns
        unique_values = {col: sorted(df[col].dropna().unique().tolist()) 
                        for col in display_columns if col in df.columns}
        
        return {
            'preview_data': preview_df.to_dict('records'),
            'full_data': full_df.to_dict('records'),  # Include full data for download
            'unique_values': unique_values,
            'format_errors': format_errors,
            'error_rows': error_rows
        }
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")