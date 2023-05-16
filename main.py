import uvicorn
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from src.extract_timeseries import get_historical_timeseries
from src.calculations import calculate_mean_value_current_value_and_rp
from src.api_request import get_forecast_and_historical_data

app = FastAPI()


class Coordinate(BaseModel):
    timestamp: int
    latitude: float
    longitude: float


@app.get("/temperature")
async def get_daily_average_temperature(coordinate: Coordinate = Depends()):
    # get forecast and historical temperature data
    forecast_temperature, historical_temperature = await get_forecast_and_historical_data(
        coordinate=coordinate,
        variable='temperature_2m_max',
        models='era5_land'
    )

    # get daily, weekly and monthly historical data
    daily_historical_temperature, weekly_historical_temperature, monthly_historical_temperature = \
        await get_historical_timeseries(coordinate, historical_temperature)

    # Daily
    daily_mean_temperature, daily_return_period, daily_current_temperature = \
        await calculate_mean_value_current_value_and_rp(
            daily_historical_temperature,
            forecast_temperature,
            coordinate,
            timeframe='daily'
        )

    # Weekly
    weekly_mean_temperature, weekly_return_period, weekly_current_temperature = \
        await calculate_mean_value_current_value_and_rp(
            weekly_historical_temperature,
            forecast_temperature,
            coordinate,
            timeframe='weekly'
        )

    # Monthly
    monthly_mean_temperature, monthly_return_period, monthly_current_temperature = \
        await calculate_mean_value_current_value_and_rp(
            monthly_historical_temperature,
            forecast_temperature,
            coordinate,
            timeframe='monthly'
        )

    return {
        'daily_average_temperature': daily_mean_temperature,
        'daily_current_temperature': daily_current_temperature,
        'daily_return_period_temperature': daily_return_period,
        'daily_historical_temperature': list(daily_historical_temperature.values.squeeze()),
        'daily_historical_index': list(daily_historical_temperature.index),
        'weekly_average_temperature': weekly_mean_temperature,
        'weekly_current_temperature': weekly_current_temperature,
        'weekly_return_period_temperature': weekly_return_period,
        'weekly_historical_temperature': list(weekly_historical_temperature.values.squeeze()),
        'weekly_historical_index': list(weekly_historical_temperature.index),
        'monthly_average_temperature': monthly_mean_temperature,
        'monthly_current_temperature': monthly_current_temperature,
        'monthly_return_period_temperature': monthly_return_period,
        'monthly_historical_temperature': list(monthly_historical_temperature.values.squeeze()),
        'monthly_historical_index': list(monthly_historical_temperature.index)
    }


@app.get("/precipitation")
async def get_precipitation(coordinate: Coordinate = Depends()):
    # get forecast and historical temperature data
    forecast_precipitation, historical_precipitation = await get_forecast_and_historical_data(
        coordinate=coordinate,
        variable='precipitation_sum',
        models='era5'
    )

    # get daily, weekly and monthly historical data
    daily_historical_precipitation, weekly_historical_precipitation, monthly_historical_precipitation = \
        await get_historical_timeseries(coordinate, historical_precipitation)

    # daily
    daily_mean_precipitation, daily_return_period, daily_current_precipitation = \
        await calculate_mean_value_current_value_and_rp(
            daily_historical_precipitation,
            forecast_precipitation,
            coordinate,
            timeframe='daily'
        )

    # weekly
    weekly_mean_precipitation, weekly_return_period, weekly_current_precipitation = \
        await calculate_mean_value_current_value_and_rp(
            weekly_historical_precipitation,
            forecast_precipitation,
            coordinate,
            timeframe='weekly'
        )

    # monthly
    monthly_mean_precipitation, monthly_return_period, monthly_current_precipitation = \
        await calculate_mean_value_current_value_and_rp(
            monthly_historical_precipitation,
            forecast_precipitation,
            coordinate,
            timeframe='monthly'
        )

    return {
        'daily_average_precipitation': daily_mean_precipitation,
        'daily_current_precipitation': daily_current_precipitation,
        'daily_return_period_precipitation': daily_return_period,
        'daily_historical_precipitation': list(daily_historical_precipitation.values.squeeze()),
        'daily_historical_index': list(daily_historical_precipitation.index),
        'weekly_average_precipitation': weekly_mean_precipitation,
        'weekly_current_precipitation': weekly_current_precipitation,
        'weekly_return_period_precipitation': weekly_return_period,
        'weekly_historical_precipitation': list(weekly_historical_precipitation.values.squeeze()),
        'weekly_historical_index': list(weekly_historical_precipitation.index),
        'monthly_average_precipitation': monthly_mean_precipitation,
        'monthly_current_precipitation': monthly_current_precipitation,
        'monthly_return_period_precipitation': monthly_return_period,
        'monthly_historical_precipitation': list(monthly_historical_precipitation.values.squeeze()),
        'monthly_historical_index': list(monthly_historical_precipitation.index),
    }


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)
