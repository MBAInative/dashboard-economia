"""
Test de carga optimizada
"""
import sys
import time
sys.path.insert(0, 'app')

print("Testing optimized data loading...")
start = time.time()

from data_loader import fetch_eurostat_multi_country
from utils import EUROSTAT_CONFIG, PEER_COUNTRIES

# GDP
print("\n[GDP PEERS]")
gdp_config = EUROSTAT_CONFIG["GDP_PEERS"]
gdp_filters = {k: v for k, v in gdp_config.get('filters', {}).items() if k.lower() != 'geo'}
t = time.time()
gdp_data = fetch_eurostat_multi_country(gdp_config['code'], PEER_COUNTRIES, gdp_filters)
print(f"  Tiempo: {time.time()-t:.1f}s")
for c, df in gdp_data.items():
    print(f"  {c}: {len(df) if df is not None and not df.empty else 0} filas")

# Unemployment
print("\n[UNEMP PEERS]")
unemp_config = EUROSTAT_CONFIG["UNEMPLOYMENT"]
unemp_filters = {k: v for k, v in unemp_config.get('filters', {}).items() if k.lower() != 'geo'}
t = time.time()
unemp_data = fetch_eurostat_multi_country(unemp_config['code'], PEER_COUNTRIES, unemp_filters)
print(f"  Tiempo: {time.time()-t:.1f}s")
for c, df in unemp_data.items():
    if df is not None and not df.empty:
        print(f"  {c}: {len(df)} filas, último={df['value'].iloc[-1]:.1f}%")
    else:
        print(f"  {c}: VACÍO")

print(f"\nTOTAL: {time.time()-start:.1f}s")
