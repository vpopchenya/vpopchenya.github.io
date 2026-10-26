"""Форма заявки: без ключа честно говорит, что не подключена; с ключом отправляет нужные поля.

Настоящий сервис форм тесты не трогают: ключ подставляется в страницу, а запрос к Web3Forms подменяется.
Запуск из папки сайта: python -m pytest tests
"""

import json

import pytest
from playwright.sync_api import Page, expect

from conftest import ALL_WIDTHS, HOME_PAGES, viewport

FORM_ENDPOINT = "https://api.web3forms.com/submit"


@pytest.mark.parametrize("width", ALL_WIDTHS)
@pytest.mark.parametrize("path", HOME_PAGES)
def test_form_without_key_shows_note_and_disables_submit(page: Page, site_url, path, width):
    page.set_viewport_size(viewport(width))
    page.goto(site_url + path)
    expect(page.get_by_test_id("form-note")).to_be_visible()
    expect(page.get_by_test_id("form-submit")).to_be_disabled()


@pytest.mark.parametrize("path", HOME_PAGES)
def test_order_button_picks_the_plan(page: Page, site_url, path):
    page.goto(site_url + path)
    page.get_by_test_id("plan-corporate").get_by_test_id("plan-order").click()
    expect(page.get_by_test_id("type-corporate").locator("input")).to_be_checked()


@pytest.mark.parametrize("path", HOME_PAGES)
def test_other_opens_required_field_and_unsure_shows_hint(page: Page, site_url, path):
    page.goto(site_url + path)
    page.get_by_test_id("type-other").click()
    expect(page.get_by_test_id("form-other-box")).to_be_visible()
    expect(page.get_by_test_id("form-other")).to_have_attribute("required", "")

    page.get_by_test_id("type-unsure").click()
    expect(page.get_by_test_id("form-unsure-hint")).to_be_visible()
    expect(page.get_by_test_id("form-other-box")).to_be_hidden()


@pytest.mark.parametrize("path", HOME_PAGES)
def test_form_with_key_sends_fields_only_after_consent(page: Page, site_url, path):
    sent = []

    def page_with_key(route):
        response = route.fetch()
        route.fulfill(response=response, body=response.text().replace('data-key=""', 'data-key="TEST"'))

    def fake_form_service(route):
        sent.append(json.loads(route.request.post_data))
        route.fulfill(status=200, content_type="application/json", body='{"success": true}')

    page.route(site_url + path, page_with_key)
    page.route(FORM_ENDPOINT, fake_form_service)
    page.goto(site_url + path)

    expect(page.get_by_test_id("form-note")).to_have_count(0)
    submit = page.get_by_test_id("form-submit")
    expect(submit).to_be_enabled()

    page.get_by_test_id("form-name").fill("Тест")
    page.get_by_test_id("form-contact").fill("test@example.test")
    submit.click()
    page.wait_for_timeout(300)
    assert not sent, "форма ушла без согласия на обработку данных"

    page.get_by_test_id("form-consent").check()
    submit.click()
    expect(page.get_by_test_id("form-status")).to_have_class("form-status ok")
    assert len(sent) == 1
    assert sent[0]["access_key"] == "TEST"
    assert sent[0]["name"] == "Тест" and sent[0]["contact"] == "test@example.test"
    expect(page.get_by_test_id("form-name")).to_have_value("")  # после отправки форма очищается
