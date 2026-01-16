"""
Verificar fechas más recientes de los datos
"""
import sys
sys.path.insert(0, 'app')

from data_loader import fetch_eurostat_data
from utils import EUROSTAT_CONFIG

indicators = ['REAL_GDP_PC', 'GINI', 'HICP', 'DEBT_PC', 'NEET', 'AROPE']

print("="*60)
print("FECHAS MÁS RECIENTES DE LOS DATOS")
print("="*60)

for ind in indicators:
    try:
        config = EUROSTAT_CONFIG[ind]
        df = fetch_eurostat_data(config['code'], config.get('filters'))
        if df is not None and not df.empty:
            max_date = df['date'].max()
            last_val = df['value'].iloc[-1]
            print(f"{ind}: {max_date} -> {last_val:.1f}")
        else:
            print(f"{ind}: SIN DATOS")
    except Exception as e:
        print(f"{ind}: ERROR - {e}")

print("="*60)
