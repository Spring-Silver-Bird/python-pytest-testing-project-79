"""Tests for CLI."""


import runpy
import sys

import pytest
import requests

from page_loader import cli

PAGE_URL = "https://ru.hexlet.io/courses"
PAGE_NAME = "ru-hexlet-io-courses.html"


def test_cli_main_success(monkeypatch, tmp_path):
    calls = {}

    def fake_download(url, output_dir):
        calls["url"] = url
        calls["output_dir"] = output_dir
        return str(tmp_path / "ru-hexlet-io-courses.html")

    monkeypatch.setattr(cli, "download", fake_download)
    cli.main(["https://ru.hexlet.io/courses", "--output", str(tmp_path)])
    assert calls["url"] == "https://ru.hexlet.io/courses"
    assert calls["output_dir"] == str(tmp_path)


def test_cli_main_default_output(monkeypatch, tmp_path):
    calls = {}

    def fake_download(url, output_dir):
        calls["url"] = url
        calls["output_dir"] = output_dir
        return str(tmp_path / "ru-hexlet-io-courses.html")

    monkeypatch.setattr(cli, "download", fake_download)
    monkeypatch.setattr(cli.os, "getcwd", lambda: str(tmp_path))
    cli.main(["https://ru.hexlet.io/courses"])
    assert calls["output_dir"] == str(tmp_path)


def test_cli_main_error_exits(capsys, monkeypatch, tmp_path):
    def fake_download(url, output_dir):
        raise requests.RequestException("network down")

    monkeypatch.setattr(cli, "download", fake_download)
    with pytest.raises(SystemExit) as exc:
        cli.main(["https://ru.hexlet.io/courses", "--output", str(tmp_path)])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "network down" in err


def test_cli_main_error_file_not_found(capsys, monkeypatch):
    def fake_download(url, output_dir):
        raise FileNotFoundError("missing dir")

    monkeypatch.setattr(cli, "download", fake_download)
    with pytest.raises(SystemExit) as exc:
        cli.main(["https://ru.hexlet.io/courses"])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "missing dir" in err


def test_cli_main_prints_saved_path(capsys, monkeypatch, tmp_path):
    saved = tmp_path / PAGE_NAME
    monkeypatch.setattr(cli, "download", lambda url, output: str(saved))

    cli.main([PAGE_URL, "--output", str(tmp_path)])

    out = capsys.readouterr().out
    assert out.strip() == str(saved)


def test_cli_main_requires_url():
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_cli_main_rejects_unknown_option():
    with pytest.raises(SystemExit) as exc:
        cli.main([PAGE_URL, "--unknown"])
    assert exc.value.code == 2


def test_cli_main_http_error_exits(capsys, requests_mock, tmp_path):
    requests_mock.get(PAGE_URL, status_code=404)

    with pytest.raises(SystemExit) as exc:
        cli.main([PAGE_URL, "--output", str(tmp_path)])

    assert exc.value.code == 1
    assert "Error:" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_cli_main_downloads_page(requests_mock, tmp_path, capsys):
    requests_mock.get(PAGE_URL, text="<html><body><p>Hello</p></body></html>")

    cli.main([PAGE_URL, "--output", str(tmp_path)])

    saved = tmp_path / PAGE_NAME
    assert saved.exists()
    assert "Hello" in saved.read_text(encoding="utf-8")
    assert capsys.readouterr().out.strip() == str(saved)


def test_cli_module_runs_as_script(requests_mock, tmp_path, monkeypatch, capsys):
    requests_mock.get(PAGE_URL, text="<html><body><p>Hello</p></body></html>")
    monkeypatch.setattr(
        sys, "argv", ["page-loader", PAGE_URL, "--output", str(tmp_path)]
    )

    runpy.run_path(cli.__file__, run_name="__main__")

    assert (tmp_path / PAGE_NAME).exists()
    assert str(tmp_path / PAGE_NAME) in capsys.readouterr().out
