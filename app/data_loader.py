"""
Data Loader para el Monitor de EconomÃ­a Real
Obtiene datos de Eurostat e INE utilizando la librerÃ­a eurostat
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import eurostat


@st.cache_data(ttl=86400)
def fetch_ine_data(serie_code, nult=40):
    """Obtiene datos del INE (Instituto Nacional de EstadÃ­stica)"""
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
    Encuentra la columna geogrÃ¡fica en un DataFrame de Eurostat.
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
            # Intentar parseo genÃ©rico
            return pd.to_datetime(x)
    except Exception:
        return pd.NaT


@st.cache_data(ttl=86400)
def fetch_eurostat_data(dataset_code, filters=None):
    """
    Obtiene datos de Eurostat usando la librerÃ­a eurostat.
    
    Args:
        dataset_code: CÃ³digo del dataset (ej: 'namq_10_gdp')
        filters: Diccionario con filtros (ej: {'unit': 'CLV_I10', 'geo': 'ES'})
    
    Returns:
        DataFrame con columnas ['date', 'value']
    """
    try:
        # 1. Descargar dataset completo
        df = eurostat.get_data_df(dataset_code)
        
        if df is None or df.empty:
            return pd.DataFrame()

        # 2. Normalizar nombres de columnas a minÃºsculas
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
            # Si no hay filtros, usar EspaÃ±a por defecto
            if geo_col:
                df = df[df[geo_col] == 'ES']
        
        if df.empty:
            return pd.DataFrame()
        
        # 5. Identificar columnas de datos (las que son fechas, empiezan con dÃ­gito)
        id_cols = []
        date_cols = []
        for col in df.columns:
            # Las columnas de fechas suelen empezar con un nÃºmero (aÃ±o)
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
        
        # 10. CRÃTICO: Agregar por fecha para evitar duplicados (mÃºltiples filas por fecha causan bandas en grÃ¡ficas)
        result = result.groupby('date')['value'].mean().reset_index()
        
        # 11. Filtrar datos desde aÃ±o 2000 (evitar histÃ³rico muy antiguo)
        result = result[result['date'] >= '2000-01-01']
        
        return result.reset_index(drop=True)

    except Exception as e:
        # Log silencioso - en producciÃ³n podrÃ­a loguearse
        return pd.DataFrame()


@st.cache_data(ttl=86400)
def fetch_eurostat_multi_country(dataset_code, countries, filters=None):
    """
    Obtiene datos de Eurostat para mÃºltiples paÃ­ses.
    
    Args:
        dataset_code: CÃ³digo del dataset
        countries: Lista de cÃ³digos de paÃ­s (ej: ['ES', 'DE', 'FR'])
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
        
        # 6. Procesar cada paÃ­s
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


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_esios_data_v6(token):
    """
    Obtiene datos de demanda eléctrica real de la API de ESIOS (Red Eléctrica).
    Indicador 1293: Demanda real (MW)
    Versión 6: CHUNKS MENSUALES + RETIES.
    Para máxima fiabilidad, bajamos bloques de 1 mes (payload ligero) y reintentamos si falla.
    """
    if not token:
        return pd.DataFrame()
    
    all_dfs = []
    end_year = datetime.now().year
    start_year = 2000
    
    import time

    # Generar rangos MENSUALES para evitar Timeouts
    # 26 años * 12 meses = ~300 peticiones.
    ranges = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Cuidado con fecha futura
            if year == end_year and month > datetime.now().month:
                break
                
            # Fin de mes
            last_day = pd.Period(f"{year}-{month}").days_in_month
            s_str = f"{year}-{month:02d}-01T00:00:00"
            e_str = f"{year}-{month:02d}-{last_day}T23:59:59"
            ranges.append((s_str, e_str))
            
    total_steps = len(ranges)
    progress_text = "Descargando histórico ESIOS (Mes a Mes)... Esta operación puede tardar 1-2 minutos."
    my_bar = st.progress(0, text=progress_text)

    for i, (s_str, e_str) in enumerate(ranges):
        # Actualizar barra cada 5 pasos para no saturar UI
        if i % 5 == 0 or i == total_steps - 1:
            my_bar.progress((i + 1) / total_steps, text=f"Descargando {s_str[:7]}... ({i+1}/{total_steps})")
        
        url = f"https://api.esios.ree.es/indicators/1293?start_date={s_str}&end_date={e_str}" # Sin time_trunc (Raw)
        
        headers = {
            'Accept': 'application/json; application/vnd.esios-api-v1+json',
            'Content-Type': 'application/json',
            'x-api-key': token,
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" 
        }
        
        # RETRY LOGIC
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                # Timeout 10s suficiente para 1 mes
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'indicator' in data and 'values' in data['indicator']:
                        chunk = pd.DataFrame(data['indicator']['values'])
                        if not chunk.empty:
                            chunk['date'] = pd.to_datetime(chunk['datetime'], utc=True, errors='coerce')
                            chunk = chunk.dropna(subset=['date'])
                            chunk['date'] = chunk['date'].dt.tz_localize(None)
                            chunk['value'] = pd.to_numeric(chunk['value'], errors='coerce')
                            all_dfs.append(chunk[['date', 'value']])
                    success = True
                    break # Éxito, salir del retry loop
                
                elif response.status_code == 403:
                    print(f"Bloqueo 403 en {s_str}.") 
                    # No retry on 403 usually (blocked), but maybe temporary? break to be safe
                    break
                elif response.status_code == 429: # Rate limit
                    time.sleep(2) # Esperar más
                    
            except Exception as e:
                print(f"Error {e} en {s_str}. Retry {attempt+1}/{max_retries}")
                time.sleep(1)
        
        if not success:
            print(f"Fallo definitivo en chunk {s_str}")
            
        time.sleep(0.05) # Pausa muy breve ya que hacemos muchas peticiones pequeñas

    my_bar.empty()

    if all_dfs:
        full_raw = pd.concat(all_dfs).drop_duplicates(subset=['date']).sort_values('date')
        full_daily = full_raw.set_index('date').resample('D')['value'].mean().reset_index()
        return full_daily
    
    return pd.DataFrame()

