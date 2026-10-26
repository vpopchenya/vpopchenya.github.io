"""Блок «Как проходит работа» и условия под тарифами: есть на обеих страницах и не ломает вёрстку.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page, expect

PAGES = ["/", "/en/"]


@pytest.mark.parametrize("path", PAGES)
def test_process_has_five_steps_and_plans_note(page: Page, site_url, path):
    page.goto(site_url + path)
    for number in range(1, 6):
        expect(page.get_by_test_id(f"step-{number}")).to_be_attached()
    # Условия не должны потеряться: в примечании говорится про домен и хостинг.
    note = page.get_by_test_id("plans-note")
    expect(note).to_contain_text("хостинг" if path == "/" else "hosting")


@pytest.mark.parametrize("path", PAGES)
def test_no_horizontal_scroll_on_phone(page: Page, site_url, path):
    page.set_viewport_size({"width": 390, "height": 900})
    page.goto(site_url + path)
    overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    assert overflow <= 0, f"{path}: страница шире экрана на {overflow}px"
