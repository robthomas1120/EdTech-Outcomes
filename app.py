from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
from preprocessing import process_file, read_file, validate_format, fix_program_outcome_format
import pdfkit
from typing import List

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mapping')
def mapping():
    return render_template('mapping.html')

@app.route('/calculation')
def calculation():
    return render_template('calculation.html')

@app.route('/join')
def join():
    return render_template('join.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            format_pattern = request.form.get('format_pattern')
            df = read_file(filepath)
            
            # Get display columns (Program and Course Outcomes)
            display_columns = ['Program Outcomes', 'Course Outcomes']
            preview_df = df[display_columns] if all(col in df.columns for col in display_columns) else df
            
            preview_data = {
                'display_columns': preview_df.columns.tolist(),
                'preview_rows': preview_df.values.tolist(),
                'total_rows': len(preview_df),
                'format_errors': [],
                'unique_values': {
                    col: preview_df[col].dropna().unique().tolist()
                    for col in preview_df.columns
                }
            }

            if format_pattern:
                # Validate format if pattern is provided
                preview_data['format_errors'] = validate_format(df, format_pattern)

            return jsonify({
                'success': True,
                'filename': filename,
                'preview': preview_data
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Invalid file type'})

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

@app.route('/fix-format', methods=['POST'])
def fix_format():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['file']
    format_pattern = request.form.get('format_pattern', 'BC_#')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Read the file
            df = read_file(filepath)
            
            # Fix the format in the Program Outcomes column
            if 'Program Outcomes' in df.columns:
                df['Program Outcomes'] = df['Program Outcomes'].apply(
                    lambda x: fix_program_outcome_format(x, format_pattern)
                )
            
            # Save the fixed file
            output_filename = f"fixed_{filename}"
            output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            if filename.endswith('.xlsx'):
                df.to_excel(output_filepath, index=False)
            else:
                df.to_csv(output_filepath, index=False)
            
            # Return preview of fixed data
            display_columns = ['Program Outcomes', 'Course Outcomes']
            preview_df = df[display_columns] if all(col in df.columns for col in display_columns) else df
            
            return jsonify({
                'success': True,
                'filename': output_filename,
                'preview': {
                    'display_columns': preview_df.columns.tolist(),
                    'preview_rows': preview_df.values.tolist(),
                    'total_rows': len(preview_df),
                    'unique_values': {
                        col: preview_df[col].dropna().unique().tolist()
                        for col in preview_df.columns
                    }
                }
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Invalid file type'})

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
        pdfkit.from_string(html, pdf_path)
        
        return pdf_path
        
    except Exception as e:
        raise Exception(f"Error converting to PDF: {str(e)}")

@app.route('/process-join', methods=['POST'])
def process_join():
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'})
    
    files = request.files.getlist('files[]')
    result = process_join_files(files, app.config['UPLOAD_FOLDER'])
    
    if result['success']:
        # Convert to PDF
        try:
            csv_path = os.path.join(app.config['UPLOAD_FOLDER'], result['filename'])
            pdf_path = save_as_pdf(csv_path)
            result['pdf_filename'] = os.path.basename(pdf_path)
        except Exception as e:
            # If PDF conversion fails, we still return the CSV result
            result['pdf_error'] = str(e)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)