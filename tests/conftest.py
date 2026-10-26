"""Общие настройки тестов: поднимаем сайт на компьютере, чтобы тесты проверяли текущий код, а не живой сайт."""

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

SITE_ROOT = Path(__file__).resolve().parent.parent


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def site_url():
    """Запускает простой веб-сервер Python в папке сайта на всё время тестов."""
    port = _free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=SITE_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    # Ждём, пока сервер начнёт принимать соединения (обычно доли секунды).
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.1).close()
            break
        except OSError:
            time.sleep(0.1)
    yield url
    server.terminate()
