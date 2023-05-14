import uvicorn
from fastapi import FastAPI, Depends
import xarray as xr
from fastapi import Response
from pydantic import BaseModel
from datetime import datetime, timedelta
from src.temperature_timeseries import get_historical_timeseries
from src.temperature_plot import plot_timeseries, plot_histogram
from src.calculations import calculate_mean_temp_and_rp
from src.api_request import get_forecast_and_historical_data

app = FastAPI()


class Coordinate(BaseModel):
    timestamp: int
    latitude: float
    longitude: float


def read_data():
    path = r'C:\Users\jakob\3D Objects\E_obs'
    file1 = r'\tn_ens_mean_0.1deg_reg_v27.0e.nc'
    file2 = r'\tx_ens_mean_0.1deg_reg_v27.0e.nc'
    file3 = r'\tg_ens_mean_0.1deg_reg_v27.0e.nc'

    temperature_min = xr.open_dataarray(path + file1)
    temperature_max = xr.open_dataarray(path + file2)
    temperature_mean = xr.open_dataarray(path + file3)

    return {'max': temperature_max, 'mean': temperature_mean, 'min': temperature_min}


@app.get("/temperature/daily")
async def get_daily_average_temperature(coordinate: Coordinate = Depends()):

    # get forecast and historical temperature data
    forecast_temperature, historical_temperature = await get_forecast_and_historical_data(coordinate=coordinate)

    # get daily, weekly and monthly data
    daily_historical_temperature, weekly_historical_temperature, monthly_historical_temperature = \
        get_historical_timeseries(coordinate, historical_temperature)

    # -----------------------------------------------------------------------------------------------------------------
    # DAILY
    # -----------------------------------------------------------------------------------------------------------------

    # get date
    date = datetime.fromtimestamp(coordinate.timestamp)
    date_string = date.strftime('%Y-%m-%d')

    daily_current_temperature = float(forecast_temperature.loc[date_string].values)

    daily_mean_temperature, daily_return_period = await calculate_mean_temp_and_rp(
        daily_historical_temperature,
        daily_current_temperature,
        coordinate
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Weekly
    # -----------------------------------------------------------------------------------------------------------------

    # date a week ago
    date_last_week = date - timedelta(days=6)
    date_last_week_string = date_last_week.strftime('%Y-%m-%d')

    weekly_current_temperature = float(forecast_temperature.loc[date_last_week_string:date_string].mean().values)

    weekly_mean_temperature, weekly_return_period = await calculate_mean_temp_and_rp(
        weekly_historical_temperature,
        weekly_current_temperature,
        coordinate
    )

    # -----------------------------------------------------------------------------------------------------------------
    # monthly
    # -----------------------------------------------------------------------------------------------------------------

    # date a month ago
    date_last_month = date - timedelta(days=30)
    date_last_month_string = date_last_week.strftime('%Y-%m-%d')

    monthly_current_temperature = float(forecast_temperature.loc[date_last_month_string:date_string].mean().values)

    monthly_mean_temperature, monthly_return_period = await calculate_mean_temp_and_rp(
        monthly_historical_temperature,
        monthly_current_temperature,
        coordinate
    )


    return {
        'daily_average_temperature': daily_mean_temperature,
        'daily_current_temperature': daily_current_temperature,
        'daily_return_period': daily_return_period,
        'weekly_average_temperature': weekly_mean_temperature,
        'weekly_current_temperature': weekly_current_temperature,
        'weekly_return_period': weekly_return_period,
        'monthly_average_temperature': monthly_mean_temperature,
        'monthly_current_temperature': monthly_current_temperature,
        'monthly_return_period': monthly_return_period
    }


@app.get("/image/temperature/daily/timeseries")
async def get_daily_temperature_timeseries(coordinate: Coordinate = Depends()):
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    mean_temperature = float(temperature_at_position.mean('time').values)
    im_bytes = await plot_timeseries(temperature_at_position, mean_temperature)
    headers = {'Content-Disposition': 'inline; filename="timeseries.png"'}
    return Response(im_bytes, headers=headers, media_type='image/png')

@app.get("/image/temperature/daily/histogram")
async def get_daily_temperature_histogram(coordinate: Coordinate = Depends()):
    # Get historical timeseries
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    # Get current temperature
    forecast_temperature = await get_forecast_data(coordinate)
    date = datetime.fromtimestamp(coordinate.timestamp)
    date_string = date.strftime('%Y-%m-%d')
    current_temperature = forecast_temperature.loc[date_string].values[0]
    # Plot
    im_bytes = await plot_histogram(temperature_at_position, current_temperature)
    headers = {'Content-Disposition': 'inline; filename="histogram.png"'}
    return Response(im_bytes, headers=headers, media_type='image/png')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
