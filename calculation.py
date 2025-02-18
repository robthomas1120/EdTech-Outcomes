from flask import Blueprint, jsonify, request
import pandas as pd
import os
from werkzeug.utils import secure_filename

calculation_bp = Blueprint('calculation', __name__)

def read_csv(filepath):
    """Read CSV file and return DataFrame"""
    return pd.read_csv(filepath)

def get_unique_count(df, column_name):
    """Get count of unique values in a column"""
    return len(df[column_name].unique())

def get_unique_values(df, column_name):
    """Get list of unique values in a column"""
    return df[column_name].unique().tolist()

@calculation_bp.route('/get-calculation-options', methods=['POST'])
def get_calculation_options():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
        
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        df = read_csv(filepath)
        
        columns = df.columns.tolist()
        required_columns = [
            'learning outcome group title',
            'student name',
            'learning outcome name'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            return jsonify({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            })
            
        return jsonify({
            'success': True,
            'filename': filename,
            'columns': columns
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@calculation_bp.route('/calculate-preview', methods=['POST'])
def calculate_preview():
    try:
        data = request.get_json()
        filename = data.get('filename')
        selected_calculations = data.get('calculations', [])
        
        filepath = os.path.join('uploads', filename)
        df = read_csv(filepath)
        
        preview_data = {}
        
        if 'programs' in selected_calculations:
            preview_data['number of programs/departments'] = [get_unique_count(df, 'learning outcome group title')]
            
        if 'students' in selected_calculations:
            preview_data['total students'] = [get_unique_count(df, 'student name')]
            
        if 'cilo_count' in selected_calculations:
            preview_data['number of CILO\'s'] = [get_unique_count(df, 'learning outcome name')]
            
        if 'cilo_names' in selected_calculations:
            preview_data['CILO names'] = get_unique_values(df, 'learning outcome name')
            
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@calculation_bp.route('/append-calculations', methods=['POST'])
def append_calculations():
    try:
        data = request.get_json()
        filename = data.get('filename')
        selected_calculations = data.get('calculations', [])
        
        filepath = os.path.join('uploads', filename)
        df = read_csv(filepath)
        
        # Get the number of rows in the original dataframe
        num_rows = len(df)
        
        # Create empty columns first
        if 'programs' in selected_calculations:
            df['number of programs/departments'] = ''
            df.loc[0, 'number of programs/departments'] = get_unique_count(df, 'learning outcome group title')
            
        if 'students' in selected_calculations:
            df['total students'] = ''
            df.loc[0, 'total students'] = get_unique_count(df, 'student name')
            
        if 'cilo_count' in selected_calculations:
            df['number of CILO\'s'] = ''
            df.loc[0, 'number of CILO\'s'] = get_unique_count(df, 'learning outcome name')
            
        if 'cilo_names' in selected_calculations:
            df['CILO names'] = ''
            cilo_names = get_unique_values(df, 'learning outcome name')
            for idx, cilo in enumerate(cilo_names):
                if idx < num_rows:  # Ensure we don't exceed dataframe bounds
                    df.loc[idx, 'CILO names'] = cilo
        
        # Save updated CSV
        output_filename = f'calculated_{filename}'
        output_filepath = os.path.join('uploads', output_filename)
        df.to_csv(output_filepath, index=False)
        
        return jsonify({
            'success': True,
            'filename': output_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})