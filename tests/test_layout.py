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
def test_nothing_sticks_out_past_the_edges(page: Page, site_url, path, width):
    # Оба края: ловушка для ботов раньше стояла на 9999 px левее экрана, и встроенный браузер
    # Telegram на iPhone давал сдвинуть страницу влево. Проверка только правого края этого не видела.
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    page.wait_for_timeout(1500)  # ждём конца анимаций первого экрана: печать в начале нарочно больше
    sticking_out = page.evaluate(
        """width => [...document.querySelectorAll('.wrap *')]
            .filter(el => { const r = el.getBoundingClientRect(); return r.right > width + 1 || r.left < -1; })
            .map(el => el.dataset.testid || el.className || el.tagName)
            .slice(0, 5)""",
        width,
    )
    assert not sticking_out, f"вылезает за край экрана: {sticking_out}"


@pytest.mark.parametrize("width", ALL_WIDTHS)
def test_sites_panel_text_stays_inside_rounded_corner(page: Page, site_url, width):
    # У карточки «Сайты» большое скругление снизу слева. На телефоне оно срезало последнюю строку.
    page.set_viewport_size(viewport(width))
    page.goto(site_url + "/")
    corner_hit = page.get_by_test_id("panel-sites").evaluate(
        """panel => {
            const box = panel.getBoundingClientRect();
            const r = parseFloat(getComputedStyle(panel).borderBottomLeftRadius);
            const range = document.createRange();
            range.selectNodeContents(panel.querySelector('p'));
            const lines = [...range.getClientRects()];
            const last = lines[lines.length - 1];
            // Расстояние от левого нижнего угла карточки до начала последней строки.
            const dx = last.left - box.left, dy = box.bottom - last.bottom;
            if (dx >= r || dy >= r) return null;  // строка вне зоны скругления
            const inside = (r - dx) ** 2 + (r - dy) ** 2 <= r ** 2;
            return inside ? null : {dx, dy, r};
        }"""
    )
    assert corner_hit is None, f"последняя строка попала на скругление: {corner_hit}"


@pytest.mark.parametrize("width", [1280, 390])
@pytest.mark.parametrize("card", ["panel-tests", "panel-sites", "plan-landing", "work-card-1"])
def test_cards_have_equal_padding_on_all_sides(page: Page, site_url, card, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + "/")
    top, right, bottom, left = page.get_by_test_id(card).evaluate(
        """el => { const s = getComputedStyle(el);
            return [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].map(parseFloat); }"""
    )
    # Под жёлтой кнопкой есть ступенька 6 px: снизу отступ больше ровно на неё, чтобы на глаз было поровну.
    button_step = 6 if card == "plan-landing" else 0
    assert top == right == left == bottom - button_step, f"отступы {top} {right} {bottom} {left}"
