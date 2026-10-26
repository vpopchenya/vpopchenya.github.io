"""Появление секций при прокрутке и страховка на случай, если main.js не загрузился.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page

from conftest import HOME_PAGES, viewport

SECTIONS = ["section-what", "section-prices", "section-works", "section-about", "section-order", "section-contacts"]


def section_opacities(page: Page):
    return {test_id: page.get_by_test_id(test_id).evaluate("el => getComputedStyle(el).opacity") for test_id in SECTIONS}


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("path", HOME_PAGES)
def test_every_section_appears_while_scrolling(page: Page, site_url, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    height = page.evaluate("document.documentElement.scrollHeight")
    # На сайте плавная прокрутка; в тесте прыгаем мгновенно, иначе страница не успевает докрутиться.
    for y in range(0, height, 300):
        page.evaluate("y => window.scrollTo({top: y, behavior: 'instant'})", y)
        page.wait_for_timeout(80)
    page.wait_for_timeout(900)  # секция выезжает 0,7 с
    hidden = {k: v for k, v in section_opacities(page).items() if v != "1"}
    assert not hidden, f"секции не появились: {hidden}"


@pytest.mark.parametrize("path", HOME_PAGES)
def test_sections_appear_even_without_main_js(page: Page, site_url, path):
    # Если main.js не загрузился, CSS-страховка показывает все секции через 2,5 с.
    page.route("**/main.js", lambda route: route.abort())
    page.goto(site_url + path)
    page.wait_for_timeout(3200)
    hidden = {k: v for k, v in section_opacities(page).items() if v != "1"}
    assert not hidden, f"без main.js секции остались скрытыми: {hidden}"
