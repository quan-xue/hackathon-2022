from datetime import datetime
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from starlette.middleware.cors import CORSMiddleware

from app.core import config, tasks
from app.background.scrape_onepa import update_onepa_events

import logging
from app.api.routes import router as api_router


def get_application():
    app = FastAPI(title="Kaypoh@Kampung", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    app.include_router(api_router, prefix="/api")

    return app


app = get_application()


@app.on_event("startup")
@repeat_every(seconds=60 * 60 * 24)  # Daily
def update_db_with_onepa_events() -> None:
    start = datetime.now()
    logging.info(f"Running daily update of onepa events at {start}")
    update_onepa_events()
    end = datetime.now()
    seconds = (end - start).seconds
    logging.info(f"Finished daily update of onepa events at {end} after {seconds} seconds")
