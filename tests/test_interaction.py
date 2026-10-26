"""Работа с клавиатуры, наведение и переключение языка.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page, expect

from conftest import HOME_PAGES, viewport


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("path", HOME_PAGES)
def test_skip_link_appears_on_tab(page: Page, site_url, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    page.keyboard.press("Tab")
    skip = page.get_by_test_id("skip-link")
    expect(skip).to_be_focused()
    page.wait_for_timeout(400)  # ссылка выезжает за 0,2 с, меряем после анимации
    assert skip.bounding_box()["y"] >= 0, "ссылка «Перейти к содержимому» осталась за краем экрана"


@pytest.mark.parametrize("path", HOME_PAGES)
def test_contact_hover_moves_name_without_resizing_row(page: Page, site_url, path):
    # Сдвиг сделан через transform: строка не должна менять размер (анимировать padding нельзя).
    page.goto(site_url + path)
    row = page.get_by_test_id("contact-github")
    row.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    height_before = row.bounding_box()["height"]
    row.hover()
    page.wait_for_timeout(500)
    transform = row.evaluate("el => getComputedStyle(el.firstElementChild).transform")
    assert transform != "none", "название не сдвинулось при наведении"
    assert row.bounding_box()["height"] == height_before, "строка контакта изменила размер"


def test_language_switch_both_ways(page: Page, site_url):
    page.goto(site_url + "/")
    page.get_by_test_id("lang-en").click()
    expect(page).to_have_url(site_url + "/en/")
    expect(page.locator("html")).to_have_attribute("lang", "en")

    page.get_by_test_id("lang-ru").click()
    expect(page).to_have_url(site_url + "/")
    expect(page.locator("html")).to_have_attribute("lang", "ru")
