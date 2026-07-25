"""background 模块负责把图片解码、下载、校验与落盘移出 MCP 请求返回路径。"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from .models.common import ImageToolResult

BACKGROUND_ACK_DELAY_SECONDS = 1.0
logger = logging.getLogger(__name__)
_background_threads: set[threading.Thread] = set()
_background_threads_lock = threading.Lock()


def estimate_base64_decoded_size(image_base64: str) -> int:
    """不解码图片，仅根据 base64 字符串长度估算最终二进制文件大小。"""

    _, separator, payload = image_base64.partition(",")
    normalized = payload if separator and image_base64.startswith("data:") else image_base64
    compact = "".join(normalized.split())
    padding = len(compact) - len(compact.rstrip("="))
    return max(0, len(compact) * 3 // 4 - padding)


def _run_persistence_task(task_name: str, persistence: Callable[[], ImageToolResult]) -> None:
    """执行单个后台落盘任务；异常只记录日志，绝不触发第二次上游请求。"""

    try:
        result = persistence()
        logger.info("Background image persistence completed task=%s file=%s", task_name, result.file_path)
    except Exception:
        logger.exception("Background image persistence failed task=%s", task_name)
    finally:
        current_thread = threading.current_thread()
        with _background_threads_lock:
            _background_threads.discard(current_thread)


def schedule_background_persistence(task_name: str, persistence: Callable[[], ImageToolResult]) -> None:
    """启动守护线程后固定等待 1 秒，让 MCP 调用方尽快收到上游完成确认。"""

    thread = threading.Thread(
        target=_run_persistence_task,
        args=(task_name, persistence),
        name=f"image-persist-{task_name}",
        daemon=True,
    )
    with _background_threads_lock:
        _background_threads.add(thread)
    thread.start()
    time.sleep(BACKGROUND_ACK_DELAY_SECONDS)


def wait_for_background_persistence(timeout_seconds: float = 5.0) -> None:
    """等待当前已登记任务结束，供测试与进程优雅收尾使用。"""

    deadline = time.monotonic() + timeout_seconds
    while True:
        with _background_threads_lock:
            threads = list(_background_threads)
        if not threads:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        for thread in threads:
            thread.join(timeout=remaining)