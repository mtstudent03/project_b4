import pandas as pd

def library_merger(yt_df, reading_df, ig_df, concentration_df):
    master_library = pd.concat([yt_df, reading_df, ig_df, concentration_df], axis=1).sort_index()
    time_cols = [c for c in master_library.columns if c != 'concentration']
    master_library[time_cols] = master_library[time_cols].fillna(0)
    return master_library