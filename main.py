import uvicorn
from fastapi import FastAPI

from src.api import precipitation, temperature

app = FastAPI()

app.include_router(temperature.router, prefix='/temperature')
app.include_router(precipitation.router, prefix='/precipitation')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)
