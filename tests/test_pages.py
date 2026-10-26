"""Все страницы на всех ключевых ширинах: без ошибок, без ответов 4xx, страница не сдвигается вбок.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page

from conftest import ALL_PAGES, ALL_WIDTHS, viewport


@pytest.mark.parametrize("width", ALL_WIDTHS)
@pytest.mark.parametrize("path", ALL_PAGES)
def test_page_has_no_errors_and_fits_the_screen(page: Page, site_url, page_problems, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    # Печать «тесты пройдены» начинает анимацию увеличенной вдвое, и раньше в это время страницу
    # можно было сдвинуть вбок (баг найден на 768–1280 px). Окно короткое и зависит от задержек
    # анимации, поэтому пробуем несколько раз за первые 1,5 с, как это сделал бы человек:
    # прокруткой колесом или тачпадом вбок.
    page.mouse.move(width / 2, 300)
    for _ in range(10):
        page.mouse.wheel(500, 0)
        page.wait_for_timeout(150)
        assert page.evaluate("scrollX") == 0, "страницу можно сдвинуть вбок"
        assert page.evaluate("innerHeight - document.documentElement.clientHeight") == 0, "внизу появилась полоса прокрутки"

    assert not page_problems["console"], f"ошибки в консоли: {page_problems['console']}"
    assert not page_problems["responses"], f"ответы с ошибкой: {page_problems['responses']}"
