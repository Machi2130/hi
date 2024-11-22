from flask import Flask, render_template, request
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class ExcelProcessor:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or 'processed_files'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_excel(self, file_path):
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            df.dropna(how='all', inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.fillna('', inplace=True)
            return df
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compare_excel_files(file1_path, file2_path):
    try:
        processor = ExcelProcessor()
        df1 = processor.process_excel(file1_path)
        df2 = processor.process_excel(file2_path)
        
        all_columns = set(df1.columns).union(set(df2.columns))
        df1 = df1.reindex(columns=all_columns, fill_value="")
        df2 = df2.reindex(columns=all_columns, fill_value="")
        
        df1_str = df1.fillna("").astype(str)
        df2_str = df2.fillna("").astype(str)
        
        differences = []
        max_rows = max(len(df1), len(df2))
        
        for idx in range(max_rows):
            for col in all_columns:
                value1 = df1_str.iloc[idx][col] if idx < len(df1) else ""
                value2 = df2_str.iloc[idx][col] if idx < len(df2) else ""
                
                if value1 != value2:
                    differences.append({
                        'row': idx + 2,
                        'column': col,
                        'file1_value': value1,
                        'file2_value': value2
                    })
        
        return differences, None
    except Exception as e:
        return [], f"Error comparing Excel files: {str(e)}"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', differences=None)

@app.route('/compare', methods=['POST'])
def compare():
    if 'file1' not in request.files or 'file2' not in request.files:
        return render_template('index.html', error='Please upload both files')
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        return render_template('index.html', error='No files selected')
    
    if not (allowed_file(file1.filename) and allowed_file(file2.filename)):
        return render_template('index.html', error='Only Excel files (.xls, .xlsx) are allowed')
    
    file1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
    file2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))
    
    file1.save(file1_path)
    file2.save(file2_path)
    
    differences, error = compare_excel_files(file1_path, file2_path)
    
    os.remove(file1_path)
    os.remove(file2_path)
    
    if error:
        return render_template('index.html', error=error)
    
    return render_template('index.html', differences=differences)

if __name__ == '__main__':
    app.run(debug=True)
