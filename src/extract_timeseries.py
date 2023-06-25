import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# %%
def get_historical_timeseries(coordinate, data_historical):
    date = datetime.fromtimestamp(coordinate.timestamp)

    # select week and months
    weekly_data = []
    monthly_data = []

    for year in range(1950, date.year):
        end_date = datetime(year=year, month=date.month, day=date.day)
        week = pd.date_range(end_date - timedelta(days=6), end_date, freq='d')
        weekly_data.append(float(data_historical.loc[week].mean()))
        month = pd.date_range(end_date - timedelta(days=30), end_date, freq='d')
        monthly_data.append(float(data_historical.loc[month].mean()))

    daily_data = data_historical[(data_historical.index.month == date.month) & (data_historical.index.day == date.day)]
    daily_data.index = daily_data.index.year
    weekly_data = pd.DataFrame(data={daily_data.columns[0]: weekly_data}, index=np.arange(1950, date.year))
    monthly_data = pd.DataFrame(data={daily_data.columns[0]: monthly_data}, index=np.arange(1950, date.year))

    return daily_data, weekly_data, monthly_data
