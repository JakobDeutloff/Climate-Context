from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.stats import norm, gamma

from src.definitions import WeatherVariable, ReturnPeriodMode, TimeFrame
from src.extract_timeseries import get_historical_timeseries
from src.weather_api_request import get_forecast_and_historical_data
import logging
logger = logging.getLogger('uvicorn.error')

# Small constant to avoid division by zero.
EPSILON = 1e-6


WEATHER_VARIABLE_TO_DISTRIBUTION = {
    WeatherVariable.TEMPERATURE: norm,
    WeatherVariable.PRECIPITATION: gamma
}


def calculate_return_period(
        timeseries: pd.DataFrame,
        current_value: float,
        mode: ReturnPeriodMode = ReturnPeriodMode.MAX
) -> float:
    """
    Computes the value of the return period for the current value of the weather variable.

    Args:
        timeseries: Days in years timeseries at location in °C.
        current_value: Daily temperature in °C.
        mode: Indicates whether extreme minima or maxima are investigated. For values higher than mean temperature
            choose ReturnPeriodMode.MAX, else choose ReturnPeriodMode.MIN.

    Returns:
        Return period in years.
    """
    cumulative_probability = calculate_cumulative_probability(
        timeseries=timeseries,
        current_value=current_value,
        weather_variable=WeatherVariable(timeseries.columns[0])
    )

    if mode == ReturnPeriodMode.MAX:
        return_period = 1 / (1 - cumulative_probability + EPSILON)
    else:
        # Mode is ReturnPeriodMode.MIN.
        return_period = 1 / (cumulative_probability + EPSILON)
    return return_period


def calculate_cumulative_probability(
        timeseries: pd.DataFrame,
        current_value: float,
        weather_variable: WeatherVariable
) -> float:
    probability_distribution = WEATHER_VARIABLE_TO_DISTRIBUTION[weather_variable]

    pdf_parameters = probability_distribution.fit(timeseries)

    # Cumulative probability distribution doesn't fit well to a distribution, where many values are at the edge
    # of the distribution at 0.
    if WeatherVariable.PRECIPITATION == weather_variable and current_value == 0:
        _, counts = np.unique(timeseries, return_counts=True)
        # Use first element which should usually be 0. Otherwise, lowest element is taken as unique returns sorted.
        return counts[0] / len(timeseries)

    return probability_distribution.cdf(current_value, *pdf_parameters)


def calculate_mean_value_current_value_and_rp(
        historical_values,
        forecast_values,
        coordinate,
        time_frame
):
    # get date
    date = datetime.fromtimestamp(coordinate.timestamp)
    date_string = date.strftime('%Y-%m-%d')

    # Calculate current temperature
    if TimeFrame.DAILY == time_frame:
        current_value = float(forecast_values.loc[date_string].values)
    elif TimeFrame.WEEKLY == time_frame:
        date_last_week = date - timedelta(days=6)
        date_last_week_string = date_last_week.strftime('%Y-%m-%d')
        current_value = float(forecast_values.loc[date_last_week_string:date_string].mean().values)
    elif TimeFrame.MONTHLY == time_frame:
        date_last_month = date - timedelta(days=30)
        date_last_month_string = date_last_month.strftime('%Y-%m-%d')
        current_value = float(forecast_values.loc[date_last_month_string:date_string].mean().values)
    else:
        current_value = []

    # calculate average temperature over the whole timeseries
    mean_historical_value = float(historical_values.mean().values)

    # calculate return period of actual temperature
    if current_value > mean_historical_value:
        return_period = calculate_return_period(historical_values, current_value, mode=ReturnPeriodMode.MAX)
        last_occurrence = calculate_last_occurrence(historical_values, current_value, mode=ReturnPeriodMode.MAX)
    elif current_value < mean_historical_value:
        return_period = calculate_return_period(historical_values, current_value, mode=ReturnPeriodMode.MIN)
        last_occurrence = calculate_last_occurrence(historical_values, current_value, mode=ReturnPeriodMode.MIN)
    else:
        return_period = 2  # if temperatures are the same cdf=0.5 which gives rp=2
        last_occurrence = calculate_last_occurrence(historical_values, current_value, mode=ReturnPeriodMode.MAX)

    return mean_historical_value, return_period, current_value, last_occurrence


def calculate_last_occurrence(historical_data, current_value, mode):
    if ReturnPeriodMode.MAX == mode:
        if historical_data.iloc[:, 0].sort_index(ascending=False).ge(current_value).eq(False).all():
            return 'Never'
        return historical_data.iloc[:, 0].sort_index(ascending=False).ge(current_value).idxmax().item()
    else:
        if historical_data.iloc[:, 0].sort_index(ascending=False).le(current_value).eq(False).all():
            return 'Never'
        return historical_data.iloc[:, 0].sort_index(ascending=False).le(current_value).idxmax().item()


def get_weather_variable_data(coordinate, weather_model, weather_variable, weather_variable_name):
    forecast_data, historical_data = get_forecast_and_historical_data(
        coordinate=coordinate,
        weather_variable=weather_variable,
        weather_model=weather_model
    )

    logger.info('Calculate weather climate context stats.')
    daily_historical_data, weekly_historical_data, monthly_historical_data = \
        get_historical_timeseries(coordinate, historical_data)

    daily_mean_value, daily_return_period, daily_current_value, daily_last_occurrence = \
        calculate_mean_value_current_value_and_rp(
            daily_historical_data,
            forecast_data,
            coordinate,
            time_frame=TimeFrame.DAILY
        )

    weekly_mean_value, weekly_return_period, weekly_current_value, weekly_last_occurrence = \
        calculate_mean_value_current_value_and_rp(
            weekly_historical_data,
            forecast_data,
            coordinate,
            time_frame=TimeFrame.WEEKLY
        )

    monthly_mean_value, monthly_return_period, monthly_current_value, monthly_last_occurrence = \
        calculate_mean_value_current_value_and_rp(
            monthly_historical_data,
            forecast_data,
            coordinate,
            time_frame=TimeFrame.MONTHLY
        )

    return {
        f'daily_average_{weather_variable_name.value}': daily_mean_value,
        f'daily_current_{weather_variable_name.value}': daily_current_value,
        f'daily_return_period_{weather_variable_name.value}': daily_return_period,
        f'daily_historical_{weather_variable_name.value}': list(daily_historical_data.values.squeeze()),
        'daily_historical_index': list(daily_historical_data.index),
        f'daily_last_occurrence_{weather_variable_name.value}': daily_last_occurrence,
        f'weekly_average_{weather_variable_name.value}': weekly_mean_value,
        f'weekly_current_{weather_variable_name.value}': weekly_current_value,
        f'weekly_return_period_{weather_variable_name.value}': weekly_return_period,
        f'weekly_historical_{weather_variable_name.value}': list(weekly_historical_data.values.squeeze()),
        'weekly_historical_index': list(weekly_historical_data.index),
        f'weekly_last_occurrence_{weather_variable_name.value}': weekly_last_occurrence,
        f'monthly_average_{weather_variable_name.value}': monthly_mean_value,
        f'monthly_current_{weather_variable_name.value}': monthly_current_value,
        f'monthly_return_period_{weather_variable_name.value}': monthly_return_period,
        f'monthly_historical_{weather_variable_name.value}': list(monthly_historical_data.values.squeeze()),
        'monthly_historical_index': list(monthly_historical_data.index),
        f'monthly_last_occurrence_{weather_variable_name.value}': monthly_last_occurrence,
    }
