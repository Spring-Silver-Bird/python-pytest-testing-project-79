"""URL-driven naming rules.

Contract:
- ``https://ru.hexlet.io/courses`` -> ``ru-hexlet-io-courses.html``
- resources dir -> ``ru-hexlet-io-courses_files/``
- resource file -> ``<dir-name>-<hash-of-resource-url><ext>``
"""

import hashlib
import os
import re
from urllib.parse import urlparse


def _slug_from_url(url: str) -> str:
    """Turn URL (host + path) into a dash-separated slug.

    Example: ``https://ru.hexlet.io/courses`` -> ``ru-hexlet-io-courses``.
    """
    parsed = urlparse(url)
    # host + path without trailing slash, query/fragment ignored
    raw = (parsed.netloc + parsed.path).rstrip("/")
    slug = re.sub(r"[^0-9a-zA-Z]", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def url_to_filename(url: str) -> str:
    """Return HTML filename for a page URL.

    ``https://ru.hexlet.io/courses`` -> ``ru-hexlet-io-courses.html``.
    """
    return f"{_slug_from_url(url)}.html"


def url_to_dirname(url: str) -> str:
    """Return resources directory name for a page URL.

    ``https://ru.hexlet.io/courses`` -> ``ru-hexlet-io-courses_files``.
    """
    return f"{_slug_from_url(url)}_files"


def resource_filename(page_dir: str, resource_url: str) -> str:
    """Return a filename for a page resource.

    Format: ``<dir-name>-<short-hash-of-resource-url><ext>`` where ``<ext>``
    is taken from the resource URL path (empty string if none).
    """
    path = urlparse(resource_url).path
    _, ext = os.path.splitext(path)
    digest = hashlib.md5(resource_url.encode("utf-8")).hexdigest()[:8]
    return f"{page_dir}-{digest}{ext}"
