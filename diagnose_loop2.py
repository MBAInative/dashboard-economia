"""
Diagnóstico del bucle infinito - guardar a archivo
"""
import sys
import time
sys.path.insert(0, 'app')

results = []
results.append("="*60)
results.append("DIAGNÓSTICO DE CARGA DE DATOS")
results.append("="*60)

start_total = time.time()

results.append(f"\n[1] Importando módulos...")
start = time.time()
from data_loader import fetch_eurostat_data, fetch_eurostat_multi_country
from utils import EUROSTAT_CONFIG, PEER_COUNTRIES
results.append(f"    OK ({time.time()-start:.1f}s)")

# Test individual datasets
tests = [
    ("REAL_GDP_PC", EUROSTAT_CONFIG["REAL_GDP_PC"]),
    ("UNEMPLOYMENT", EUROSTAT_CONFIG["UNEMPLOYMENT"]),
    ("GINI", EUROSTAT_CONFIG["GINI"]),
    ("NEET", EUROSTAT_CONFIG["NEET"]),
    ("DEBT_PC", EUROSTAT_CONFIG["DEBT_PC"]),
]

for name, config in tests:
    start = time.time()
    results.append(f"\n[{name}] Cargando {config['code']}...")
    try:
        df = fetch_eurostat_data(config['code'], config.get('filters'))
        elapsed = time.time() - start
        if df is not None and not df.empty:
            results.append(f"    OK - {len(df)} filas ({elapsed:.1f}s)")
        else:
            results.append(f"    VACÍO ({elapsed:.1f}s)")
    except Exception as e:
        results.append(f"    ERROR: {e} ({time.time()-start:.1f}s)")

# Test multi-country
results.append(f"\n[PEERS GDP] Cargando GDP para {PEER_COUNTRIES}...")
start = time.time()
try:
    filters = {k: v for k, v in EUROSTAT_CONFIG["GDP_PEERS"].get('filters', {}).items() if k.lower() != 'geo'}
    data = fetch_eurostat_multi_country(EUROSTAT_CONFIG["GDP_PEERS"]['code'], PEER_COUNTRIES, filters)
    elapsed = time.time() - start
    for country, df in data.items():
        status = f"{len(df)} filas" if df is not None and not df.empty else "VACÍO"
        results.append(f"    {country}: {status}")
    results.append(f"    Total: {elapsed:.1f}s")
except Exception as e:
    results.append(f"    ERROR: {e}")

results.append(f"\n[PEERS UNEMP] Cargando Paro para {PEER_COUNTRIES}...")
start = time.time()
try:
    filters = {k: v for k, v in EUROSTAT_CONFIG["UNEMPLOYMENT"].get('filters', {}).items() if k.lower() != 'geo'}
    data = fetch_eurostat_multi_country(EUROSTAT_CONFIG["UNEMPLOYMENT"]['code'], PEER_COUNTRIES, filters)
    elapsed = time.time() - start
    for country, df in data.items():
        status = f"{len(df)} filas" if df is not None and not df.empty else "VACÍO"
        results.append(f"    {country}: {status}")
    results.append(f"    Total: {elapsed:.1f}s")
except Exception as e:
    results.append(f"    ERROR: {e}")

results.append(f"\nTIEMPO TOTAL: {time.time()-start_total:.1f}s")
results.append("\n" + "="*60)

with open('diagnose_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
print('Guardado en diagnose_result.txt')
