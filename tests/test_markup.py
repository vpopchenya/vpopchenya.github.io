"""Разметка для автотестов и контакты: полный набор data-testid, ссылки на Telegram и email ведут куда нужно.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page

from conftest import ALL_PAGES, HOME_PAGES

HEADER = {"logo", "lang-switch", "lang-ru", "lang-en"}
HOME_COMMON = HEADER | {
    "skip-link", "stamp", "hero-title", "hero-order",
    "section-what", "section-prices", "section-works", "section-about", "section-order", "section-contacts",
    "panel-tests", "panel-sites",
    "plan-landing", "plan-corporate", "plan-multipage", "plan-price", "plan-order", "plans-note",
    "section-process", "step-1", "step-2", "step-3", "step-4", "step-5",
    "work-card-1", "work-card-2", "works-order",
    "about-photo", "about-name", "about-github",
    "order-form", "form-note", "form-name", "form-contact",
    "type-landing", "type-corporate", "type-multipage", "type-other", "type-unsure",
    "form-other-box", "form-other", "form-unsure-hint", "form-message", "form-botcheck",
    "form-consent", "form-privacy", "form-submit", "form-status",
    "contact-github", "contact-telegram", "contact-email", "footer", "footer-privacy",
}
# Блок цен — единственное осознанное различие версий: в RU переключатель ₽ / BYN, в EN только доллары.
EXPECTED_TEST_IDS = {
    "/": HOME_COMMON | {"currency-switch", "currency-rub", "currency-byn", "plan-price-rub", "plan-price-byn"},
    "/en/": HOME_COMMON | {"plan-price-usd"},
    "/privacy/": HEADER | {"privacy-page", "privacy-email", "back-home"},
    "/en/privacy/": HEADER | {"privacy-page", "privacy-email", "back-home"},
    "/404.html": {"notfound", "notfound-home", "notfound-en"},
}


@pytest.mark.parametrize("path", ALL_PAGES)
def test_page_has_exactly_the_documented_test_ids(page: Page, site_url, path):
    # Список совпадает с таблицей в CLAUDE.md: добавили элемент — допишите и туда, и сюда.
    page.goto(site_url + path)
    found = set(page.evaluate("[...document.querySelectorAll('[data-testid]')].map(el => el.dataset.testid)"))
    expected = EXPECTED_TEST_IDS[path]
    assert found == expected, f"не хватает: {expected - found}, лишние: {found - expected}"


@pytest.mark.parametrize("path", HOME_PAGES)
def test_contacts_are_real_links(page: Page, site_url, path):
    # Контакты больше не заглушки: Telegram ведёт в t.me, email открывает почтовую программу.
    page.goto(site_url + path)
    telegram = page.get_by_test_id("contact-telegram")
    assert telegram.get_attribute("href").startswith("https://t.me/")
    assert "noopener" in telegram.get_attribute("rel")
    assert page.get_by_test_id("contact-email").get_attribute("href").startswith("mailto:")
