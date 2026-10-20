"""Tests for CLI."""


import pytest
import requests

from page_loader import cli


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
