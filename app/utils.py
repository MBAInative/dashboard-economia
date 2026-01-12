# Mapping of indicators and API configurations

# INE Indicators (Table IDs / Series Codes)
# Note: These might need adjustment based on exact series IDs available in INE API
INE_CONFIG = {
    "GDP": {"id": "CNTR", "operation": "30678"},  # Contabilidad Nacional Trimestral
    "CPI": {"id": "IPC", "operation": "251852"},   # Indice de Precios de Consumo
    "HOURS_WORKED": {"id": "EPA_HOURS", "operation": "30456"}, # Horas trabajadas (EPA)
    "IPI": {"id": "IPI", "operation": "XXX"}, # Indice de Produccion Industrial (Placeholder)
    "COMPANY_CREATION": {"id": "COMP", "operation": "XXX"} # Sociedades Mercantiles
}

# Eurostat Indicators (Dataset Codes)
EUROSTAT_CONFIG = {
    "HICP": "prc_hicp_manr",  # Harmonised index of consumer prices
    "GDP": "namq_10_gdp",     # GDP and main components
    "DEBT": "gov_10dd_edpt1", # Quarterly government debt
    "CONFIDENCE": "teibs010", # Economic sentiment indicator
    "UNEMPLOYMENT": "une_rt_m", # Unemployment by sex and age - monthly data
    "RETAIL_TRADE": "sts_trtu_m" # Retail trade volume (ICM equivalent proxy)
}

# Constants for PCA
PCA_COMPONENTS = 1
ICTR_BASE = 100
ICTR_SCALE = 10
