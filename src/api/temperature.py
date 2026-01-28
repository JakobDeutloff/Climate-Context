from fastapi import Depends, APIRouter

from src.definitions import WeatherVariable, Coordinate, WeatherModel, WeatherVariableName
from src.calculate_statistics import get_weather_variable_data
import logging
logger = logging.getLogger('uvicorn.error')

router = APIRouter()


@router.get("")
async def get_daily_average_temperature(coordinate: Coordinate = Depends()):
    logger.info('Entering get_temperature.')
    weather_variable_data = get_weather_variable_data(
        coordinate=coordinate,
        weather_model=WeatherModel.ERA5,
        weather_variable=WeatherVariable.TEMPERATURE,
        weather_variable_name=WeatherVariableName.TEMPERATURE
    )
    logger.info(f"Sending precipitation data.")
    return weather_variable_data
