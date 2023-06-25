from enum import Enum

from pydantic import BaseModel


class ReturnPeriodMode(Enum):
    MIN = 'min'
    MAX = 'max'


class WeatherVariable(Enum):
    TEMPERATURE = 'temperature_2m_max'
    PRECIPITATION = 'precipitation_sum'


class WeatherVariableName(Enum):
    TEMPERATURE = 'temperature'
    PRECIPITATION = 'precipitation'


class TimeFrame(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


class WeatherModel(Enum):
    ERA5 = 'era5'
    ERA5_LAND = 'era5_land'


class Coordinate(BaseModel):
    timestamp: int
    latitude: float
    longitude: float
