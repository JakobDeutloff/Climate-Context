import uvicorn
from fastapi import FastAPI, Depends
import xarray as xr
from fastapi import Response
from pydantic import BaseModel
from datetime import datetime

from src.temperature import get_position_timeseries
from src.temperature_plot import plot_timeseries, plot_histogram
from src.return_periods import calculate_return_period
from src.api_request import get_forecast_data

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
    # get date
    date = datetime.fromtimestamp(coordinate.timestamp)
    date_string = date.strftime('%Y-%m-%d')

    # get forecast temperature data
    forecast_temperature = await get_forecast_data(coordinate)

    # get temperature data at position
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')

    # calculate average temperature over the whole timeseries
    mean_temperature = float(temperature_at_position.mean('time').values)

    # calculate return period of actual temperature
    if forecast_temperature.loc[date_string].values[0] > mean_temperature:
        return_period = await calculate_return_period(temperature_at_position,
                                                      forecast_temperature.loc[date_string], mode='max')
    elif forecast_temperature.loc[date_string].values[0] < mean_temperature:
        return_period = await calculate_return_period(temperature_at_position,
                                                      forecast_temperature.loc[date_string], mode='min')
    else:
        return_period = 2  # if temperatures are the same cdf=0.5 which gives rp=2

    return {
        'average_temperature': mean_temperature,
        'todays_temperature': forecast_temperature.loc[date_string].values[0],
        'return_period': return_period
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
    temperature_cache = read_data()
    uvicorn.run(app, host='0.0.0.0', port=8000)
