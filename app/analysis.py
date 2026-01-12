import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from .utils import ICTR_BASE, ICTR_SCALE, PCA_COMPONENTS

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
    # 1. Align all series to a common monthly frequency
    # Upsample quarterly data to monthly if necessary
    
    series_list = []
    for name, df in indicators_dict.items():
        if df.empty:
            continue
        
        df = df.set_index('date').sort_index()
        # Resample to month end
        df_monthly = df.resample('M').last() 
        # Interpolate linear for quarterly->monthly conversion or just ffill
        df_monthly = df_monthly.interpolate(method='linear')
        
        # Calculate YoY growth (assuming monthly after resampling)
        # Note: If the original data was already a rate (like unemployment), 
        # we might handle it differently (diff instead of log-diff), but for ICTR usually we want changes.
        # Let's apply log-diff to everything for simplicity in this V1 as per general PDF instructions
        
        # Use diff(12) for YoY
        df_growth = np.log(df_monthly['value']).diff(12).rename(name)
        series_list.append(df_growth)
        
    if not series_list:
        return None, None
        
    # Combine into one DataFrame
    df_combined = pd.concat(series_list, axis=1).dropna()
    
    if df_combined.empty:
        return None, None
        
    # 2. Standardize
    df_scaled, scaler = standardize_data(df_combined)
    
    # 3. PCA
    pca_data, explained_var, pca_model = run_pca(df_scaled)
    
    # 4. Scale to ICTR (Mean 100, SD 10)
    # The PCA output is typically Mean 0, Var 1 (roughly)
    # We want to map it to 100 +/- 10
    ictr_series = (pca_data[:, 0] * ICTR_SCALE) + ICTR_BASE
    
    result_df = pd.DataFrame(ictr_series, index=df_combined.index, columns=['ICTR'])
    
    return result_df, explained_var
