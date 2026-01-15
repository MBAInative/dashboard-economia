"""
Verificación de datos de paro
"""
import sys
sys.path.insert(0, 'app')

from data_loader import fetch_eurostat_data, fetch_eurostat_multi_country
from utils import EUROSTAT_CONFIG, PEER_COUNTRIES

print("="*60)
print("VERIFICACIÓN DATOS DE PARO")
print("="*60)

# Config actual
config = EUROSTAT_CONFIG["UNEMPLOYMENT"]
print(f"\nConfig: {config}")

# Obtener datos para todos los países
filters = {k: v for k, v in config.get('filters', {}).items() if k.lower() != 'geo'}
data = fetch_eurostat_multi_country(config['code'], PEER_COUNTRIES, filters)

print("\nÚltimos datos por país:")
for country, df in data.items():
    if not df.empty:
        ultimo = df['value'].iloc[-1]
        fecha = df['date'].iloc[-1]
        print(f"  {country}: {ultimo:.1f}% (fecha: {fecha})")
    else:
        print(f"  {country}: SIN DATOS")

# Verificar si los datos son razonables
print("\n" + "="*60)
print("REFERENCIA: Tasas de paro esperadas (aprox. 2024)")
print("="*60)
print("  ES: ~11-12%")
print("  DE: ~3-4%")
print("  FR: ~7-8%")
print("  IT: ~7-8%")
print("  PT: ~6-7%")
print("  PL: ~3-4%")
