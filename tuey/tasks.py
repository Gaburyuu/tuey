import asyncio
import time
import threading
import functools
from huey import SqliteHuey
from .db import get_cached_result, cache_result, log_task, update_task, update_progress, init_db

# Initialize the cache DB.
init_db()

# Initialize Huey (using SQLite as our backend for persistence).
huey = SqliteHuey(filename="huey_tasks.db")

# Use per-function locks to enforce one running task at a time per function.
_locks = {}

def get_lock(func_name):
    if func_name not in _locks:
        _locks[func_name] = threading.Lock()
    return _locks[func_name]

def huey_task(func):
    """
    Decorator to wrap a function as a Huey task with progress & caching.
    Uses update_wrapper to preserve the original function's metadata.
    """
    @huey.task()
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        lock = get_lock(func_name)
        with lock:
            start_time = time.time()
            log_task(func_name, args, start_time, status="IN PROGRESS")
            # Check cache (in case it was run recently).
            cached = get_cached_result(func_name, args)
            if cached is not None:
                return cached
            try:
                # Optionally, the function itself can update progress by calling update_progress().
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = round(end_time - start_time, 2)
                update_task(func_name, args, "SUCCESS", end_time=end_time, duration=duration)
                cache_result(func_name, args, result)
                return result
            except Exception as e:
                end_time = time.time()
                duration = round(end_time - start_time, 2)
                update_task(func_name, args, "FAILED", end_time=end_time, duration=duration, error_message=str(e))
                raise e

    # Use functools.update_wrapper to copy the metadata from the original function.
    functools.update_wrapper(wrapper, func)
    return wrapper

async def run_task(func, args, func_name):
    # If cached, return immediately.
    cached = get_cached_result(func_name, args)
    if cached is not None:
        return cached
    # Otherwise, enqueue the task (it must be decorated with @huey_task).
    task = func(*args)  # Huey handles queuing; extra calls are queued automatically.
    # Wait for the task to complete. (This polling is simplified; you can integrate callbacks as needed.)
    while not task.completed:
        await asyncio.sleep(1)
    return task.get(block=False)

def get_queue_count(func_name):
    # Count pending tasks for this function.
    count = 0
    for task in huey.pending():
        if task.task_name == func_name:
            count += 1
    return count
