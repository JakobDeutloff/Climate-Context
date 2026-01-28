import uvicorn
from uvicorn.config import LOGGING_CONFIG
from fastapi import FastAPI

from src.api import precipitation, temperature

app = FastAPI()

app.include_router(temperature.router, prefix='/temperature')
app.include_router(precipitation.router, prefix='/precipitation')


if __name__ == '__main__':
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"] = '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=80,
        log_level='info',
    )
