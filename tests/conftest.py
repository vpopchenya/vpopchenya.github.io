"""Общие настройки тестов: поднимаем сайт на компьютере, чтобы тесты проверяли текущий код, а не живой сайт."""

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

SITE_ROOT = Path(__file__).resolve().parent.parent

# Ключевые ширины: основные экраны и обе стороны каждой точки перестройки вёрстки в CSS (900 и 760 px).
# Ошибки вёрстки чаще всего прячутся как раз на этих границах.
ALL_WIDTHS = [1920, 1280, 901, 900, 768, 761, 760, 390]
HOME_PAGES = ["/", "/en/"]
# 404 открываем напрямую: python -m http.server не отдаёт нашу 404.html на несуществующий адрес.
ALL_PAGES = HOME_PAGES + ["/privacy/", "/en/privacy/", "/404.html"]
_HEIGHTS = {1920: 1080, 390: 844}


def viewport(width):
    """Размер окна для ширины: типичная высота экрана такой ширины."""
    return {"width": width, "height": _HEIGHTS.get(width, 900)}


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


@pytest.fixture
def page_problems(page):
    """Собирает ошибки страницы: ошибки в консоли (в том числе нарушения CSP) и ответы 4xx/5xx.

    Подписка ставится до page.goto, поэтому ловит и то, что случается при загрузке.
    """
    problems = {"console": [], "responses": []}
    page.on("console", lambda msg: msg.type == "error" and problems["console"].append(msg.text))
    page.on("pageerror", lambda err: problems["console"].append(str(err)))
    page.on("response", lambda r: r.status >= 400 and problems["responses"].append(f"{r.status} {r.url}"))
    return problems
