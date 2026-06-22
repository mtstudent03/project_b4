import pandas as pd

def library_merger(yt_df, reading_df, ig_df):
    master_library = pd.concat([yt_df, reading_df, ig_df], axis=1).sort_index()
    master_library = master_library.fillna(0)
    return master_library