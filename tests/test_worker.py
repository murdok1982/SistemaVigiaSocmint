import pytest
from src.worker import WorkerSettings, run_analysis_worker

class TestWorker:
    def test_worker_settings_exists(self):
        assert hasattr(WorkerSettings, "functions")
        assert run_analysis_worker in WorkerSettings.functions

    def test_worker_settings_redis(self):
        assert hasattr(WorkerSettings, "redis_settings")
        assert WorkerSettings.max_jobs == 10
        assert WorkerSettings.job_timeout == 300
