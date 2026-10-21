"""Basic tests for ``page_loader.loader.download``: happy path and inputs."""

from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup

from page_loader.loader import _resource_refs, download

FIXTURES = Path(__file__).parent / "fixtures"
PAGE_URL = "https://ru.hexlet.io/courses"
PAGE_NAME = "ru-hexlet-io-courses.html"
DIR_NAME = "ru-hexlet-io-courses_files"
RES_PREFIX = "https://ru.hexlet.io/assets/"


@pytest.fixture
def resources_page(requests_mock):
    """Mock the fixture page and its three local resources."""
    html = FIXTURES.joinpath("page.html").read_text(encoding="utf-8")
    css = FIXTURES.joinpath("styles/application.css").read_bytes()
    js = FIXTURES.joinpath("scripts/app.js").read_bytes()
    png = FIXTURES.joinpath("static/pic.png").read_bytes()
    requests_mock.get(PAGE_URL, text=html)
    requests_mock.get(RES_PREFIX + "application.css", content=css)
    requests_mock.get(RES_PREFIX + "app.js", content=js)
    requests_mock.get(RES_PREFIX + "pic.png", content=png)
    return png


def test_download_saves_page(requests_mock, tmp_path):
    requests_mock.get(PAGE_URL, text="<html><body><p>Hello</p></body></html>")

    path = download(PAGE_URL, str(tmp_path))

    assert path == str(tmp_path / PAGE_NAME)
    assert "Hello" in Path(path).read_text(encoding="utf-8")
    assert not (tmp_path / DIR_NAME).exists()


def test_download_missing_output_dir(requests_mock, tmp_path):
    with pytest.raises(FileNotFoundError):
        download(PAGE_URL, str(tmp_path / "missing"))

    assert requests_mock.call_count == 0


def test_download_page_http_error(requests_mock, tmp_path):
    requests_mock.get(PAGE_URL, status_code=404)

    with pytest.raises(requests.HTTPError):
        download(PAGE_URL, str(tmp_path))

    assert list(tmp_path.iterdir()) == []


def test_download_saves_resources(resources_page, tmp_path):
    download(PAGE_URL, str(tmp_path))

    files_dir = tmp_path / DIR_NAME
    assert files_dir.is_dir()
    saved = sorted(p.name for p in files_dir.iterdir())
    assert len(saved) == 3
    assert {Path(name).suffix for name in saved} == {".css", ".js", ".png"}
    assert next(files_dir.glob("*.png")).read_bytes() == resources_page


def test_download_rewrites_local_paths(resources_page, tmp_path):
    path = download(PAGE_URL, str(tmp_path))

    html = Path(path).read_text(encoding="utf-8")
    assert f"{DIR_NAME}/" in html
    assert RES_PREFIX not in html


def test_download_keeps_external_urls(resources_page, tmp_path):
    path = download(PAGE_URL, str(tmp_path))

    html = Path(path).read_text(encoding="utf-8")
    assert "https://cdn.example.com/banner.png" in html
    assert 'href="/courses/docker"' in html


def test_download_skips_empty_resource_url(requests_mock, tmp_path):
    html = '<html><body><img src="   "><script src=""></script></body></html>'
    requests_mock.get(PAGE_URL, text=html)
    path = download(PAGE_URL, str(tmp_path))
    assert not (tmp_path / DIR_NAME).exists()
    assert PAGE_NAME in path


def test_download_link_rel_as_string(requests_mock, tmp_path):
    html = '<html><head><link rel="stylesheet" href="assets/app.css"></head></html>'
    css = b"body{}"
    requests_mock.get(PAGE_URL, text=html)
    requests_mock.get(RES_PREFIX + "app.css", content=css)
    path = download(PAGE_URL, str(tmp_path))
    files_dir = tmp_path / DIR_NAME
    assert files_dir.exists()
    html_out = Path(path).read_text(encoding="utf-8")
    assert f"{DIR_NAME}/" in html_out


