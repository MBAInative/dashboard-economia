"""
Verificación de datos de paro - guardando a archivo
"""
import sys
sys.path.insert(0, 'app')

from data_loader import fetch_eurostat_data, fetch_eurostat_multi_country
from utils import EUROSTAT_CONFIG, PEER_COUNTRIES

results = []
results.append("="*60)
results.append("VERIFICACIÓN DATOS DE PARO")
results.append("="*60)

# Config actual
config = EUROSTAT_CONFIG["UNEMPLOYMENT"]
results.append(f"\nConfig: {config}")

# Obtener datos para todos los países
filters = {k: v for k, v in config.get('filters', {}).items() if k.lower() != 'geo'}
data = fetch_eurostat_multi_country(config['code'], PEER_COUNTRIES, filters)

results.append("\nÚltimos datos por país:")
for country, df in data.items():
    if not df.empty:
        ultimo = df['value'].iloc[-1]
        fecha = df['date'].iloc[-1]
        results.append(f"  {country}: {ultimo:.1f}% (fecha: {fecha})")
    else:
        results.append(f"  {country}: SIN DATOS")

# Verificar si los datos son razonables
results.append("\n" + "="*60)
results.append("REFERENCIA: Tasas de paro esperadas (aprox. 2024)")
results.append("="*60)
results.append("  ES: ~11-12%")
results.append("  DE: ~3-4%")
results.append("  FR: ~7-8%")
results.append("  IT: ~7-8%")
results.append("  PT: ~6-7%")
results.append("  PL: ~3-4%")

with open('verify_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
print('Guardado en verify_result.txt')
