import os
import time

from arq.connections import RedisSettings
from prometheus_client import Counter, Histogram, start_http_server


WORKER_JOBS_PROCESSED = Counter(
    "vigia_worker_jobs_processed_total",
    "Total jobs processed by the worker",
    ["job_name", "status"],
)
WORKER_JOB_DURATION = Histogram(
    "vigia_worker_job_duration_seconds",
    "Time spent processing a worker job",
    ["job_name"],
)

try:
    start_http_server(9101)
except Exception:
    pass


async def run_analysis_worker(ctx, objective: str, platforms: list[str], max_results: int, analyst_id: str):
    job_name = "run_analysis_worker"
    start = time.monotonic()
    try:
        from src.orchestrator import VigiaOrchestrator
        from src.database import async_session
        async with async_session() as db:
            orchestrator = VigiaOrchestrator()
            result = await orchestrator.run_analysis_pipeline(
                objective=objective,
                platforms=platforms,
                max_results=max_results,
                db=db,
                analyst_id=analyst_id,
            )
            WORKER_JOBS_PROCESSED.labels(job_name=job_name, status="success").inc()
            return result.model_dump()
    except Exception:
        WORKER_JOBS_PROCESSED.labels(job_name=job_name, status="error").inc()
        raise
    finally:
        WORKER_JOB_DURATION.labels(job_name=job_name).observe(time.monotonic() - start)


class WorkerSettings:
    functions = [run_analysis_worker]
    redis_settings = RedisSettings(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        password=os.environ.get("REDIS_PASSWORD", ""),
    )
    max_jobs = 10
    job_timeout = 300
