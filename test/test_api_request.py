from unittest import TestCase
from unittest.mock import patch, ANY

import pandas as pd
import pytest
import responses
from requests import Response

import src.weather_api_request
from src.definitions import WeatherVariable, TimeFrame, Coordinate, WeatherModel
from src.weather_api_request import FORECAST_API_ENDPOINT, weather_api_request, WeatherApiException, \
    get_forecast_and_historical_data, HISTORICAL_API_ENDPOINT


@pytest.fixture
def forecast_parameters():
    return {
        'latitude': 48.3504104,
        'longitude': 10.8766662,
        'daily': WeatherVariable.TEMPERATURE.value,
        'timezone': 'auto',
        'start_date': '2023-05-23',
        'end_date': '2023-06-22'
    }


@pytest.fixture
def historical_parameters():
    return {
        'daily': WeatherVariable.TEMPERATURE.value,
        'end_date': '2022-06-27',
        'latitude': 48.3504104,
        'longitude': 10.8766662,
        'models': 'era5_land',
        'start_date': '1950-01-01',
        'timezone': 'auto'
    }


@pytest.fixture
def successful_weather_api_response():
    return {
        'daily': {
            'time' : [
                '2023-05-23', '2023-05-24', '2023-05-25', '2023-05-26', '2023-05-27', '2023-05-28', '2023-05-29',
                '2023-05-30', '2023-05-31', '2023-06-01', '2023-06-02', '2023-06-03', '2023-06-04', '2023-06-05',
                '2023-06-06', '2023-06-07', '2023-06-08', '2023-06-09', '2023-06-10', '2023-06-11', '2023-06-12',
                '2023-06-13', '2023-06-14', '2023-06-15', '2023-06-16', '2023-06-17', '2023-06-18', '2023-06-19',
                '2023-06-20', '2023-06-21', '2023-06-22'
            ],
            WeatherVariable.TEMPERATURE.value: [
                20.5, 14.6, 20.9, 22.4, 22.2, 22.8, 23.6, 22.8, 23.3, 25.2, 24.1, 23.0, 23.0, 24.2, 21.5, 24.0,
                26.2, 25.0, 24.4, 25.4, 24.5, 23.2, 23.4, 23.1, 24.2, 26.2, 29.1, 29.8, 32.2, 26.1, 32.7
            ]
        }
    }


@pytest.fixture
def weather_data(successful_weather_api_response):
    return pd.DataFrame(
        data=successful_weather_api_response[TimeFrame.DAILY.value][WeatherVariable.TEMPERATURE.value],
        index=pd.DatetimeIndex(successful_weather_api_response[TimeFrame.DAILY.value]['time']),
        columns=[WeatherVariable.TEMPERATURE.value]
    )


@pytest.fixture
def failed_weather_api_response():
    return {
        'reason': 'Failure reason.'
    }


@pytest.fixture(scope='package')
def coordinate():
    return Coordinate(
        timestamp=1687461397,
        latitude=48.3504104,
        longitude=10.8766662
    )


@responses.activate
def test_weather_api_request_successful(successful_weather_api_response, forecast_parameters):
    responses.add(
        method=responses.GET,
        url=FORECAST_API_ENDPOINT,
        json=successful_weather_api_response,
        status=200
    )

    expected = pd.DataFrame(
        data=successful_weather_api_response[TimeFrame.DAILY.value][WeatherVariable.TEMPERATURE.value],
        index=pd.DatetimeIndex(successful_weather_api_response[TimeFrame.DAILY.value]['time']),
        columns=[WeatherVariable.TEMPERATURE.value]
    )
    actual = weather_api_request(
        parameters=forecast_parameters,
        weather_variable=WeatherVariable.TEMPERATURE,
        api_uri=FORECAST_API_ENDPOINT
    )

    pd.testing.assert_frame_equal(expected, actual)


@responses.activate
def test_weather_api_request_failure(forecast_parameters, failed_weather_api_response):
    responses.add(
        method=responses.GET,
        url=FORECAST_API_ENDPOINT,
        json=failed_weather_api_response,
        status=400
    )

    with pytest.raises(WeatherApiException):
        weather_api_request(
            parameters=forecast_parameters,
            weather_variable=WeatherVariable.TEMPERATURE,
            api_uri=FORECAST_API_ENDPOINT
        )


def test_get_forecast_and_historical_data_successful(
        successful_weather_api_response,
        weather_data,
        coordinate,
        forecast_parameters,
        historical_parameters
):
    with patch('src.weather_api_request.weather_api_request', return_value=weather_data) as mock_weather_api_request:
        actual_forecast_data, actual_historical_data = get_forecast_and_historical_data(
            coordinate=coordinate,
            weather_variable=WeatherVariable.TEMPERATURE,
            weather_model=WeatherModel.ERA5_LAND
        )

        pd.testing.assert_frame_equal(weather_data, actual_forecast_data)
        pd.testing.assert_frame_equal(weather_data, actual_historical_data)

        TestCase().assertDictEqual(forecast_parameters, mock_weather_api_request.call_args_list[0].kwargs['parameters'])
        assert WeatherVariable.TEMPERATURE == mock_weather_api_request.call_args_list[0].kwargs['weather_variable']
        assert FORECAST_API_ENDPOINT == mock_weather_api_request.call_args_list[0].kwargs['api_uri']

        TestCase().assertDictEqual(historical_parameters, mock_weather_api_request.call_args_list[1].kwargs['parameters'])
        assert WeatherVariable.TEMPERATURE == mock_weather_api_request.call_args_list[1].kwargs['weather_variable']
        assert HISTORICAL_API_ENDPOINT == mock_weather_api_request.call_args_list[1].kwargs['api_uri']


def test_get_forecast_and_historical_data_failure(
        successful_weather_api_response,
        weather_data,
        coordinate,
        forecast_parameters,
        historical_parameters
):
    with pytest.raises(WeatherApiException):
        with patch('src.weather_api_request.weather_api_request', side_effect=WeatherApiException()):
            get_forecast_and_historical_data(
                coordinate=coordinate,
                weather_variable=WeatherVariable.TEMPERATURE,
                weather_model=WeatherModel.ERA5_LAND
            )
