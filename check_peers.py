import eurostat
import pandas as pd

def check_peers():
    code = "namq_10_gdp"
    peers = ['ES', 'DE', 'FR', 'IT', 'PT', 'PL']
    print(f"--- CHECKING PEERS FOR {code} ---")
    
    try:
        df = eurostat.get_data_df(code)
        df.columns = [c.lower() for c in df.columns]
        
        geo_col = next((c for c in df.columns if 'geo' in c), None)
        
        # Filter for peers
        df = df[df[geo_col].isin(peers)]
        
        # Check common units
        available_units = df['unit'].unique()
        print("All Units:", available_units)
        
        # Find a unit present for ALL peers
        valid_units = []
        for u in available_units:
            countries_with_unit = df[df['unit'] == u][geo_col].unique()
            if len(countries_with_unit) == len(peers):
                valid_units.append(u)
        
        print(f"UNITS VALID FOR ALL {len(peers)} PEERS: {valid_units}")
        
        # Check Seasonality
        print("S_ADJ options:", df['s_adj'].unique())

    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_peers()
