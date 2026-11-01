"""Блок «Заказать сайт»: формы нет, связаться можно кнопками Telegram и почты.

Форму убрали (решение 26.10.2026, studio/docs/requirements/vpopchenya-site/order-form-brief.md):
сайт сам не собирает персональные данные, человек сам решает написать.
Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page, expect

from conftest import ALL_WIDTHS, HOME_PAGES, viewport


@pytest.mark.parametrize("width", ALL_WIDTHS)
@pytest.mark.parametrize("path", HOME_PAGES)
def test_order_buttons_lead_to_telegram_and_email(page: Page, site_url, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    telegram = page.get_by_test_id("order-telegram")
    email = page.get_by_test_id("order-email")
    telegram.scroll_into_view_if_needed()
    expect(telegram).to_be_visible()
    expect(email).to_be_visible()
    assert telegram.get_attribute("href").startswith("https://t.me/")
    assert "noopener" in telegram.get_attribute("rel")
    assert email.get_attribute("href").startswith("mailto:")


@pytest.mark.parametrize("path", HOME_PAGES)
def test_every_order_button_scrolls_to_the_order_block(page: Page, site_url, path):
    page.goto(site_url + path)
    order_buttons = page.locator(
        "[data-testid=hero-order], [data-testid=plan-order], [data-testid=works-order]"
    )
    expect(order_buttons).to_have_count(5)
    for href in order_buttons.evaluate_all("els => els.map(el => el.getAttribute('href'))"):
        assert href == "#order"


@pytest.mark.parametrize("path", HOME_PAGES)
def test_site_collects_no_data(page: Page, site_url, path):
    # Нет формы и нет разрешения на запросы к чужим серверам: данные с сайта никуда не уходят.
    page.goto(site_url + path)
    expect(page.locator("form")).to_have_count(0)
    csp = page.locator("meta[http-equiv=Content-Security-Policy]").get_attribute("content")
    assert "connect-src" not in csp, "в CSP осталось разрешение на запросы к внешнему сервису"
