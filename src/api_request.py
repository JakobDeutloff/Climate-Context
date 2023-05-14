import requests
from datetime import datetime, timedelta
import pandas as pd
# %%

async def get_forecast_data(coordinate):

    # Get start and enddate
    today = datetime.fromtimestamp(coordinate.timestamp)
    startdate = today - timedelta(days=30)
    today_string = today.strftime('%Y-%m-%d')
    startdate_string = startdate.strftime('%Y-%m-%d')

    parameters = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'daily': 'temperature_2m_max',
        'timezone': 'auto',
        'start_date': startdate_string,
        'end_date': today_string
    }

    request = requests.get('https://api.open-meteo.com/v1/forecast', parameters)
    daily_data = pd.DataFrame(data=request.json()['daily']['temperature_2m_max'],
                              index=pd.DatetimeIndex(request.json()['daily']['time']),
                              columns=['temperature_2m_max'])

    return daily_data

