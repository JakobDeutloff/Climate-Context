import io

from PIL import Image
from matplotlib import pyplot as plt


async def plot_timeseries(temperature_at_position, mean_temperature):
    with plt.rc_context({'axes.edgecolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'}):
        fig, ax = plt.subplots()
        ax.plot(temperature_at_position.time.dt.year, temperature_at_position, color='white')
        ax.axhline(mean_temperature, color='white', linestyle='--')
        ax.set_xlabel('Year')
        ax.set_ylabel('Temperature [°C]')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
    im = Image.open(buf)
    with io.BytesIO() as buf:
        im.save(buf, format='PNG')
        im_bytes = buf.getvalue()
    return im_bytes
