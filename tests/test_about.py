"""Блок «Обо мне»: фото загружается, оформлено для скорости и доступности, раскладка по ширинам.

Запуск из папки сайта: python -m pytest tests
"""

import pytest
from playwright.sync_api import Page, expect

PAGES = ["/", "/en/"]
WIDTHS = [390, 760, 761, 768, 1280, 1920]


def open_about(page: Page, site_url: str, path: str):
    page.goto(site_url + path)
    # Фото загружается лениво (loading="lazy"), поэтому сначала прокручиваем к блоку.
    page.get_by_test_id("section-about").scroll_into_view_if_needed()
    photo = page.get_by_test_id("about-photo")
    # page.wait_for_function здесь не работает: CSP сайта запрещает выполнять код из строки (eval).
    # Поэтому опрашиваем картинку обычным вызовом функции.
    for _ in range(50):
        if photo.evaluate("img => img.complete && img.naturalWidth > 0"):
            return photo
        page.wait_for_timeout(100)
    raise AssertionError("фото не загрузилось за 5 секунд")


@pytest.mark.parametrize("path", PAGES)
def test_photo_loads_and_is_described(page: Page, site_url, path):
    photo = open_about(page, site_url, path)
    expect(photo).to_be_visible()
    # Подпись для незрячих и поисковиков, размеры против прыжков страницы, ленивая загрузка.
    assert photo.get_attribute("alt"), "у фото нет alt"
    assert photo.get_attribute("width") and photo.get_attribute("height"), "у фото нет width/height"
    assert photo.get_attribute("loading") == "lazy"
    assert photo.evaluate("img => img.currentSrc").endswith(".webp")


@pytest.mark.parametrize("path", PAGES)
def test_github_link(page: Page, site_url, path):
    page.goto(site_url + path)
    link = page.get_by_test_id("about-github")
    assert link.get_attribute("href") == "https://github.com/vpopchenya"
    assert "noopener" in link.get_attribute("rel")


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("path", PAGES)
def test_layout_by_width(page: Page, site_url, path, width):
    page.set_viewport_size({"width": width, "height": 900})
    photo = open_about(page, site_url, path)
    name = page.get_by_test_id("about-name")
    photo_box, name_box = photo.bounding_box(), name.bounding_box()
    if width > 760:
        # Компьютер и планшет: фото слева, текст справа.
        assert name_box["x"] > photo_box["x"] + photo_box["width"], "текст не справа от фото"
    else:
        # Телефон: фото над текстом.
        assert name_box["y"] > photo_box["y"] + photo_box["height"], "текст не под фото"
    # Жёлтая рамка сдвинута на 14 px вправо от фото и не должна вылезать за край экрана.
    # scrollWidth здесь не подходит: в начале загрузки его увеличивает анимация печати.
    frame_right = photo.evaluate("img => img.parentElement.getBoundingClientRect().right + 14")
    assert frame_right <= width, f"рамка выходит за край: {frame_right} > {width}"
