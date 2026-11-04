"""
Background Scheduler for Automated Data Refresh and Forecast Updates.
"""

import asyncio
import logging
import os
from typing import Optional

from src.database.connection import SessionLocal
from src.services.data_ingestion import DataIngestionService
from src.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL_SECONDS", 1800))  # Default 30 min


class DataRefreshScheduler:
    def __init__(self, interval_seconds: int = REFRESH_INTERVAL_SECONDS):
        self.interval = interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.ingestion_service = DataIngestionService()
        self.prediction_service = PredictionService.get_instance()

    async def _loop(self):
        logger.info(f"Background refresh scheduler started (interval: {self.interval}s)")
        while self.is_running:
            try:
                db = SessionLocal()
                try:
                    logger.info("Executing scheduled external data refresh...")
                    refresh_res = await self.ingestion_service.refresh_all_sources(db)
                    logger.info(f"Refresh completed: {refresh_res.get('stations_processed')} stations processed.")

                    # Run predictions for primary stations (e.g., Sri Rangam, Upper Anicut, Bhavani, Mettur)
                    key_stations = [23, 28, 1, 14]
                    for sid in key_stations:
                        try:
                            self.prediction_service.run_prediction(station_id=sid, db=db)
                        except Exception as pe:
                            logger.warning(f"Scheduled prediction skipped for station {sid}: {pe}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in scheduler execution loop: {e}")

            # Sleep until next cycle
            await asyncio.sleep(self.interval)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Background refresh scheduler stopped.")
