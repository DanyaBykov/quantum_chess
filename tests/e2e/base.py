from __future__ import annotations

import os
import shlex
import subprocess
import time
import unittest
from pathlib import Path
from typing import Any

import httpx

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    SELENIUM_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - only triggered when selenium is unavailable
    webdriver = None  # type: ignore[assignment]
    By = None  # type: ignore[assignment]
    WebDriver = object  # type: ignore[assignment]
    EC = None  # type: ignore[assignment]
    WebDriverWait = None  # type: ignore[assignment]
    SELENIUM_IMPORT_ERROR = exc


ROOT = Path(__file__).resolve().parents[2]
BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
RUN_SELENIUM_E2E = os.getenv("RUN_SELENIUM_E2E") == "1"
DEFAULT_APP_SERVER_CMD = (
    f"{ROOT}/.venv/bin/python -m uvicorn api.app:app --host 127.0.0.1 --port 8000"
)


def selenium_enabled() -> bool:
    return RUN_SELENIUM_E2E and SELENIUM_IMPORT_ERROR is None


def selenium_skip_reason() -> str:
    if not RUN_SELENIUM_E2E:
        return "Set RUN_SELENIUM_E2E=1 to run Selenium E2E tests"
    if SELENIUM_IMPORT_ERROR is not None:
        return f"Selenium import failed: {SELENIUM_IMPORT_ERROR}"
    return "Selenium disabled"


class LocalAppServer:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.process: subprocess.Popen[str] | None = None
        self._spawned = False

    def ensure_running(self) -> None:
        if self._is_healthy():
            return
        self._spawn()
        self._wait_until_healthy()

    def stop(self) -> None:
        if not self._spawned or self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)

    def _is_healthy(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/game", timeout=1.5)
            return response.status_code == 200
        except Exception:
            return False

    def _spawn(self) -> None:
        command = os.getenv("E2E_APP_SERVER_CMD", DEFAULT_APP_SERVER_CMD)
        self.process = subprocess.Popen(  # noqa: S603 - command is trusted local config
            shlex.split(command),
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self._spawned = True

    def _wait_until_healthy(self, timeout_seconds: float = 30.0) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if self._is_healthy():
                return
            time.sleep(0.2)
        raise RuntimeError("Timed out waiting for local app server to become healthy")


class SeleniumE2ECase(unittest.TestCase):
    driver: WebDriver
    wait: WebDriverWait
    server: LocalAppServer
    base_url = BASE_URL.rstrip("/")

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not selenium_enabled():
            raise unittest.SkipTest(selenium_skip_reason())
        cls.server = LocalAppServer(cls.base_url)
        cls.server.ensure_running()
        cls.driver = webdriver.Safari()  # type: ignore[union-attr]
        cls.driver.set_window_size(1440, 1024)
        cls.wait = WebDriverWait(cls.driver, 10)  # type: ignore[call-arg]

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            if hasattr(cls, "driver"):
                cls.driver.quit()
        finally:
            if hasattr(cls, "server"):
                cls.server.stop()
        super().tearDownClass()

    def api_get(self, path: str) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}{path}", timeout=10)
        response.raise_for_status()
        return response.json()

    def api_post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        response = httpx.post(f"{self.base_url}{path}", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def reset_game(self) -> None:
        self.api_post("/game/reset")

    def open_app(self) -> None:
        self.driver.get(self.base_url)
        self.wait.until(
            EC.presence_of_element_located(  # type: ignore[union-attr]
                (By.CSS_SELECTOR, 'button[aria-label="Square a1"]')  # type: ignore[arg-type]
            )
        )

    def square(self, sq: str):
        selector = f'button[aria-label="Square {sq}"]'
        return self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))  # type: ignore[union-attr,arg-type]
        )

    def click_square(self, sq: str) -> None:
        self.square(sq).click()

    def click_button(self, label: str) -> None:
        button = self.wait.until(
            EC.element_to_be_clickable(  # type: ignore[union-attr]
                (
                    By.XPATH,
                    f"//button[contains(normalize-space(), '{label}')]",
                )  # type: ignore[arg-type]
            )
        )
        button.click()

    def wait_for_side_to_move(self, side: str) -> None:
        self.wait.until(lambda d: f"{side} to move" in d.page_source)

    def wait_for_text(self, text: str) -> None:
        self.wait.until(lambda d: text in d.page_source)

    def selection_text(self) -> str:
        return self.driver.find_element(By.CSS_SELECTOR, ".selection-display").text

    def action_button(self, label: str):
        return self.driver.find_element(By.XPATH, f"//button[normalize-space()='{label}']")

    def execute_classical_move(self, src: str, target: str) -> None:
        self.click_button("Classical")
        self.click_square(src)
        self.click_square(target)
        self.click_button("Execute")
