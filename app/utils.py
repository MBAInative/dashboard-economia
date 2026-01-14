# Mapping of indicators and API configurations based on "Citizen Realism" Methodology
# Focus: Per Capita, Inequality, Real Welfare, International Comparison (Peers)

# INE Indicators (Table IDs / Series Codes)
INE_CONFIG = {
    "GDP": {"id": "CNTR", "operation": "30678", "label": "PIB (Volumen)"}, 
    "IPC_GENERAL": {"id": "IPC", "operation": "251852", "label": "IPC General"},
    "HOURS_WORKED": {"id": "EPA_HOURS", "operation": "30456", "label": "Horas Trabajadas (EPA)"},
    "FORECLOSURES": {"id": "EJECUCIONES", "operation": "25171", "label": "Ejecuciones Hipotecarias"}, 
    "COMPANY_CREATION": {"id": "SOCIEDADES", "operation": "Mercantile", "label": "Constitución Sociedades"},
    "CRIME_LO": {"id": "CRIMINALIDAD", "operation": "Proxy", "label": "Criminalidad (Proxy)"}
}

# Eurostat Indicators (Dataset Codes & Filters)
EUROSTAT_CONFIG = {
    # --- BIENESTAR & DESIGUALDAD ---
    "REAL_GDP_PC": {"code": "sdg_08_10", "filters": {"unit": "CLV20_EUR_HAB", "geo": "ES"}}, 
    "GINI": {"code": "ilc_di12", "filters": {"age": "TOTAL", "geo": "ES"}}, 
    "AROPE": {"code": "ilc_peps01", "filters": {"unit": "PC", "age": "TOTAL", "sex": "T", "geo": "ES"}},
    
    # --- COMPARATIVA INTERNACIONAL ---
    # Usamos CLV_I10 (Índice 2010=100) para comparativa directa de volumen
    "GDP_PEERS": {"code": "namq_10_gdp", "filters": {"unit": "CLV_I10", "na_item": "B1GQ", "s_adj": "SCA"}}, 
    "UNEMPLOYMENT": {"code": "une_rt_m", "filters": {"unit": "PC_ACT", "age": "TOTAL", "sex": "T", "s_adj": "SA"}},
    
    # --- DEUDA & FISCALIDAD ---
    # sdg_17_40: Deuda pública bruta del gobierno general (en millones EUR y % PIB)
    "DEBT_PC": {"code": "sdg_17_40", "filters": {"unit": "PC_GDP", "geo": "ES"}},  # Deuda como % del PIB (más interpretable)
    # gov_10a_main: Ingresos totales del gobierno general
    "TAX_REVENUE": {"code": "gov_10a_main", "filters": {"unit": "PC_GDP", "na_item": "TR", "sector": "S13", "geo": "ES"}},  # TR = Total Revenue
    "BOND_YIELD": {"code": "irt_lt_mcby_m", "filters": {"geo": "ES"}},
    
    # --- EDUCACION & SOCIEDAD ---
    # NEET: unit es "PC" (no PC_POP)
    "NEET": {"code": "edat_lfse_20", "filters": {"unit": "PC", "sex": "T", "age": "Y15-29", "geo": "ES"}}, 
    
    # --- VIVIENDA ---
    "HOUSE_PRICES": {"code": "prc_hpi_q", "filters": {"unit": "I15_Q", "geo": "ES"}},
    
    # --- OTROS ---
    "HICP": {"code": "prc_hicp_manr", "filters": {"unit": "I15", "coicop": "CP00", "geo": "ES"}}, 
    "SENTIMENT": {"code": "teibs010", "filters": {"geo": "ES"}}
}

# Constants
PEER_COUNTRIES = ['ES', 'DE', 'FR', 'IT', 'PT', 'PL']
PCA_COMPONENTS = 1
ICTR_BASE = 100
ICTR_SCALE = 10