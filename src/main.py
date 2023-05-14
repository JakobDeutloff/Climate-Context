import uvicorn
from fastapi import FastAPI
import xarray as xr
from fastapi import Response
from pydantic import BaseModel

from src.temperature import get_position_timeseries
from src.temperature_plot import plot_timeseries

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


@app.post("/average_temperature/daily")
async def post_daily_average_temperature(coordinate: Coordinate):
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    mean_temperature = float(temperature_at_position.mean('time').values)
    return {'average_temperature': mean_temperature}


@app.post("/image/daily")
async def post_daily_image(coordinate: Coordinate):
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    mean_temperature = float(temperature_at_position.mean('time').values)
    im_bytes = await plot_timeseries(temperature_at_position, mean_temperature)
    headers = {'Content-Disposition': 'inline; filename="timeseries.png"'}
    return Response(im_bytes, headers=headers, media_type='image/png')


if __name__ == '__main__':
    temperature_cache = read_data()
    uvicorn.run(app, host='0.0.0.0', port=8000)
