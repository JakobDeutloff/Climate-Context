from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from numpy.random import default_rng
from scipy.stats import genextreme, gamma

from src.calculate_statistics import calculate_return_period, calculate_cumulative_probability, WeatherVariable, \
    ReturnPeriodMode, calculate_last_occurrence

TEMPERATURE_C = 0
TEMPERATURE_LOCATION = 15
TEMPERATURE_SCALE = 5

LOW_PRECIPITATION_A = 1
LOW_PRECIPITATION_LOCATION = 0
LOW_PRECIPITATION_SCALE = 2

HIGH_PRECIPITATION_A = 7.5
HIGH_PRECIPITATION_LOCATION = 15
HIGH_PRECIPITATION_SCALE = 2


@pytest.fixture
def temperature_timeseries():
    rng = default_rng(69514468002301609459978422552062721160)

    index = pd.Index(list(range(1950, 2023, 1)))
    data = {
        'temperature_2m_max': genextreme.rvs(
            c=TEMPERATURE_C,
            loc=TEMPERATURE_LOCATION,
            scale=TEMPERATURE_SCALE,
            size=len(index),
            random_state=rng
        )
    }
    return pd.DataFrame(
        index=index,
        data=data
    )


def get_precipitation_timeseries(a, location, scale):
    rng = default_rng(69514468002301609459978422552062721160)

    index = pd.Index(list(range(1950, 2023, 1)))
    temperature_data = gamma.rvs(
        a=a,
        loc=location,
        scale=scale,
        size=len(index),
        random_state=rng
    )
    # Usually, many days are without any precipitation.
    temperature_data = [np.floor(value) if value < 1 else value for value in temperature_data]
    data = {
        'precipitation_sum': temperature_data
    }
    return pd.DataFrame(
        index=index,
        data=data
    )


@pytest.fixture
def low_precipitation_timeseries():
    return get_precipitation_timeseries(LOW_PRECIPITATION_A, LOW_PRECIPITATION_LOCATION, LOW_PRECIPITATION_SCALE)


