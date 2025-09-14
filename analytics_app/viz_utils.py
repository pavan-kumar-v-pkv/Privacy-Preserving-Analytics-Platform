"""
Visualization utilities for original vs anonymized data comparison.
Generates plots and summary statistics to visualize the impact of anonymization.
"""
import pandas as pd
import matplotlib
# Configure matplotlib to use a non-interactive backend (Agg) to avoid thread-related crashes
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid
from django.conf import settings

from .privacy_utils import anonymize_data

# Define media directory for plots
MEDIA_DIR = os.path.join(settings.MEDIA_ROOT, 'plots')
os.makedirs(MEDIA_DIR, exist_ok=True)

def generate_basic_stats(df: pd.DataFrame):
    """Return summary statistics of the DataFrame as HTML (to render in template)"""
    try:
        # For mixed data types, only include numeric columns in describe
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) > 0:
            return numeric_df.describe().transpose().to_html(classes="table table-striped")
        else:
            # If no numeric columns, return basic info
            return pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes,
                'Non-Null Count': df.count(),
                'Null Count': df.isna().sum()
            }).to_html(classes="table table-striped")
    except Exception as e:
        return f"<div class='alert alert-warning'>Error generating statistics: {str(e)}</div>"

def generate_plots(df: pd.DataFrame, prefix="orig"):
    """Generate histograms & correlation heatmaps. Save images and return file paths."""
    plot_paths = []

    # First ensure dataframe has consistent types - convert to numeric where possible
    # but ignore errors (will leave non-convertible values as NaN)
    df_clean = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Try to convert to numeric, but set errors='coerce' to turn strings into NaN
                df_clean[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                # If conversion fails completely, just keep as is
                pass
    
    # Histogram of all numerical columns
    for col in df_clean.select_dtypes(include="number").columns[:3]: # Limit to first 3 numeric columns for brevity
        # Skip columns with too many NaN values
        if df_clean[col].isna().sum() > 0.5 * len(df_clean):
            continue
            
        filename = f"{prefix}_hist_{col}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(MEDIA_DIR, filename)
        plt.figure(figsize=(6,4))
        sns.histplot(df_clean[col].dropna(), kde=True)
        plt.title(f'Distribution of {col} ({prefix})')
        plt.savefig(filepath)
        plt.close()
        
        # Return URL path for the template to use
        url_path = f"{settings.MEDIA_URL}plots/{filename}"
        plot_paths.append(url_path)

    # Correlation heatmap
    numeric_cols = df_clean.select_dtypes(include="number").columns
    if len(numeric_cols) >= 2:  # Need at least 2 columns for correlation
        # Filter out columns with too many NaN values
        valid_cols = [col for col in numeric_cols if df_clean[col].isna().sum() <= 0.5 * len(df_clean)]
        
        if len(valid_cols) >= 2:  # Still need at least 2 valid columns
            filename = f"{prefix}_corr_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(MEDIA_DIR, filename)
            plt.figure(figsize=(8,6))
            corr = df_clean[valid_cols].corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', cbar=True)
            plt.title(f'Correlation Matrix ({prefix})')
            plt.savefig(filepath)
            plt.close()
            
            # Return URL path for the template to use
            url_path = f"{settings.MEDIA_URL}plots/{filename}"
            plot_paths.append(url_path)

    return plot_paths

def compare_datasets(orig_df: pd.DataFrame, epsilon: float = 1.0):
    """Anonymize the original DataFrame and generate comparison stats and plots."""
    try:
        # Make a copy to avoid modifying the original dataframe
        df = orig_df.copy()
        
        # Apply anonymization
        anon_df = anonymize_data(df, epsilon=epsilon)
        
        # Generate statistics
        orig_stats = generate_basic_stats(df)
        anon_stats = generate_basic_stats(anon_df)
        
        # Generate plots
        orig_plots = generate_plots(df, prefix="orig")
        anon_plots = generate_plots(anon_df, prefix="anon")
        
        return {
            "orig_stats": orig_stats,
            "anon_stats": anon_stats,
            "orig_plots": orig_plots,
            "anon_plots": anon_plots,
            "anonymized_df": anon_df.head().to_html(classes="table table-bordered")  # Show sample of anonymized data
        }
    except Exception as e:
        # If any error occurs, return a simple error message
        import traceback
        error_details = traceback.format_exc()
        return {
            "error": f"Error generating visualizations: {str(e)}",
            "details": error_details,
            "orig_stats": df.describe().to_html(classes="table table-bordered") if 'df' in locals() else "",
            "anon_stats": "",
            "orig_plots": [],
            "anon_plots": [],
            "anonymized_df": ""
        }