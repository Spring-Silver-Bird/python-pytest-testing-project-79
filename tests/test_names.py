"""Unit tests for the URL-driven naming rules in ``page_loader.names``."""

import re

import pytest

from page_loader.names import resource_filename, url_to_dirname, url_to_filename

PAGE_URLS = [
    "https://ru.hexlet.io/courses",
    "https://ru.hexlet.io/courses/",
    "https://ru.hexlet.io/",
    "https://ru.hexlet.io/courses?lang=ru#top",
    "http://localhost:8080/page",
    "https://ru.hexlet.io/programs/python-pytest-testing",
    "https://ru.hexlet.io/a//b---c",
    "https://RU.hexlet.io/Courses",
]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://ru.hexlet.io/courses", "ru-hexlet-io-courses.html"),
        ("https://ru.hexlet.io/courses/", "ru-hexlet-io-courses.html"),
        ("https://ru.hexlet.io/", "ru-hexlet-io.html"),
        (
            "https://ru.hexlet.io/courses?lang=ru#top",
            "ru-hexlet-io-courses.html",
        ),
        ("http://localhost:8080/page", "localhost-8080-page.html"),
        (
            "https://ru.hexlet.io/programs/python-pytest-testing",
            "ru-hexlet-io-programs-python-pytest-testing.html",
        ),
        ("https://ru.hexlet.io/a//b---c", "ru-hexlet-io-a-b-c.html"),
        ("https://RU.hexlet.io/Courses", "RU-hexlet-io-Courses.html"),
    ],
)
def test_url_to_filename(url, expected):
    assert url_to_filename(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://ru.hexlet.io/courses", "ru-hexlet-io-courses_files"),
        ("https://ru.hexlet.io/", "ru-hexlet-io_files"),
        ("http://localhost:8080/page", "localhost-8080-page_files"),
    ],
)
def test_url_to_dirname(url, expected):
    assert url_to_dirname(url) == expected


@pytest.mark.parametrize("url", PAGE_URLS)
def test_dirname_matches_filename(url):
    filename = url_to_filename(url)
    dirname = url_to_dirname(url)
    assert dirname == filename.removesuffix(".html") + "_files"


@pytest.mark.parametrize("url", PAGE_URLS)
def test_filename_is_well_formed(url):
    filename = url_to_filename(url)
    assert filename.endswith(".html")
    assert re.fullmatch(r"[A-Za-z0-9.-]+\.html", filename)


@pytest.mark.parametrize("ext", [".css", ".png", ".js"])
def test_resource_filename_keeps_extension(ext):
    page_dir = "ru-hexlet-io-courses_files"
    resource_url = f"https://ru.hexlet.io/assets/style{ext}"
    name = resource_filename(page_dir, resource_url)
    assert name.startswith(f"{page_dir}-")
    assert name.endswith(ext)
    assert re.fullmatch(
        rf"{re.escape(page_dir)}-[0-9a-f]{{8}}{re.escape(ext)}", name
    )


def test_resource_filename_without_extension():
    name = resource_filename(
        "ru-hexlet-io-courses_files", "https://ru.hexlet.io/assets/app"
    )
    assert not name.endswith(".")
    assert re.fullmatch(r"ru-hexlet-io-courses_files-[0-9a-f]{8}", name)


def test_resource_filename_hash_format():
    name = resource_filename(
        "page_files", "https://ru.hexlet.io/assets/style.css"
    )
    assert name.startswith("page_files-")
    assert re.fullmatch(r"page_files-[0-9a-f]{8}\.css", name)


def test_resource_filename_is_deterministic():
    args = ("ru-hexlet-io-courses_files", "https://ru.hexlet.io/assets/pic.png")
    assert resource_filename(*args) == resource_filename(*args)


def test_resource_filename_differs_for_different_urls():
    page_dir = "ru-hexlet-io-courses_files"
    first = resource_filename(page_dir, "https://ru.hexlet.io/assets/pic.png")
    second = resource_filename(page_dir, "https://ru.hexlet.io/assets/pic2.png")
    assert first != second
