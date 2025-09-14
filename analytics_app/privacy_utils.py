"""
Privacy utilities for anonymizing uploaded datasets.
Provides:
1. remove_pii: Function to remove personally identifiable information (PII) from a DataFrame.
2. adding_noise: Function to add Gaussian noise to numerical columns for differential privacy.
3. generalizing_categorical: Function to generalize categorical data into broader categories.
"""
import pandas as pd
import numpy as np

# List of common PII columns to remove
DIRECT_IDENTIFIERS = ['name', 'email', 'phone', 'address', 'ssn', 'dob', 'rollno', 'mobile', 'id', 'user_id', 'student_id']

def group_rare_values(x, rare_list):
    """Helper function to group rare values"""
    return "Other" if x in rare_list else x

def anonymize_data(df: pd.DataFrame, epsilon: float = 1.0) -> pd.DataFrame:
    """
    Anonymizes the given DataFrame by removing PII, adding noise to numerical data,
    and generalizing categorical data.
    
    Parameters:
    df (pd.DataFrame): The input DataFrame to be anonymized.
    epsilon (float): Privacy parameter controlling the privacy-utility tradeoff.
                     Lower values provide stronger privacy but more noise.
                     Default is 1.0, which is a moderate level of privacy.
    
    Returns:
    pd.DataFrame: The anonymized DataFrame.
    """
    df = df.copy()

    # Drop direct identifiers if present
    for col in df.columns:
        if any(identifier in col.lower() for identifier in DIRECT_IDENTIFIERS):
            df.drop(col, axis=1, inplace=True)
            print(f"Dropped column: {col} as it may contain personal identifiers")

    # Add noise to numerical columns
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    for col in numeric_cols:
        # Calculate column-specific scale for noise based on data range and epsilon
        data_range = df[col].max() - df[col].min()
        # Scale noise based on data range and epsilon
        # Higher epsilon = less noise, lower epsilon = more noise
        scale = data_range * (0.1 / epsilon)
        
        # Generate noise with appropriate scale
        noise = np.random.laplace(0, scale, size=len(df))
        
        # Add noise to the column
        df[col] = df[col] + noise
        
        # Round to reasonable precision to avoid exposing exact noise values
        # Number of decimal places depends on the scale of the data
        if df[col].dtype == 'int64':
            df[col] = df[col].round().astype('int64')
        else:
            # For float columns, determine appropriate rounding
            magnitude = np.log10(abs(df[col].mean())) if df[col].mean() != 0 else 0
            decimals = max(2, int(4 - magnitude))  # More decimals for smaller numbers
            df[col] = df[col].round(decimals)

    # Generalize categorical columns
    for col in df.select_dtypes(include=["object", "category"]).columns:
        # Skip columns with too many unique values (likely not good candidates for generalization)
        if df[col].nunique() > 20:
            continue
            
        if "rank" in col.lower():
            # Create quantile-based categories for rank columns
            df[col] = pd.qcut(df[col].rank(method='first'), q=5, 
                              labels=["Top 20%", "20-40%", "40-60%", "60-80%", "Bottom 20%"])
        elif df[col].nunique() <= 10:
            # For low-cardinality categorical columns, apply k-anonymity
            # by grouping rare categories together
            value_counts = df[col].value_counts()
            rare_values = value_counts[value_counts < len(df) * 0.05].index.tolist()
            
            if rare_values:
                # Using numpy's where is more efficient than apply with lambda
                df[col] = np.where(df[col].isin(rare_values), "Other", df[col])
    
    return df