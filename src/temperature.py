from datetime import datetime


async def get_position_timeseries(coordinate, temperature, variable):
    dt_object = datetime.fromtimestamp(coordinate.timestamp)
    temperature_at_position = temperature[variable].sel(latitude=coordinate.latitude, longitude=coordinate.longitude,
                                                        time=(temperature[variable].time.dt.month == dt_object.month) &
                                                             (temperature[variable].time.dt.day == dt_object.day),
                                                        method='nearest')
    return temperature_at_position


