from xclim.indices.stats import fit, parametric_cdf


# %% calculate single RP
def calculate_return_period(temperature_timeseries, actual_temperature, mode='max'):
    """
    Computes the value of the return period for the actual temperature
    :param temperature_timeseries: days in years timeseries at location in °C
    :param actual_temperature: daily temperature in °C
    :param mode: str, indicates whether extreme minima or maxima are investigated.
     For exceedance of mean temperature choose 'max', else choose 'min'.
    :return: return period in years
    """
    params = fit(temperature_timeseries, dist='genextreme')
    cdf = parametric_cdf(params, actual_temperature)
    if mode == 'max':
        return_period = 1 / (1 - cdf.values[0])
    elif mode == 'min':
        return_period = 1 / cdf.values[0]
    else:
        return_period = False
    return return_period
