import uvicorn
from fastapi import FastAPI, Depends
import xarray as xr
from fastapi import Response
from pydantic import BaseModel

from src.temperature import get_position_timeseries
from src.temperature_plot import plot_timeseries
from src.return_periods import calculate_return_period

app = FastAPI()


class Coordinate(BaseModel):
    timestamp: int
    latitude: float
    longitude: float
    temperature: float = 20


def read_data():
    path = r'C:\Users\jakob\3D Objects\E_obs'
    file1 = r'\tn_ens_mean_0.1deg_reg_v27.0e.nc'
    file2 = r'\tx_ens_mean_0.1deg_reg_v27.0e.nc'
    file3 = r'\tg_ens_mean_0.1deg_reg_v27.0e.nc'

    temperature_min = xr.open_dataarray(path + file1)
    temperature_max = xr.open_dataarray(path + file2)
    temperature_mean = xr.open_dataarray(path + file3)

    return {'max': temperature_max, 'mean': temperature_mean, 'min': temperature_min}


@app.get("/average_temperature/daily")
async def get_daily_average_temperature(coordinate: Coordinate = Depends()):
    # get temperature data at position
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')

    # calculate average temperature over the whole timeseries
    mean_temperature = float(temperature_at_position.mean('time').values)

    # calculate return period of actual temperature
    if coordinate.temperature > mean_temperature:
        return_period = calculate_return_period(temperature_at_position, coordinate.temperature, mode='max')
    elif coordinate.temperature < mean_temperature:
        return_period = calculate_return_period(temperature_at_position, coordinate.temperature, mode='min')
    else:
        return_period = 2  # if temperatures are the same cdf=0.5 which gives rp=2

    return {'average_temperature': mean_temperature, 'return_period': return_period}


@app.get("/image/daily")
async def get_daily_image(coordinate: Coordinate = Depends()):
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    mean_temperature = float(temperature_at_position.mean('time').values)
    im_bytes = await plot_timeseries(temperature_at_position, mean_temperature)
    headers = {'Content-Disposition': 'inline; filename="timeseries.png"'}
    return Response(im_bytes, headers=headers, media_type='image/png')


if __name__ == '__main__':
    temperature_cache = read_data()
    uvicorn.run(app, host='0.0.0.0', port=8000)
