"""In-memory asynchronous task execution queue with worker thread pooling."""

from __future__ import annotations
import concurrent.futures
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from agent.orchestrator import Orchestrator, TaskRunReport


class QueueTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    goal: str
    status: str = "pending"  # pending, running, completed, failed
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskQueue:
    """Thread-safe task execution queue for asynchronous agent workloads."""

    def __init__(self, orchestrator: Orchestrator, max_workers: int = 2):
        self.orchestrator = orchestrator
        self.max_workers = max_workers
        self.tasks: Dict[str, QueueTask] = {}
        self._lock = threading.Lock()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, goal: str, use_memory: bool = True, use_reflection: bool = True) -> QueueTask:
        """Submits a new task to the queue for background execution."""
        task = QueueTask(goal=goal)
        with self._lock:
            self.tasks[task.task_id] = task

        self.executor.submit(self._run_task, task.task_id, goal, use_memory, use_reflection)
        return task

    def _run_task(self, task_id: str, goal: str, use_memory: bool, use_reflection: bool):
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "running"
                self.tasks[task_id].started_at = time.time()

        try:
            report: TaskRunReport = self.orchestrator.run_task(
                goal=goal,
                use_memory=use_memory,
                use_reflection=use_reflection,
            )
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "completed"
                    self.tasks[task_id].completed_at = time.time()
                    self.tasks[task_id].result = {
                        "passed": report.passed,
                        "score": report.verdict.score,
                        "answer": report.execution.answer,
                        "steps": report.execution.total_steps,
                        "tokens": report.execution.total_tokens,
                    }
        except Exception as e:
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "failed"
                    self.tasks[task_id].completed_at = time.time()
                    self.tasks[task_id].error = str(e)

    def get_task(self, task_id: str) -> Optional[QueueTask]:
        with self._lock:
            return self.tasks.get(task_id)

    def list_tasks(self, limit: int = 50) -> List[QueueTask]:
        with self._lock:
            sorted_tasks = sorted(self.tasks.values(), key=lambda t: t.created_at, reverse=True)
            return sorted_tasks[:limit]

    def shutdown(self, wait: bool = False):
        self.executor.shutdown(wait=wait)