def test_download_resource_http_error(requests_mock, tmp_path):
    html = '<html><head><link rel="stylesheet" href="assets/app.css"></head></html>'
    requests_mock.get(PAGE_URL, text=html)
    requests_mock.get(RES_PREFIX + "app.css", status_code=500)
    with pytest.raises(requests.HTTPError):
        download(PAGE_URL, str(tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_download_resource_request_exception(requests_mock, tmp_path):
    html = '<html><head><link rel="stylesheet" href="assets/app.css"></head></html>'
    requests_mock.get(PAGE_URL, text=html)
    requests_mock.get(RES_PREFIX + "app.css", exc=requests.RequestException("boom"))
    with pytest.raises(requests.RequestException):
        download(PAGE_URL, str(tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_download_page_request_exception(requests_mock, tmp_path):
    requests_mock.get(PAGE_URL, exc=requests.RequestException("network down"))

    with pytest.raises(requests.RequestException):
        download(PAGE_URL, str(tmp_path))

    assert list(tmp_path.iterdir()) == []


def test_download_empty_html(requests_mock, tmp_path):
    requests_mock.get(PAGE_URL, text="")

    path = download(PAGE_URL, str(tmp_path))

    assert Path(path).read_text(encoding="utf-8") == ""
    assert not (tmp_path / DIR_NAME).exists()


def test_download_output_dir_is_a_file(requests_mock, tmp_path):
    target = tmp_path / "not-a-dir.txt"
    target.write_text("x", encoding="utf-8")
    requests_mock.get(PAGE_URL, text="<html></html>")

    with pytest.raises(FileNotFoundError):
        download(PAGE_URL, str(target))

    assert requests_mock.call_count == 0


def test_download_relative_resource_url(requests_mock, tmp_path):
    html = '<html><head><link rel="stylesheet" href="assets/app.css"></head></html>'
    requests_mock.get(PAGE_URL, text=html)
    requests_mock.get(RES_PREFIX + "app.css", content=b"body{}")

    path = download(PAGE_URL, str(tmp_path))

    assert requests_mock.request_history[-1].url == RES_PREFIX + "app.css"
    assert f"{DIR_NAME}/" in Path(path).read_text(encoding="utf-8")


def test_download_reuses_duplicate_resource(requests_mock, tmp_path):
    html = (
        '<html><body><img src="/assets/pic.png">'
        '<img src="/assets/pic.png"></body></html>'
    )
    requests_mock.get(PAGE_URL, text=html)
    requests_mock.get(RES_PREFIX + "pic.png", content=b"png")

    path = download(PAGE_URL, str(tmp_path))

    resource_requests = [
        request
        for request in requests_mock.request_history
        if request.url == RES_PREFIX + "pic.png"
    ]
    assert len(resource_requests) == 1
    saved = list((tmp_path / DIR_NAME).iterdir())
    assert len(saved) == 1
    html_out = Path(path).read_text(encoding="utf-8")
    assert html_out.count(f"{DIR_NAME}/{saved[0].name}") == 2


def test_download_only_external_resources(requests_mock, tmp_path):
    html = (
        '<html><body><img src="https://cdn.example.com/banner.png">'
        '<script src="https://cdn.example.com/app.js"></script></body></html>'
    )
    requests_mock.get(PAGE_URL, text=html)

    path = download(PAGE_URL, str(tmp_path))

    assert not (tmp_path / DIR_NAME).exists()
    html_out = Path(path).read_text(encoding="utf-8")
    assert "https://cdn.example.com/banner.png" in html_out
    assert "https://cdn.example.com/app.js" in html_out


def test_download_default_output_dir(requests_mock, tmp_path, monkeypatch):
    requests_mock.get(PAGE_URL, text="<html><body><p>Hi</p></body></html>")
    monkeypatch.chdir(tmp_path)

    path = download(PAGE_URL)

    assert path == str(tmp_path / PAGE_NAME)
    assert Path(path).exists()


def test_download_relative_output_dir_returns_absolute_path(
    requests_mock, tmp_path, monkeypatch
):
    out = tmp_path / "out"
    out.mkdir()
    requests_mock.get(PAGE_URL, text="<html></html>")
    monkeypatch.chdir(tmp_path)

    path = download(PAGE_URL, "out")

    assert path == str(out / PAGE_NAME)
    assert Path(path).is_absolute()


def test_resource_refs_collects_images_scripts_and_stylesheets():
    html = (
        '<html><head><link rel="stylesheet" href="a.css">'
        '<link rel="icon" href="favicon.ico"></head>'
        '<body><img src="pic.png"><script src="app.js"></script>'
        "<script>console.log(1)</script></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")

    refs = list(_resource_refs(soup))

    assert [(tag.name, attr) for tag, attr in refs] == [
        ("img", "src"),
        ("script", "src"),
        ("link", "href"),
    ]


def test_resource_refs_accepts_plain_string_rel():
    soup = BeautifulSoup("<html></html>", "html.parser")
    link = soup.new_tag("link", href="assets/app.css")
    link["rel"] = "stylesheet"
    soup.append(link)

    assert list(_resource_refs(soup)) == [(link, "href")]


def test_resource_refs_skips_non_stylesheet_string_rel():
    soup = BeautifulSoup("<html></html>", "html.parser")
    link = soup.new_tag("link", href="favicon.ico")
    link["rel"] = "icon"
    soup.append(link)

    assert list(_resource_refs(soup)) == []
