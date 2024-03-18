import pandas as pd
import os


def aggregate_and_save(directory):
    count = 0
    df = None
    for data_dir in os.listdir(directory):
        path = os.path.join(os.getcwd(), directory, data_dir, "results.csv")
        if os.path.exists(path):
            count += 1
            appendable = pd.read_csv(path, header=0)
            if count == 1:
                df = appendable
            else:
                df = df._append(appendable, ignore_index=True)

    if df is not None:
        df = df.rename(columns={'Unnamed: 0': 'DirIndex'})
        df.to_csv(os.path.join(os.getcwd(), f"{directory}/all_results.csv"))
