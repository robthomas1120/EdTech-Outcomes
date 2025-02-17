from flask import jsonify, send_file
import pandas as pd
import os
from typing import List
import io

def process_join_files(files: List, upload_folder: str) -> dict:
    """
    Process multiple CSV files and join them together.
    
    Args:
        files: List of file objects from the request
        upload_folder: Path to the upload folder
    
    Returns:
        dict: Response containing success status, preview data, and filename
    """
    try:
        # Read and combine all CSV files
        dataframes = []
        for file in files:
            if file.filename.endswith('.csv'):
                # Save the file temporarily
                temp_path = os.path.join(upload_folder, file.filename)
                file.save(temp_path)
                
                # Read the CSV
                df = pd.read_csv(temp_path)
                dataframes.append(df)
                
                # Clean up the temporary file
                os.remove(temp_path)
        
        if not dataframes:
            return {
                'success': False,
                'error': 'No valid CSV files provided'
            }
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Generate preview
        preview_rows = combined_df.head(5).to_string()
        
        # Save the combined file
        output_filename = 'combined_output.csv'
        output_path = os.path.join(upload_folder, output_filename)
        combined_df.to_csv(output_path, index=False)
        
        return {
            'success': True,
            'filename': output_filename,
            'total_rows': len(combined_df),
            'columns': combined_df.columns.tolist(),
            'preview': preview_rows
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def save_as_pdf(filepath: str) -> str:
    """
    Convert the CSV file to PDF format.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        df = pd.read_csv(filepath)
        pdf_path = filepath.rsplit('.', 1)[0] + '.pdf'
        
        # Create a styled HTML table
        styled_df = df.style.set_properties(**{
            'border': '1px solid black',
            'padding': '5px'
        }).hide_index()
        
        # Convert to PDF using df.to_html() and save
        html = f"""
        <html>
            <head>
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 5px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                {styled_df.to_html()}
            </body>
        </html>
        """
        
        # Save as PDF using pdfkit
        import pdfkit
        pdfkit.from_string(html, pdf_path)
        
        return pdf_path
        
    except Exception as e:
        raise Exception(f"Error converting to PDF: {str(e)}")