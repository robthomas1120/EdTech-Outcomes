from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
from preprocessing import process_file, read_file, validate_format, fix_program_outcome_format
from calculation import calculation_bp  # Import the blueprint
from mapping import mapping_bp  # Import the mapping blueprint
import pdfkit
from typing import List

app = Flask(__name__)  # Create Flask app instance first
app.register_blueprint(calculation_bp)  # Then register the blueprint
app.register_blueprint(mapping_bp, url_prefix='/mapping')  # Register the mapping blueprint with prefix

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

@app.route('/preprocessing')
def preprocessing():
    return render_template('index.html')

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
        
        # Limit the dataframe to a manageable size for the PDF
        if len(df) > 1000:
            preview_df = df.head(1000)
            truncated_message = "<p><strong>Note:</strong> This PDF shows only the first 1000 rows of the data.</p>"
        else:
            preview_df = df
            truncated_message = ""
        
        # Handle very wide dataframes by only showing the first 20 columns
        max_cols = 20
        if len(preview_df.columns) > max_cols:
            preview_df = preview_df.iloc[:, :max_cols]
            cols_message = f"<p><strong>Note:</strong> Only the first {max_cols} columns are shown in this PDF.</p>"
            truncated_message += cols_message
        
        # Create a styled HTML table with better formatting
        styles = [
            dict(selector="th", props=[("font-weight", "bold"),
                                     ("background-color", "#f2f2f2"),
                                     ("border", "1px solid black"),
                                     ("padding", "5px"),
                                     ("text-align", "center")]),
            dict(selector="td", props=[("border", "1px solid black"),
                                     ("padding", "5px"),
                                     ("max-width", "200px"),
                                     ("overflow", "hidden"),
                                     ("text-overflow", "ellipsis"),
                                     ("white-space", "nowrap")]),
            dict(selector="table", props=[("border-collapse", "collapse"),
                                        ("width", "100%"),
                                        ("font-size", "10pt")])
        ]
        
        # Handle potential styling issues with large datasets
        try:
            # Try with full styling
            styled_df = preview_df.style.set_table_styles(styles).hide_index()
            html_table = styled_df.to_html()
        except:
            # Fallback to basic styling if the dataframe is too large
            html_table = preview_df.to_html(index=False, border=1, classes="dataframe")
        
        # Build complete HTML with CSS for better printing
        html = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <title>Combined CSV Data</title>
                <style>
                    @page {{
                        size: landscape;
                        margin: 0.5cm;
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        page-break-inside: auto;
                    }}
                    tr {{
                        page-break-inside: avoid;
                        page-break-after: auto;
                    }}
                    th, td {{
                        border: 1px solid black;
                        padding: 5px;
                        text-align: left;
                        max-width: 200px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        font-weight: bold;
                        text-align: center;
                    }}
                    h1 {{
                        text-align: center;
                        font-size: 14pt;
                    }}
                    .metadata {{
                        margin-bottom: 15px;
                        font-size: 9pt;
                    }}
                </style>
            </head>
            <body>
                <h1>Combined CSV Data</h1>
                <div class="metadata">
                    <p><strong>Total Rows:</strong> {len(df)}</p>
                    <p><strong>Total Columns:</strong> {len(df.columns)}</p>
                    <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                {truncated_message}
                {html_table}
            </body>
        </html>
        """
        
        # Configure pdfkit options for better rendering
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '0.5cm',
            'margin-right': '0.5cm',
            'margin-bottom': '0.5cm',
            'margin-left': '0.5cm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'zoom': 0.8
        }
        
        # Save as PDF using pdfkit
        pdfkit.from_string(html, pdf_path, options=options)
        
        return pdf_path
        
    except Exception as e:
        raise Exception(f"Error converting to PDF: {str(e)}")

def process_join_files(files: List, upload_folder: str) -> dict:
    """
    Simple function to join CSV files by appending rows.
    With NaN handling for JSON serialization.
    
    Args:
        files: List of file objects from the request
        upload_folder: Path to the upload folder
    
    Returns:
        dict: Response containing success status, preview data, and filename
    """
    import datetime
    import pandas as pd
    import numpy as np
    import json
    
    try:
        # Create empty DataFrame to hold all data
        combined_df = None
        processed_files = []
        
        # Process each file
        for file in files:
            if not file.filename:
                continue
                
            # Save file temporarily
            temp_path = os.path.join(upload_folder, secure_filename(file.filename))
            file.save(temp_path)
            
            # Read CSV file
            try:
                df = pd.read_csv(temp_path)
                processed_files.append(file.filename)
                print(f"Successfully read {file.filename} with {len(df)} rows and {len(df.columns)} columns")
                
                # If this is the first file, use it as the base
                if combined_df is None:
                    combined_df = df
                else:
                    # Append this file's rows to the combined DataFrame
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
                    print(f"Combined DataFrame now has {len(combined_df)} rows")
            except Exception as e:
                print(f"Error reading {file.filename}: {str(e)}")
            
            # Clean up temporary file
            os.remove(temp_path)
        
        # Check if we successfully processed any files
        if combined_df is None or combined_df.empty:
            return {
                'success': False,
                'error': 'Could not process any of the uploaded files'
            }
        
        # Generate output filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'combined_{timestamp}.csv'
        output_path = os.path.join(upload_folder, output_filename)
        
        # Save combined data to CSV
        combined_df.to_csv(output_path, index=False)
        print(f"Saved combined file with {len(combined_df)} rows to {output_filename}")
        
        # Custom JSON encoder to handle NaN values
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return None if np.isnan(obj) else float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if pd.isna(obj):
                    return None
                return super(NpEncoder, self).default(obj)
        
        # Convert preview to dictionary with NaN handling
        preview_df = combined_df.head(10).copy()
        
        # Replace NaN with None
        preview_df = preview_df.replace({np.nan: None})
        preview_dict = preview_df.to_dict('records')
        
        # Return the result
        result = {
            'success': True,
            'filename': output_filename,
            'total_rows': len(combined_df),
            'columns': combined_df.columns.tolist(),
            'preview': preview_dict,
            'processed_files': processed_files
        }
        
        # Serialize to JSON and back to ensure no NaN values remain
        json_result = json.dumps(result, cls=NpEncoder)
        return json.loads(json_result)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': f'Error joining files: {str(e)}'
        }

@app.route('/process-join', methods=['POST'])
def process_join():
    """
    Process the uploaded files for joining.
    With NaN handling for proper JSON serialization.
    """
    try:
        if 'files[]' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No files provided in the request'
            })
        
        files = request.files.getlist('files[]')
        
        # Check if we received any files
        if not files or all(not f.filename for f in files):
            return jsonify({
                'success': False, 
                'error': 'No files were selected for upload'
            })
        
        # Log incoming files for debugging
        print(f"Received {len(files)} files for joining:")
        for file in files:
            if file.filename:
                print(f"  - {file.filename}")
        
        # Process the files
        result = process_join_files(files, app.config['UPLOAD_FOLDER'])
        
        # Ensure all values in the result are JSON-serializable (no NaN values)
        import numpy as np
        import pandas as pd
        import json
        
        # Custom JSON encoder to handle NaN values
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return None if np.isnan(obj) else float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if pd.isna(obj):
                    return None
                return super(NpEncoder, self).default(obj)
        
        # Convert the result to JSON with special handling for NaN
        json_result = json.dumps(result, cls=NpEncoder)
        
        # Return the processed result
        return app.response_class(
            response=json_result,
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Exception in process_join: {str(e)}")
        print(error_trace)
        
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
    
@app.route('/get-calculation-options', methods=['POST'])
def get_calculation_options():
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
            # You might want to do some validation on the file here
            # For now, just return success with the filename
            return jsonify({
                'success': True,
                'filename': filename,
                'message': 'File uploaded successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Invalid file type'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)