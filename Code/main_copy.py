from typing import Dict

import uvicorn
from fastapi import FastAPI
import xarray as xr
from matplotlib import pyplot as plt
from pydantic import BaseModel
from datetime import datetime
import numpy as np
from fastapi import Response
from PIL import Image
import io

from xarray import DataArray

app = FastAPI()


class Coordinate(BaseModel):
    timestamp: int
    latitude: float
    longitude: float


class LocationData(BaseModel):
    average_temperature: float
    timeseries_image: bytes


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
    ax.plot(temperature_at_position.time.dt.years, temperature_at_position, color='navy')
    ax.axhline(mean_temperature, color='grey', linestyle='--')
    ax.set_xlabel('Year')
    ax.set_ylabel('LocationData [°C]')

    # save to array
    image_from_plot = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    image_from_plot = image_from_plot.reshape(fig.canvas.get_width_height()[::-1] + (3,))

    return image_from_plot


async def get_position_timeseries(coordinate, temperature, variable):
    dt_object = datetime.fromtimestamp(coordinate.timestamp)
    temperature_at_position = temperature[variable].sel(latitude=coordinate.latitude, longitude=coordinate.longitude,
                                                        time=(temperature[variable].time.dt.month == dt_object.month) &
                                                             (temperature[variable].time.dt.day == dt_object.day),
                                                        method='nearest')
    return temperature_at_position


async def buffer_image(image):

    # save image to an in-memory bytes buffer
    im = Image.fromarray(image)
    with io.BytesIO() as buf:
        im.save(buf, format='PNG')
        im_bytes = buf.getvalue()

    return im_bytes


@app.post("/daily")
async def daily(coordinate: Coordinate):
    temperature_at_position = await get_position_timeseries(coordinate, temperature_cache, 'max')
    mean_temperature = float(temperature_at_position.mean('time').values)
    timeseries_image = plot_timeseries(temperature_at_position, mean_temperature)
    image_buffered = buffer_image(timeseries_image)
    return LocationData(average_temperature=mean_temperature, timeseries_image=image_buffered)

@app.post("/dummy")
async def dummy(coordinate: Coordinate):
    return coordinate


if __name__ == '__main__':
    temperature_cache = read_data()
    uvicorn.run(app, host='0.0.0.0', port=7000)
