# Create Authentication views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
import os, pandas as pd, numpy as np
from django.http import HttpResponse
from .forms import UploadFileForm  # Import the UploadFileForm from forms.py
from .privacy_utils import anonymize_data

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


