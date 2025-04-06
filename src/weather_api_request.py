from typing import Dict, Union, Tuple

import requests
from datetime import datetime, timedelta
import pandas as pd

from src.definitions import WeatherVariable, Coordinate, WeatherModel

FORECAST_API_ENDPOINT = 'https://api.open-meteo.com/v1/forecast'
HISTORICAL_API_ENDPOINT = 'http://127.0.0.1:8081/v1/archive'


class WeatherApiException(Exception):
    """Raised when the weather API does not successfully provide weather data."""
    pass


def get_forecast_and_historical_data(
        coordinate: Coordinate,
        weather_variable: WeatherVariable,
        weather_model: WeatherModel
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Get start and end date
    today = datetime.fromtimestamp(coordinate.timestamp)
    start_date = today - timedelta(days=30)
    end_date_historical = today - timedelta(days=360)
    end_date_historical_string = end_date_historical.strftime('%Y-%m-%d')
    today_string = today.strftime('%Y-%m-%d')
    start_date_string = start_date.strftime('%Y-%m-%d')

    parameters_forecast = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'daily': weather_variable.value,
        'timezone': 'auto',
        'start_date': start_date_string,
        'end_date': today_string
    }

    parameters_historical = {
        'latitude': coordinate.latitude,
        'longitude': coordinate.longitude,
        'models': weather_model.value,
        'daily': weather_variable.value,
        'timezone': 'auto',
        'start_date': '1940-01-01',
        'end_date': end_date_historical_string
    }

    forecast_data = weather_api_request(
        parameters=parameters_forecast,
        weather_variable=weather_variable,
        api_uri=FORECAST_API_ENDPOINT)
    historical_data = weather_api_request(
        parameters=parameters_historical,
        weather_variable=weather_variable,
        api_uri=HISTORICAL_API_ENDPOINT
    )

    return forecast_data, historical_data


def weather_api_request(
        parameters: Dict[str, Union[str, float]],
        weather_variable: WeatherVariable,
        api_uri: str
) -> pd.DataFrame:
    api_response = requests.get(api_uri, params=parameters)

    if api_response.status_code != 200:
        raise WeatherApiException(f'Failed to fetch weather data with: {api_response.json()["reason"]}')

    return pd.DataFrame(
        data=api_response.json()['daily'][weather_variable.value],
        index=pd.DatetimeIndex(api_response.json()['daily']['time']),
        columns=[weather_variable.value]
    )
