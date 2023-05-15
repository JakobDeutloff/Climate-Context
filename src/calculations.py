from datetime import datetime, timedelta
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


async def calculate_mean_value_current_value_and_rp(historical_values, forecast_values, coordinate, timeframe):

    # get date
    date = datetime.fromtimestamp(coordinate.timestamp)
    date_string = date.strftime('%Y-%m-%d')

    # Claculate current temperature
    if timeframe == 'daily':
        current_value = float(forecast_values.loc[date_string].values)
    elif timeframe == 'weekly':
        date_last_week = date - timedelta(days=6)
        date_last_week_string = date_last_week.strftime('%Y-%m-%d')
        current_value = float(forecast_values.loc[date_last_week_string:date_string].mean().values)
    elif timeframe == 'monthly':
        date_last_month = date - timedelta(days=30)
        date_last_month_string = date_last_month.strftime('%Y-%m-%d')
        current_value = float(forecast_values.loc[date_last_month_string:date_string].mean().values)
    else:
        current_value = []

    # calculate average temperature over the whole timeseries
    mean_historical_value = float(historical_values.mean().values)

    # calculate return period of actual temperature
    if current_value > mean_historical_value:
        return_period = await calculate_return_period(historical_values, current_value, mode='max')
    elif current_value < mean_historical_value:
        return_period = await calculate_return_period(historical_values, current_value, mode='min')
    else:
        return_period = 2  # if temperatures are the same cdf=0.5 which gives rp=2

    return mean_historical_value, return_period, current_value
