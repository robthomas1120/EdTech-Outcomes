from flask import Blueprint, request, jsonify, render_template, send_file
import pandas as pd
import json
import traceback
import os
from io import BytesIO
import numpy as np

# Create blueprint with url_prefix
mapping_bp = Blueprint('mapping', __name__, url_prefix='/mapping')

@mapping_bp.route('/')
def mapping_page():
    """Render the mapping page."""
    return render_template('mapping.html')

@mapping_bp.route('/api/get-columns', methods=['POST'])
def get_columns():
    """Get available columns from the uploaded mapping template."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Read the file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            return jsonify({'success': False, 'error': 'Invalid file format'})
            
        # Process the mapping template to create one-to-one mappings
        processed_data = []
        
        for _, row in df.iterrows():
            course_outcomes = str(row['Course Outcomes']).strip()
            
            # Process each mapping type
            for col in ['Institutional Outcomes', 'SEAL of THOMASIAN EDUCATION', 'Program Outcomes']:
                if col in df.columns:
                    outcomes = str(row[col]).strip()
                    if outcomes.lower() != 'nan' and outcomes:
                        # Split multiple outcomes if they exist
                        individual_outcomes = [o.strip() for o in outcomes.split(',')]
                        for outcome in individual_outcomes:
                            if outcome:  # Only add non-empty outcomes
                                processed_data.append({
                                    'Course Outcomes': course_outcomes,
                                    col: outcome
                                })
        
        # Create processed DataFrame
        processed_df = pd.DataFrame(processed_data)
        
        # Store the processed mapping template
        processed_df.to_csv('temp_mapping_template.csv', index=False)
        
        return jsonify({
            'success': True,
            'columns': processed_df.columns.tolist()
        })
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@mapping_bp.route('/api/process-mapping', methods=['POST'])
def process_mapping():
    """Process the mapping between the template and outcomes file."""
    try:
        if 'mapping_template' not in request.files or 'outcomes_file' not in request.files:
            return jsonify({'success': False, 'error': 'Missing required files'})
        
        mapping_type = request.form.get('mapping_type')
        if not mapping_type:
            return jsonify({'success': False, 'error': 'Missing mapping type'})
        
        # Read the mapping template
        mapping_template = request.files['mapping_template']
        if mapping_template.filename.endswith('.csv'):
            template_df = pd.read_csv(mapping_template)
        else:
            template_df = pd.read_excel(mapping_template)
            
        # Process the mapping template to create one-to-one mappings
        processed_data = []
        for _, row in template_df.iterrows():
            course_outcomes = str(row['Course Outcomes']).strip()
            outcomes = str(row[mapping_type]).strip()
            if outcomes.lower() != 'nan' and outcomes:
                # Split multiple outcomes if they exist
                individual_outcomes = [o.strip() for o in outcomes.split(',')]
                for outcome in individual_outcomes:
                    if outcome:  # Only add non-empty outcomes
                        processed_data.append({
                            'Course Outcomes': course_outcomes,
                            mapping_type: outcome
                        })
        
        # Create processed template DataFrame
        template_df = pd.DataFrame(processed_data)
            
        # Read the outcomes file
        outcomes_file = request.files['outcomes_file']
        if outcomes_file.filename.endswith('.csv'):
            outcomes_df = pd.read_csv(outcomes_file)
        else:
            outcomes_df = pd.read_excel(outcomes_file)
            
        # Create mapping dictionary from processed template
        mapping_dict = {}
        for _, row in template_df.iterrows():
            course_outcome = str(row['Course Outcomes']).strip()
            mapped_outcome = str(row[mapping_type]).strip()
            if course_outcome and mapped_outcome and mapped_outcome.lower() != 'nan':
                mapping_dict[course_outcome] = mapped_outcome
        
        # Find the position of 'learning outcome name' column
        try:
            learning_outcome_pos = outcomes_df.columns.get_loc('learning outcome name')
            # Add new column before 'learning outcome name'
            outcomes_df.insert(learning_outcome_pos, mapping_type, '')
        except KeyError:
            # If column not found, try with original case
            try:
                learning_outcome_pos = outcomes_df.columns.get_loc('Learning Outcome Name')
                outcomes_df.insert(learning_outcome_pos, mapping_type, '')
            except KeyError:
                return jsonify({'success': False, 'error': 'Learning Outcome Name column not found in outcomes file'})
        
        # Map the outcomes
        for idx, row in outcomes_df.iterrows():
            try:
                course_outcome = str(row['learning outcome name']).strip()
                if course_outcome in mapping_dict:
                    outcomes_df.at[idx, mapping_type] = mapping_dict[course_outcome]
            except KeyError:
                try:
                    course_outcome = str(row['Learning Outcome Name']).strip()
                    if course_outcome in mapping_dict:
                        outcomes_df.at[idx, mapping_type] = mapping_dict[course_outcome]
                except KeyError:
                    print(f"Warning: Learning outcome name column not found in row {idx}")
                    continue
        
        # Store the results for download
        outcomes_df.to_csv('temp_mapping_results.csv', index=False)
        
        # Convert results to list of dictionaries for display
        # Handle NaN values by converting them to empty strings and show more preview rows
        results = outcomes_df.head(20).replace({np.nan: '', float('nan'): ''}).to_dict('records')
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@mapping_bp.route('/api/download-results', methods=['GET'])
def download_results():
    """Download the mapped results."""
    try:
        return send_file(
            'temp_mapping_results.csv',
            mimetype='text/csv',
            as_attachment=True,
            download_name='mapped_outcomes.csv'
        )
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})