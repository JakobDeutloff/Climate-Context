from datetime import datetime
from xclim.indices.stats import fit, parametric_cdf



async def calculate_return_period(temperature_timeseries, actual_temperature, mode='max'):
    """
    Computes the value of the return period for the actual temperature
    :param temperature_timeseries: days in years timeseries at location in °C
    :param actual_temperature: daily temperature in °C
    :param mode: str, indicates whether extreme minima or maxima are investigated.
     For exceedance of mean temperature choose 'max', else choose 'min'.
    :return: return period in years
    """
    # To xarray
    temperature_timeseries.index.name = 'time'
    temperature_timeseries_xr = temperature_timeseries.to_xarray()
    variable = list(temperature_timeseries_xr.keys())[0]
    temperature_timeseries_xr = temperature_timeseries_xr[variable]

    params = fit(temperature_timeseries_xr, dist='genextreme')
    cdf = parametric_cdf(params, actual_temperature)
    if mode == 'max':
        return_period = 1 / (1 - cdf.values[0])
    elif mode == 'min':
        return_period = 1 / cdf.values[0]
    else:
        return_period = False
    return return_period


async def calculate_mean_temp_and_rp(historical_temperature, forecast_temperature, coordinate):
    # calculate average temperature over the whole timeseries
    mean_temperature = float(historical_temperature.mean().values)

    # calculate return period of actual temperature
    if forecast_temperature > mean_temperature:
        return_period = await calculate_return_period(historical_temperature, forecast_temperature, mode='max')
    elif forecast_temperature < mean_temperature:
        return_period = await calculate_return_period(historical_temperature, forecast_temperature, mode='min')
    else:
        return_period = 2  # if temperatures are the same cdf=0.5 which gives rp=2

    return mean_temperature, return_period
