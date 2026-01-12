import requests
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

# Base URLs
INE_BASE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/"
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

@st.cache_data(ttl=3600)
def fetch_ine_data(serie_code, nult=24):
    """
    Fetches data from INE API (JSON-stat format simplified).
    """
    url = f"{INE_BASE_URL}{serie_code}?nult={nult}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # INE returns a dictionary with 'Data' list usually
        if 'Data' in data:
            df = pd.DataFrame(data['Data'])
            # 'Fecha' is usually a timestamp or distinct fields
            # Depending on series, we might need to parse 'Anyo' and 'Periodo'
            # Let's simplify assuming standard INE response structure for series
            df['date'] = pd.to_datetime(df['Fecha'], unit='ms')
            df['value'] = df['Valor']
            return df[['date', 'value']].sort_values('date')
        elif isinstance(data, list) and len(data) > 0 and 'Data' in data[0]:
             # Sometimes it returns a list of series
            df = pd.DataFrame(data[0]['Data'])
            df['date'] = pd.to_datetime(df['Fecha'], unit='ms')
            df['value'] = df['Valor']
            return df[['date', 'value']].sort_values('date')
            
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching INE data {serie_code}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_eurostat_data(dataset_code, params=None):
    """
    Fetches data from Eurostat API (JSON-stat).
    This is a simplified fetcher.
    """
    # Using the wds legacy or new dissemination API. 
    # Let's try the direct JSON-stat URL often used
    url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset_code}?format=JSON&lang=en"
    
    # Add filters if params are provided (simple implementation)
    # Real Eurostat filtering is complex via URL in this new API, usually post or specific dimension args
    # For now, we fetch the dataset and filter in pandas (not efficient for huge datasets but works for indicators)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Parsing JSON-stat is complex. 
        # Using a specialized library like pyjstat would be better, but let's try a basic manual parse
        # or rely on 'eurostat' library if we installed it.
        # Since we are writing raw requests here to avoid dependency hell if library fails:
        
        # Fallback: Simple dictionary parsing if structure is flat-ish
        # Actually, let's just use the 'value' and 'dimension' keys to reconstruct
        # This is non-trivial without a library. 
        # Let's assume we use the 'eurostat' python library for this one as it's in requirements.
        pass 
    except Exception as e:
        st.error(f"Error fetching Eurostat data {dataset_code}: {e}")
        return pd.DataFrame()

# We will implement a wrapper that uses 'eurostat' library for the actual heavy lifting
import eurostat

@st.cache_data(ttl=3600)
def get_eurostat_dataset(code):
    try:
        df = eurostat.get_data_df(code)
        return df
    except Exception as e:
        st.warning(f"Could not fetch Eurostat data via library: {e}")
        return pd.DataFrame()

def fetch_esios_data(token, indicators):
    """
    Fetches electricity data from ESIOS.
    """
    if not token:
        # Return dummy random data for visualization if no token
        dates = pd.date_range(end=datetime.today(), periods=30, freq='D')
        values = np.random.normal(100, 10, size=30)
        return pd.DataFrame({'date': dates, 'value': values})
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'x-api-key': token
    }
    # Implementation pending valid indicators and endpoint
    return pd.DataFrame()
