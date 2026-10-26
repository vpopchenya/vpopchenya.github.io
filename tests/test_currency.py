"""Переключатель валюты над карточками цен: ₽ для России, BYN для Беларуси.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page, expect

PAGES = ["/", "/en/"]
PLANS = ["plan-landing", "plan-corporate", "plan-multipage"]
DESKTOP_WIDTHS = [901, 1280, 1920]


def prices(page: Page, currency: str):
    """Цены одной валюты во всех трёх карточках."""
    return [page.get_by_test_id(plan).get_by_test_id(f"plan-price-{currency}") for plan in PLANS]


def expect_currency_shown(page: Page, shown: str, hidden: str):
    for price in prices(page, shown):
        expect(price).to_be_visible()
    for price in prices(page, hidden):
        expect(price).to_be_hidden()


@pytest.mark.parametrize("path", PAGES)
def test_rubles_by_default(page: Page, site_url, path):
    page.goto(site_url + path)
    expect(page.get_by_test_id("currency-rub").locator("input")).to_be_checked()
    expect_currency_shown(page, shown="rub", hidden="byn")


@pytest.mark.parametrize("path", PAGES)
def test_switch_to_byn_and_back(page: Page, site_url, path):
    page.goto(site_url + path)
    page.get_by_test_id("currency-byn").click()
    expect_currency_shown(page, shown="byn", hidden="rub")
    page.get_by_test_id("currency-rub").click()
    expect_currency_shown(page, shown="rub", hidden="byn")


def test_switch_works_from_keyboard(page: Page, site_url):
    # Радиокнопки переключаются стрелками: Tab до переключателя, затем стрелка вправо.
    page.goto(site_url + "/")
    page.get_by_test_id("currency-rub").locator("input").focus()
    page.keyboard.press("ArrowRight")
    expect(page.get_by_test_id("currency-byn").locator("input")).to_be_checked()
    expect_currency_shown(page, shown="byn", hidden="rub")


@pytest.mark.parametrize("currency", ["rub", "byn"])
@pytest.mark.parametrize("width", DESKTOP_WIDTHS)
@pytest.mark.parametrize("path", PAGES)
def test_prices_on_one_line_on_desktop(page: Page, site_url, path, width, currency):
    # На компьютере карточки делят строки через subgrid: цены стоят на одной высоте в любой валюте.
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(site_url + path)
    page.get_by_test_id(f"currency-{currency}").click()
    # Меряем все цены одним вызовом, в одном кадре: секция в этот момент ещё может выезжать
    # при появлении, и замеры по очереди попали бы в разные кадры анимации.
    tops = page.evaluate(
        """ids => ids.map(([plan, price]) => Math.round(document
            .querySelector(`[data-testid="${plan}"] [data-testid="${price}"]`)
            .getBoundingClientRect().top))""",
        [[plan, f"plan-price-{currency}"] for plan in PLANS],
    )
    assert max(tops) - min(tops) <= 1, f"цены на разной высоте: {tops}"


@pytest.mark.parametrize("path", PAGES)
def test_no_sideways_scroll_on_phone_with_switch(page: Page, site_url, path):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(site_url + path)
    page.get_by_test_id("currency-byn").click()
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
