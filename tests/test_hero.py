"""Первый экран: заголовок и кнопка видны сразу, а не после анимации (баг #8).

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page, expect

WIDTHS = [390, 768, 1280, 1920]
PAGES = ["/", "/en/"]


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("path", PAGES)
def test_headline_and_button_visible_right_away(page: Page, site_url, path, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(site_url + path)

    # Проверяем сразу после загрузки, без ожидания: раньше здесь была прозрачность 0,
    # и на телефоне первый экран около секунды стоял пустым.
    for test_id in ["hero-title", "hero-order"]:
        element = page.get_by_test_id(test_id)
        expect(element).to_be_visible()
        opacity = element.evaluate("el => getComputedStyle(el.closest('.intro') || el).opacity")
        assert opacity == "1", f"{test_id} на ширине {width}: прозрачность {opacity}"


def test_everything_visible_without_animations(page: Page, site_url):
    # Люди с отключёнными в системе анимациями должны видеть весь первый экран.
    page.emulate_media(reduced_motion="reduce")
    page.goto(site_url + "/")
    for selector in ["h1", ".lead", ".stamp"]:
        opacity = page.locator(selector).evaluate("el => getComputedStyle(el).opacity")
        assert opacity == "1", f"{selector}: прозрачность {opacity}"


def test_no_sideways_scroll_on_phone(page: Page, site_url):
    # Печать начинает анимацию увеличенной вдвое — страница не должна сдвигаться вбок.
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(site_url + "/")
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width <= 390
