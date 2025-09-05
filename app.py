# Flask app with Upload functionality
from flask import Flask, render_template, request, redirect
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['dataset']
        # checks if a file was uploaded and if its filename ends with .csv
        # if both are true saves the file to the UPLOAD_FOLDER
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(UPLOAD_FOLDER, "uploaded.csv")
            file.save(filepath)
            return redirect('/dashboard')
        else:
            return "Please upload a CSV file."
        
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    filepath = os.path.join(UPLOAD_FOLDER, "uploaded.csv")
    if not os.path.exists(filepath):
        return redirect('/')
    df = pd.read_csv(filepath)
    return render_template('dashboard.html', tables=[df.head().to_html(classes="data")], titles=df.columns.values)

if __name__ == '__main__':
    app.run(debug=True)