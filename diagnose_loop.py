"""
Diagnóstico del bucle infinito
"""
import sys
import time
sys.path.insert(0, 'app')

print("="*60)
print("DIAGNÓSTICO DE CARGA DE DATOS")
print("="*60)

start = time.time()
print(f"\n[1] Importando módulos...")
from data_loader import fetch_eurostat_data, fetch_eurostat_multi_country
from utils import EUROSTAT_CONFIG, PEER_COUNTRIES
print(f"    OK ({time.time()-start:.1f}s)")

# Test individual datasets
tests = [
    ("REAL_GDP_PC", EUROSTAT_CONFIG["REAL_GDP_PC"]),
    ("UNEMPLOYMENT", EUROSTAT_CONFIG["UNEMPLOYMENT"]),
    ("GINI", EUROSTAT_CONFIG["GINI"]),
]

for name, config in tests:
    start = time.time()
    print(f"\n[{name}] Cargando {config['code']}...")
    try:
        df = fetch_eurostat_data(config['code'], config.get('filters'))
        elapsed = time.time() - start
        if df is not None and not df.empty:
            print(f"    OK - {len(df)} filas ({elapsed:.1f}s)")
        else:
            print(f"    VACÍO ({elapsed:.1f}s)")
    except Exception as e:
        print(f"    ERROR: {e} ({time.time()-start:.1f}s)")

# Test multi-country (this might be the slow one)
print(f"\n[PEERS] Cargando datos para {PEER_COUNTRIES}...")
start = time.time()
try:
    filters = {k: v for k, v in EUROSTAT_CONFIG["UNEMPLOYMENT"].get('filters', {}).items() if k.lower() != 'geo'}
    data = fetch_eurostat_multi_country(EUROSTAT_CONFIG["UNEMPLOYMENT"]['code'], PEER_COUNTRIES, filters)
    elapsed = time.time() - start
    for country, df in data.items():
        status = f"{len(df)} filas" if not df.empty else "VACÍO"
        print(f"    {country}: {status}")
    print(f"    Total: {elapsed:.1f}s")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "="*60)
print("DIAGNÓSTICO COMPLETADO")
print("="*60)
