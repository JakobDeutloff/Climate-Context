import requests
from datetime import datetime, timedelta
import pandas as pd


# %%

async def get_forecast_and_historical_data(coordinate, variable, models):
    # Get start and enddate
    today = datetime.fromtimestamp(coordinate.timestamp)
    startdate = today - timedelta(days=30)
    enddate_historical = today - timedelta(days=360)
    enddate_historical_string = enddate_historical.strftime('%Y-%m-%d')
    today_string = today.strftime('%Y-%m-%d')
    startdate_string = startdate.strftime('%Y-%m-%d')

    parameters_forecast = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'daily': variable,
        'timezone': 'auto',
        'start_date': startdate_string,
        'end_date': today_string
    }

    parameters_historical = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'models': models,
        'daily': variable,
        'timezone': 'auto',
        'start_date': '1950-01-01',
        'end_date': enddate_historical_string
    }

    return api_request(parameters_forecast, parameters_historical, variable)


def api_request(parameters_forecast, parameters_historical, variable):
    request_forecast = requests.get('https://api.open-meteo.com/v1/forecast', parameters_forecast)
    forecast_data = pd.DataFrame(data=request_forecast.json()['daily'][variable],
                                 index=pd.DatetimeIndex(request_forecast.json()['daily']['time']),
                                 columns=[variable])

    request_historical = requests.get('https://archive-api.open-meteo.com/v1/archive', parameters_historical)
    historical_data = pd.DataFrame(data=request_historical.json()['daily'][variable],
                                   index=pd.DatetimeIndex(request_historical.json()['daily']['time']),
                                   columns=[variable])
    return forecast_data, historical_data
