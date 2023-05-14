from typing import List
from datetime import datetime

import uvicorn
from fastapi import FastAPI
import xarray as xr
from matplotlib import pyplot as plt
from pydantic import BaseModel
import numpy as np
import io
from PIL import Image

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


async def plot_timeseries(temperature_at_position, mean_temperature):
    fig, ax = plt.subplots()
    ax.plot(temperature_at_position.time.dt.year, temperature_at_position, color='navy')
    ax.axhline(mean_temperature, color='grey', linestyle='--')
    ax.set_xlabel('Year')
    ax.set_ylabel('LocationData [°C]')

    # save to array
    # fig.canvas.draw()
    # image_from_plot = np.array(fig.canvas.renderer.buffer_rgba()).tolist()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    im = Image.open(buf)

    return im


async def get_position_timeseries(coordinate, temperature, variable):
    dt_object = datetime.fromtimestamp(coordinate.timestamp)
    temperature_at_position = temperature[variable].sel(latitude=coordinate.latitude, longitude=coordinate.longitude,
                                                        time=(temperature[variable].time.dt.month == dt_object.month) &
                                                             (temperature[variable].time.dt.day == dt_object.day),
                                                        method='nearest')
    return temperature_at_position



@app.post("/daily")
async def daily(coordinate: Coordinate):
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    mean_temperature = float(temperature_at_position.mean('time').values)
    timeseries_image = await plot_timeseries(temperature_at_position, mean_temperature)
    return {'average_temperature': mean_temperature, 'timeseries_image':timeseries_image}


@app.post("/dummy")
async def dummy(coordinate: Coordinate):
    return coordinate


if __name__ == '__main__':
    temperature_cache = read_data()
    uvicorn.run(app, host='0.0.0.0', port=8000)
