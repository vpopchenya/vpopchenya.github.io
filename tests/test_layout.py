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


PANELS = ["panel-sites", "panel-tests"]


def _panel_gaps(page: Page, panel):
    """Место от края карточки до текста: сверху, снизу, слева, и отступ карточки."""
    return page.get_by_test_id(panel).evaluate(
        """el => { const box = el.getBoundingClientRect();
            const first = el.firstElementChild.getBoundingClientRect();
            const last = el.lastElementChild.getBoundingClientRect();
            return [first.top - box.top, box.bottom - last.bottom, first.left - box.left,
                    parseFloat(getComputedStyle(el).paddingTop)]; }"""
    )


@pytest.mark.parametrize("width", [1920, 1280, 768, 390])
def test_panel_text_has_equal_space_above_below_and_left(page: Page, site_url, width):
    # Межстрочный «воздух» над заголовком и под последней строкой срезан (text-box), поэтому сверху и слева
    # ровно --card-pad (просьба владельца, 26.10.2026). В ряду карточки одной высоты, так что ровно --card-pad
    # снизу только у карточки с самым длинным текстом, у второй там больше. Справа место зависит от переноса
    # слов, его не проверяем.
    page.set_viewport_size(viewport(width))
    page.goto(site_url + "/")
    below_gaps = []
    for panel in PANELS:
        card = page.get_by_test_id(panel)
        assert card.evaluate("el => getComputedStyle(el).textBoxTrim") == "trim-both", "межстрочный интервал не срезан"
        above, below, left, padding = _panel_gaps(page, panel)
        for name, gap in [("сверху", above), ("слева", left)]:
            assert abs(gap - padding) <= 1, f"{panel}: {name} {gap}px, а отступ карточки {padding}px"
        assert below >= padding - 1, f"{panel}: снизу {below}px, меньше отступа карточки {padding}px"
        below_gaps.append(below)
    assert abs(min(below_gaps) - padding) <= 1, f"снизу {below_gaps}px, а отступ карточки {padding}px"


@pytest.mark.parametrize("width", [1920, 1280, 768])
def test_panels_in_a_row_have_equal_height(page: Page, site_url, width):
    # Разная высота карточек рядом смотрелась неровно (просьба владельца, 26.10.2026).
    page.set_viewport_size(viewport(width))
    page.goto(site_url + "/")
    # offsetTop и offsetHeight берём из раскладки: анимация появления (transform) их не сдвигает.
    (top_a, height_a), (top_b, height_b) = [
        page.get_by_test_id(panel).evaluate("el => [el.offsetTop, el.offsetHeight]") for panel in PANELS
    ]
    assert top_a == top_b, "карточки не в одном ряду"
    assert height_a == height_b, f"высоты {height_a} и {height_b}px"
