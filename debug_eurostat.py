import eurostat
import pandas as pd

# Test GDP dataset
code = "namq_10_gdp"
print(f"Fetching {code}...")

try:
    df = eurostat.get_data_df(code)
    print("Columns:", df.columns.tolist())
    print("Head:", df.head(2))
    
    # Check distinct values for filtering
    if 'geo\time' in df.columns:
        print("Countries:", df['geo\time'].unique())
    elif 'geo' in df.columns:
        print("Countries:", df['geo'].unique())
        
    if 'unit' in df.columns:
        print("Units:", df['unit'].unique())
        
except Exception as e:
    print("Error:", e)
