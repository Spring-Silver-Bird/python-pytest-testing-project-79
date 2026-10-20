"""Download logic for the page loader."""

import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from page_loader.names import resource_filename, url_to_dirname, url_to_filename


def _is_local(page_url: str, resource_url: str) -> bool:
    """Return True if the resource lives on the page's host."""
    page_host = urlparse(page_url).netloc.lower()
    resource_host = urlparse(resource_url).netloc.lower()
    return resource_host == page_host


def _resource_refs(soup: BeautifulSoup):
    """Yield ``(tag, attribute)`` pairs pointing at downloadable resources.

    Covers ``img[src]``, ``script[src]`` and ``link[href]`` with a
    ``stylesheet`` relation; other links (canonical, favicon, ...) are
    not resources.
    """
    for tag in soup.find_all("img", src=True):
        yield tag, "src"
    for tag in soup.find_all("script", src=True):
        yield tag, "src"
    for tag in soup.find_all("link", href=True):
        rel = tag.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        if any(item.lower() == "stylesheet" for item in rel):
            yield tag, "href"


def download(url: str, output_dir: str = ".") -> str:
    """Download a page and its local resources into an existing directory.

    Same-host images, scripts and stylesheets are saved into a
    ``<page>_files/`` directory next to the page, and the HTML is
    rewritten to reference them with relative paths. URLs pointing at
    other hosts are left untouched.

    Args:
        url: page URL to fetch.
        output_dir: existing directory for the saved files.

    Returns:
        Absolute path to the saved ``<name>.html`` file.

    Raises:
        FileNotFoundError: if ``output_dir`` does not exist.
        requests.RequestException: on network/HTTP errors while fetching
            the page or any of its local resources. The HTML file is
            only written after every resource has been downloaded, so a
            failure leaves no page file behind.
        OSError: if a file or directory can't be created.
    """
    if not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    dirname = url_to_dirname(url)
    files_dir = os.path.join(os.path.abspath(output_dir), dirname)

    fetched: dict[str, str] = {}
    for tag, attr in _resource_refs(soup):
        value = tag[attr]
        if not value or not value.strip():
            continue
        resource_url = urljoin(url, value)
        if not _is_local(url, resource_url):
            continue
        if resource_url not in fetched:
            resource_response = requests.get(resource_url)
            resource_response.raise_for_status()
            filename = resource_filename(dirname, resource_url)
            os.makedirs(files_dir, exist_ok=True)
            filepath = os.path.join(files_dir, filename)
            with open(filepath, "wb") as f:
                f.write(resource_response.content)
            fetched[resource_url] = f"{dirname}/{filename}"
        tag[attr] = fetched[resource_url]

    filename = url_to_filename(url)
    filepath = os.path.join(os.path.abspath(output_dir), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(soup))
    return filepath