@pytest.fixture
def high_precipitation_timeseries():
    return get_precipitation_timeseries(HIGH_PRECIPITATION_A, HIGH_PRECIPITATION_LOCATION, HIGH_PRECIPITATION_SCALE)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_temperature_low_outlier(
        temperature_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=temperature_timeseries,
        current_value=-25,
        weather_variable=WeatherVariable.TEMPERATURE
    )
    assert cumulative_probability == pytest.approx(0)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_temperature_low(
        temperature_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=temperature_timeseries,
        current_value=10,
        weather_variable=WeatherVariable.TEMPERATURE
    )
    assert cumulative_probability == pytest.approx(expected=0.12, rel=0.1)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_temperature_medium(
        temperature_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=temperature_timeseries,
        current_value=15,
        weather_variable=WeatherVariable.TEMPERATURE
    )
    assert cumulative_probability == pytest.approx(expected=0.44, rel=0.1)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_temperature_high(
        temperature_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=temperature_timeseries,
        current_value=20,
        weather_variable=WeatherVariable.TEMPERATURE
    )
    assert cumulative_probability == pytest.approx(expected=0.76, rel=0.1)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_temperature_high_outlier(
        temperature_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=temperature_timeseries,
        current_value=45,
        weather_variable=WeatherVariable.TEMPERATURE
    )
    assert cumulative_probability == pytest.approx(expected=1, rel=0.1)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_precipitation_zero(
        low_precipitation_timeseries,
        high_precipitation_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=low_precipitation_timeseries,
        current_value=0,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(expected=0.42, rel=0.1)

    cumulative_probability = calculate_cumulative_probability(
        timeseries=high_precipitation_timeseries,
        current_value=0,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(expected=0.01, rel=0.5)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_precipitation_low(
        low_precipitation_timeseries,
        high_precipitation_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=low_precipitation_timeseries,
        current_value=5,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(expected=0.8, rel=0.1)

    cumulative_probability = calculate_cumulative_probability(
        timeseries=high_precipitation_timeseries,
        current_value=5,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(0)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_precipitation_high(
        low_precipitation_timeseries,
        high_precipitation_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=low_precipitation_timeseries,
        current_value=30,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(expected=0.99, rel=0.1)

    cumulative_probability = calculate_cumulative_probability(
        timeseries=high_precipitation_timeseries,
        current_value=30,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(expected=0.52, rel=0.1)


@pytest.mark.asyncio
async def test_calculate_cumulative_probability_precipitation_outlier(
        low_precipitation_timeseries,
        high_precipitation_timeseries
):
    cumulative_probability = calculate_cumulative_probability(
        timeseries=low_precipitation_timeseries,
        current_value=150,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(1)

    cumulative_probability = calculate_cumulative_probability(
        timeseries=high_precipitation_timeseries,
        current_value=150,
        weather_variable=WeatherVariable.PRECIPITATION
    )
    assert cumulative_probability == pytest.approx(1)


@pytest.mark.asyncio
@patch(
    'src.calculate_statistics.calculate_cumulative_probability',
    return_value=0.33
)
async def test_calculate_return_period_mode_min(
        calculate_cumulative_probability_mock,
        temperature_timeseries,
):
    current_value = 10
    return_period = calculate_return_period(
        timeseries=temperature_timeseries,
        current_value=current_value,
        mode=ReturnPeriodMode.MIN
    )

    pd.testing.assert_frame_equal(
        temperature_timeseries,
        calculate_cumulative_probability_mock.call_args.kwargs['timeseries']
    )
    assert current_value == calculate_cumulative_probability_mock.call_args.kwargs['current_value']
    assert WeatherVariable.TEMPERATURE == calculate_cumulative_probability_mock.call_args.kwargs['weather_variable']

    assert return_period == pytest.approx(expected=3, rel=0.1)


@pytest.mark.asyncio
@patch(
    'src.calculate_statistics.calculate_cumulative_probability',
    return_value=0.66
)
async def test_calculate_return_period_mode_max(
        calculate_cumulative_probability_mock,
        temperature_timeseries,
):
    current_value = 20
    return_period = calculate_return_period(
        timeseries=temperature_timeseries,
        current_value=current_value,
        mode=ReturnPeriodMode.MAX
    )

    pd.testing.assert_frame_equal(
        temperature_timeseries,
        calculate_cumulative_probability_mock.call_args.kwargs['timeseries']
    )
    assert current_value == calculate_cumulative_probability_mock.call_args.kwargs['current_value']
    assert WeatherVariable.TEMPERATURE == calculate_cumulative_probability_mock.call_args.kwargs['weather_variable']

    assert return_period == pytest.approx(expected=3, rel=0.1)


def test_calculate_last_occurrence_max(temperature_timeseries):
    current_temperature = 20
    expected_last_occurrence = 2017

    actual_last_occurrence = calculate_last_occurrence(
        current_value=current_temperature,
        historical_data=temperature_timeseries,
        mode=ReturnPeriodMode.MAX
    )

    assert expected_last_occurrence == actual_last_occurrence


def test_calculate_last_occurrence_min(temperature_timeseries):
    current_temperature = 10
    expected_last_occurrence = 2019

    actual_last_occurrence = calculate_last_occurrence(
        current_value=current_temperature,
        historical_data=temperature_timeseries,
        mode=ReturnPeriodMode.MIN
    )

    assert expected_last_occurrence == actual_last_occurrence


def test_calculate_last_occurrence_min_never(temperature_timeseries):
    current_temperature = 0
    expected_last_occurrence = 'Never'

    actual_last_occurrence = calculate_last_occurrence(
        current_value=current_temperature,
        historical_data=temperature_timeseries,
        mode=ReturnPeriodMode.MIN
    )

    assert expected_last_occurrence == actual_last_occurrence


def test_calculate_last_occurrence_max_never(temperature_timeseries):
    current_temperature = 40
    expected_last_occurrence = 'Never'

    actual_last_occurrence = calculate_last_occurrence(
        current_value=current_temperature,
        historical_data=temperature_timeseries,
        mode=ReturnPeriodMode.MAX
    )

    assert expected_last_occurrence == actual_last_occurrence
