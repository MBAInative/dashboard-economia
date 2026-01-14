import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from utils import ICTR_BASE, ICTR_SCALE, PCA_COMPONENTS

def calculate_yoy_growth(df, period_freq=12):
    """
    Calculates Year-over-Year growth or log-diff.
    df: DataFrame with 'date' and 'value'.
    period_freq: 12 for monthly, 4 for quarterly.
    """
    df = df.sort_values('date').set_index('date')
    # Log difference approximation for growth: ln(Xt) - ln(Xt-12)
    df['log_val'] = np.log(df['value'])
    df['growth'] = df['log_val'].diff(period_freq)
    return df[['growth']].dropna()

def standardize_data(df):
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)
    return pd.DataFrame(scaled_data, index=df.index, columns=df.columns), scaler

def run_pca(df_scaled):
    """
    Runs PCA on the scaled dataframe.
    """
    # Impute missing values if any (Simple forward fill or mean)
    # Since it's time series, ffill is better, but sklearn Imputer is column-wise mean/median usually
    # Let's use pandas ffill before calling this function usually, but as safety:
    df_filled = df_scaled.ffill().bfill() # Simple time-series imputation
    
    pca = PCA(n_components=PCA_COMPONENTS)
    principal_components = pca.fit_transform(df_filled)
    
    # Check polarity: The component should correlate positively with GDP/Growth.
    # We might need to flip the sign if the correlation with the average of inputs is negative
    # (assuming most inputs are pro-cyclical).
    
    # Simple polarity check: correlation with the mean of the variables
    mean_series = df_filled.mean(axis=1)
    pc1 = principal_components[:, 0]
    if np.corrcoef(mean_series, pc1)[0, 1] < 0:
        principal_components = -principal_components
        
    explained_variance = pca.explained_variance_ratio_
    
    return principal_components, explained_variance, pca

def calculate_ictr(indicators_dict):
    """
    Main function to compute ICTR.
    indicators_dict: { 'IndicatorName': DataFrame(date, value) }
    """
    series_list = []
    
    # 1. Process each indicator
    for name, df in indicators_dict.items():
        if df is None or df.empty:
            continue
            
        try:
            df = df.copy()
            if 'date' in df.columns:
                df = df.set_index('date').sort_index()
            
            # Resample to month end
            df_monthly = df.resample('M').last() 
            # Interpolate linear for quarterly->monthly conversion
            df_monthly = df_monthly.interpolate(method='linear')
            
            # Calculate Log Growth (YoY)
            # Use diff(12) for YoY
            # Safety: Ensure values are positive for Log. If not (e.g. Sentiment balance), use simple pct_change or diff.
            # Heuristic: If min value <= 0, assume it's a balance or rate where log isn't appropriate or requires shifting.
            # For simplicity in this robust version, we'll try log, and if it creates infs, we handle them.
            
            vals = df_monthly['value']
            if (vals <= 0).any():
                # If negative/zero values exist (like Sentiment), use absolute difference instead of log-diff approximation
                df_growth = vals.diff(12).rename(name)
            else:
                df_growth = np.log(vals).diff(12).rename(name)
                
            series_list.append(df_growth)
        except Exception:
            continue
        
    if not series_list:
        return None, None
        
    # Combine into one DataFrame using Outer Join to keep max history
    df_combined = pd.concat(series_list, axis=1)
    
    # CRITICAL FIX: Replace infinities with NaN before dropping
    df_combined = df_combined.replace([np.inf, -np.inf], np.nan)
    
    # 1. Drop rows that are completely empty
    df_combined = df_combined.dropna(how='all')
    
    # 2. Drop rows with any NaN (Strict PCA requirement)
    df_clean = df_combined.dropna()
    
    if df_clean.empty or len(df_clean) < 12: # Need at least some history
        # Fallback: Try filling NaNs if overlap is slight issue
        df_clean = df_combined.ffill().bfill().dropna()
        if df_clean.empty:
            return None, None
        
    # 2. Standardize
    df_scaled, scaler = standardize_data(df_clean)
    
    # 3. PCA
    try:
        pca_data, explained_var, pca_model = run_pca(df_scaled)
        
        # 4. Scale to ICTR (Mean 100, SD 10)
        ictr_series = (pca_data[:, 0] * ICTR_SCALE) + ICTR_BASE
        
        result_df = pd.DataFrame(ictr_series, index=df_clean.index, columns=['ICTR'])
        
        return result_df, explained_var
    except Exception:
        return None, None
