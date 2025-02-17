from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
from preprocessing import process_file, read_file, validate_format, fix_program_outcome_format

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)