import requests
from datetime import datetime, timedelta
import pandas as pd


# %%

async def get_forecast_and_historical_data(coordinate):
    # Get start and enddate
    today = datetime.fromtimestamp(coordinate.timestamp)
    startdate = today - timedelta(days=30)
    today_string = today.strftime('%Y-%m-%d')
    startdate_string = startdate.strftime('%Y-%m-%d')

    parameters_forecast = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'daily': 'temperature_2m_max',
        'timezone': 'auto',
        'start_date': startdate_string,
        'end_date': today_string
    }

    parameters_historical = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'models': 'era5_land',
        'daily': 'temperature_2m_max',
        'timezone': 'auto',
        'start_date': '1950-01-01',
        'end_date': today_string
    }

    request_forecast = requests.get('https://api.open-meteo.com/v1/forecast', parameters_forecast)
    forecast_data = pd.DataFrame(data=request_forecast.json()['daily']['temperature_2m_max'],
                                 index=pd.DatetimeIndex(request_forecast.json()['daily']['time']),
                                 columns=['temperature_2m_max'])

    request_historical = requests.get('https://archive-api.open-meteo.com/v1/archive', parameters_historical)
    historical_data = pd.DataFrame(data=request_historical.json()['daily']['temperature_2m_max'],
                                   index=pd.DatetimeIndex(request_historical.json()['daily']['time']),
                                   columns=['temperature_2m_max'])

    return forecast_data, historical_data
