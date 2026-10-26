"""Раскладка главной страницы по точкам перестройки: 900 px (цены) и 760 px (форма, печать).

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page

from conftest import ALL_WIDTHS, HOME_PAGES, viewport


def grid_columns(page: Page, test_id: str, container: str) -> int:
    """Сколько колонок у сетки, в которой лежит элемент с этим data-testid."""
    return page.get_by_test_id(test_id).evaluate(
        f"el => getComputedStyle(el.closest('{container}')).gridTemplateColumns.split(' ').length"
    )


@pytest.mark.parametrize("width", ALL_WIDTHS)
@pytest.mark.parametrize("path", HOME_PAGES)
def test_columns_and_stamp_follow_breakpoints(page: Page, site_url, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)

    assert grid_columns(page, "plan-landing", ".plans") == (3 if width > 900 else 1), "колонки цен"
    assert grid_columns(page, "form-name", ".form-grid") == (2 if width > 760 else 1), "колонки формы"
    # На телефоне печать встаёт в поток над заголовком, на больших экранах висит справа.
    stamp_position = page.get_by_test_id("stamp").evaluate("el => getComputedStyle(el).position")
    assert stamp_position == ("absolute" if width > 760 else "static")


@pytest.mark.parametrize("width", ALL_WIDTHS)
@pytest.mark.parametrize("path", HOME_PAGES)
def test_nothing_sticks_out_past_the_right_edge(page: Page, site_url, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    page.wait_for_timeout(1500)  # ждём конца анимаций первого экрана: печать в начале нарочно больше
    sticking_out = page.evaluate(
        """width => [...document.querySelectorAll('.wrap *')]
            .filter(el => el.getBoundingClientRect().right > width + 1)
            .map(el => el.dataset.testid || el.className || el.tagName)
            .slice(0, 5)""",
        width,
    )
    assert not sticking_out, f"вылезает за правый край: {sticking_out}"
