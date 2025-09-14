# Create Authentication views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
import os, pandas as pd, numpy as np
from django.http import HttpResponse
from .forms import UploadFileForm  # Import the UploadFileForm from forms.py
from .privacy_utils import anonymize_data
from .viz_utils import compare_datasets

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Auth
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('upload')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# File Upload and Analytics
@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            filepath = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(filepath, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            request.session['uploaded_file_path'] = filepath
            return redirect('dashboard')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

# Dashboard View: # integrate the privacy utils here
@login_required
def dashboard(request):
    filepath = request.session.get('uploaded_file_path')
    if not filepath or not os.path.exists(filepath):
        return redirect('upload')
    
    # Read dataset
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return HttpResponse(f"Error reading uploaded file. Ensure it's a valid CSV.")
    
    # Anonymize dataset
    anonymized_df = anonymize_data(df, epsilon=1.0)

    # Show only top 10 rows for preview
    preview = anonymized_df.head(10).to_html(classes='table table-bordered', index=False)

    return render(request, 'dashboard.html', 
                  {
                        'file': filepath, 
                        'table': preview
                   })

# Visualization and Comparison View
@login_required
def visualize(request):
    filepath = request.session.get('uploaded_file_path')
    if not filepath or not os.path.exists(filepath):
        return redirect('upload')
    
    # Read dataset
    try:
        # Try to determine if the file is CSV, Excel, etc.
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath)
        else:
            # Default to CSV if unsure
            df = pd.read_csv(filepath)
            
        # Basic data cleaning
        # Fill missing values in numeric columns with mean, in categorical with most frequent
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown")
                
    except Exception as e:
        return render(request, 'visualize.html', {
            'viz': {
                'error': f"Error reading the dataset: {str(e)}",
                'orig_stats': "",
                'anon_stats': "",
                'orig_plots': [],
                'anon_plots': [],
                'anonymized_df': ""
            }
        })
    
    # Generate comparison stats and plots
    try:
        comparison = compare_datasets(df, epsilon=1.0)
        return render(request, 'visualize.html', {'viz': comparison})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return render(request, 'visualize.html', {
            'viz': {
                'error': f"Error generating visualizations: {str(e)}",
                'details': error_details,
                'orig_stats': df.describe().to_html(classes="table table-bordered") if 'df' in locals() else "",
                'anon_stats': "",
                'orig_plots': [],
                'anon_plots': [],
                'anonymized_df': ""
            }
        })