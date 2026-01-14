"""
Data Loader para el Monitor de Economía Real
Obtiene datos de Eurostat e INE utilizando la librería eurostat
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import eurostat


@st.cache_data(ttl=3600)
def fetch_ine_data(serie_code, nult=40):
    """Obtiene datos del INE (Instituto Nacional de Estadística)"""
    if not serie_code:
        return pd.DataFrame()
    url = f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie_code}?nult={nult}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'Data' in data:
            df = pd.DataFrame(data['Data'])
            df['date'] = pd.to_datetime(df['Fecha'], unit='ms')
            df['value'] = df['Valor']
            return df[['date', 'value']].sort_values('date')
    except Exception:
        pass
    return pd.DataFrame()


def _find_geo_column(df):
    """
    Encuentra la columna geográfica en un DataFrame de Eurostat.
    La columna puede llamarse 'geo', 'geo\\time_period', 'geo/time', etc.
    """
    for col in df.columns:
        col_lower = col.lower()
        if col_lower == 'geo' or col_lower.startswith('geo\\') or col_lower.startswith('geo/'):
            return col
    return None


def _parse_eurostat_date(x):
    """
    Parsea fechas de Eurostat que pueden venir en formatos:
    - '2024-Q1' (trimestral)
    - '2024-M01' o '2024M01' (mensual)
    - '2024' (anual)
    """
    x = str(x).strip().upper()
    try:
        if '-Q' in x or 'Q' in x:
            # Formato trimestral: 2024-Q1 o 2024Q1
            x_clean = x.replace('-Q', 'Q')
            parts = x_clean.split('Q')
            year = int(parts[0])
            quarter = int(parts[1])
            month = quarter * 3
            return pd.Timestamp(year=year, month=month, day=1)
        elif '-M' in x or 'M' in x:
            # Formato mensual: 2024-M01 o 2024M01
            x_clean = x.replace('-M', 'M').replace('M', '-')
            return pd.to_datetime(x_clean, format='%Y-%m')
        elif len(x) == 4 and x.isdigit():
            # Formato anual: 2024
            return pd.to_datetime(x, format='%Y')
        else:
            # Intentar parseo genérico
            return pd.to_datetime(x)
    except Exception:
        return pd.NaT


@st.cache_data(ttl=3600)
def fetch_eurostat_data(dataset_code, filters=None):
    """
    Obtiene datos de Eurostat usando la librería eurostat.
    
    Args:
        dataset_code: Código del dataset (ej: 'namq_10_gdp')
        filters: Diccionario con filtros (ej: {'unit': 'CLV_I10', 'geo': 'ES'})
    
    Returns:
        DataFrame con columnas ['date', 'value']
    """
    try:
        # 1. Descargar dataset completo
        df = eurostat.get_data_df(dataset_code)
        
        if df is None or df.empty:
            return pd.DataFrame()

        # 2. Normalizar nombres de columnas a minúsculas
        df.columns = [c.lower() for c in df.columns]
        
        # 3. Detectar columna geo (puede ser 'geo', 'geo\\time_period', etc.)
        geo_col = _find_geo_column(df)
        
        # 4. Aplicar filtros
        if filters:
            for filter_col, filter_val in filters.items():
                filter_col_lower = filter_col.lower()
                
                # Manejo especial para 'geo'
                if filter_col_lower == 'geo':
                    if geo_col:
                        df = df[df[geo_col] == filter_val]
                elif filter_col_lower in df.columns:
                    df = df[df[filter_col_lower] == filter_val]
        else:
            # Si no hay filtros, usar España por defecto
            if geo_col:
                df = df[df[geo_col] == 'ES']
        
        if df.empty:
            return pd.DataFrame()
        
        # 5. Identificar columnas de datos (las que son fechas, empiezan con dígito)
        id_cols = []
        date_cols = []
        for col in df.columns:
            # Las columnas de fechas suelen empezar con un número (año)
            if col[0].isdigit():
                date_cols.append(col)
            else:
                id_cols.append(col)
        
        if not date_cols:
            return pd.DataFrame()
        
        # 6. Melt: transformar de formato ancho a largo
        df_melted = df.melt(id_vars=id_cols, var_name='period', value_name='value')
        
        # 7. Limpiar valores
        df_melted['value'] = pd.to_numeric(df_melted['value'], errors='coerce')
        
        # 8. Parsear fechas
        df_melted['date'] = df_melted['period'].apply(_parse_eurostat_date)
        
        # 9. Filtrar y ordenar
        result = df_melted[['date', 'value']].dropna().sort_values('date')
        
        # 10. CRÍTICO: Agregar por fecha para evitar duplicados (múltiples filas por fecha causan bandas en gráficas)
        result = result.groupby('date')['value'].mean().reset_index()
        
        # 11. Filtrar datos desde año 2000 (evitar histórico muy antiguo)
        result = result[result['date'] >= '2000-01-01']
        
        return result.reset_index(drop=True)

    except Exception as e:
        # Log silencioso - en producción podría loguearse
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_eurostat_multi_country(dataset_code, countries, filters=None):
    """
    Obtiene datos de Eurostat para múltiples países.
    
    Args:
        dataset_code: Código del dataset
        countries: Lista de códigos de país (ej: ['ES', 'DE', 'FR'])
        filters: Filtros adicionales (sin 'geo')
    
    Returns:
        Dict con {country_code: DataFrame}
    """
    try:
        # 1. Descargar dataset completo (una sola vez)
        df = eurostat.get_data_df(dataset_code)
        
        if df is None or df.empty:
            return {c: pd.DataFrame() for c in countries}

        # 2. Normalizar columnas
        df.columns = [c.lower() for c in df.columns]
        
        # 3. Detectar columna geo
        geo_col = _find_geo_column(df)
        if not geo_col:
            return {c: pd.DataFrame() for c in countries}
        
        # 4. Aplicar filtros que no sean geo
        if filters:
            for filter_col, filter_val in filters.items():
                filter_col_lower = filter_col.lower()
                if filter_col_lower != 'geo' and filter_col_lower in df.columns:
                    df = df[df[filter_col_lower] == filter_val]
        
        # 5. Identificar columnas de datos
        id_cols = []
        date_cols = []
        for col in df.columns:
            if col[0].isdigit():
                date_cols.append(col)
            else:
                id_cols.append(col)
        
        if not date_cols:
            return {c: pd.DataFrame() for c in countries}
        
        # 6. Procesar cada país
        results = {}
        for country in countries:
            df_country = df[df[geo_col] == country]
            
            if df_country.empty:
                results[country] = pd.DataFrame()
                continue
            
            # Melt
            df_melted = df_country.melt(id_vars=id_cols, var_name='period', value_name='value')
            df_melted['value'] = pd.to_numeric(df_melted['value'], errors='coerce')
            df_melted['date'] = df_melted['period'].apply(_parse_eurostat_date)
            
            result = df_melted[['date', 'value']].dropna().sort_values('date')
            
            # Agregar por fecha para evitar duplicados
            result = result.groupby('date')['value'].mean().reset_index()
            
            # Filtrar desde 2000
            result = result[result['date'] >= '2000-01-01']
            
            results[country] = result.reset_index(drop=True)
        
        return results

    except Exception as e:
        return {c: pd.DataFrame() for c in countries}


def fetch_esios_data(token, indicators):
    """Placeholder para datos de ESIOS (Red Eléctrica)"""
    return pd.DataFrame()
