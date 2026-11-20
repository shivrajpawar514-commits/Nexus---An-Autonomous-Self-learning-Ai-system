"""Unit and concurrency tests for TaskQueue asynchronous execution."""

import time
import pytest
from agent.llm import MockLLM
from agent.orchestrator import Orchestrator
from agent.queue import TaskQueue, QueueTask


def test_queue_submit_and_polling():
    llm = MockLLM()
    orch = Orchestrator(llm=llm)
    queue = TaskQueue(orchestrator=orch, max_workers=2)

    try:
        task = queue.submit(goal="Calculate 15 * 4 + 10")
        assert isinstance(task, QueueTask)
        assert task.status in ("pending", "running", "completed")

        # Wait for task completion
        timeout = 5.0
        start = time.time()
        while time.time() - start < timeout:
            current = queue.get_task(task.task_id)
            if current and current.status == "completed":
                break
            time.sleep(0.05)

        finished = queue.get_task(task.task_id)
        assert finished is not None
        assert finished.status == "completed"
        assert finished.result is not None
        assert finished.result["passed"] is True
        assert "70" in str(finished.result["answer"])
    finally:
        queue.shutdown(wait=False)


def test_queue_task_listing():
    llm = MockLLM()
    orch = Orchestrator(llm=llm)
    queue = TaskQueue(orchestrator=orch, max_workers=1)

    try:
        t1 = queue.submit("Goal 1")
        t2 = queue.submit("Goal 2")

        tasks = queue.list_tasks(limit=10)
        assert len(tasks) >= 2
        task_ids = [t.task_id for t in tasks]
        assert t1.task_id in task_ids
        assert t2.task_id in task_ids
    finally:
        queue.shutdown(wait=False)
