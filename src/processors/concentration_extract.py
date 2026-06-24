import pandas as pd

def parse_concentration(path):
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.dropna(subset=['date', 'concentration'])
    df['concentration'] = df['concentration'].astype(int).clip(1, 10)
    df = df.set_index('date')
    df.index = pd.to_datetime(df.index)
    return df[['concentration']]
