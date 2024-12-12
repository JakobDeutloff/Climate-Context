from fastapi import Depends, APIRouter

from src.definitions import WeatherVariable, Coordinate, WeatherModel, WeatherVariableName
from src.calculate_statistics import get_weather_variable_data


router = APIRouter()


@router.get("/")
async def get_daily_average_temperature(coordinate: Coordinate = Depends()):
    return get_weather_variable_data(
        coordinate=coordinate,
        weather_model=WeatherModel.ERA5,
        weather_variable=WeatherVariable.TEMPERATURE,
        weather_variable_name=WeatherVariableName.TEMPERATURE
    )
