import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# %%
async def get_historical_timeseries(coordinate, data_historical):
    date = datetime.fromtimestamp(coordinate.timestamp)

    # select week and months
    weekly_data = np.array([])
    monthly_data = np.array([])

    for year in range(1950, date.year):
        enddate = datetime(year=year, month=date.month, day=date.day)
        week = pd.date_range(enddate - timedelta(days=6), enddate, freq='d')
        weekly_data = np.append(weekly_data, data_historical.loc[week].mean())
        month = pd.date_range(enddate - timedelta(days=30), enddate, freq='d')
        monthly_data = np.append(monthly_data, data_historical.loc[month].mean())

    daily_data = data_historical[(data_historical.index.month == date.month) & (data_historical.index.day == date.day)]
    daily_data.index = daily_data.index.year
    weekly_data = pd.DataFrame(data=weekly_data, index=np.arange(1950, date.year))
    monthly_data = pd.DataFrame(data=monthly_data, index=np.arange(1950, date.year))

    return daily_data, weekly_data, monthly_data
