import io

from PIL import Image
from matplotlib import pyplot as plt


async def plot_timeseries(temperature_at_position, mean_temperature):
    fig, ax = plt.subplots()
    ax.plot(temperature_at_position.time.dt.year, temperature_at_position, color='navy')
    ax.axhline(mean_temperature, color='grey', linestyle='--')
    ax.set_xlabel('Year')
    ax.set_ylabel('LocationData [°C]')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    im = Image.open(buf)
    with io.BytesIO() as buf:
        im.save(buf, format='PNG')
        im_bytes = buf.getvalue()
    return im_bytes
