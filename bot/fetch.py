#!/usr/bin/env python3
import os
import re
import shutil
import sys
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_store import append_snapshots, get_last_snapshot, init_csv

USERNAME = "postandoaquesia"
PROFILE_URL = f"https://www.instagram.com/{USERNAME}/"
COOKIES_FILE = Path(__file__).parent.parent / ".cookies"

CHROME_CANDIDATES = (
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/snap/bin/chromium",
    "/usr/bin/google-chrome",
)
CHROMEDRIVER_CANDIDATES = ("/usr/bin/chromedriver",)


def parse_count(raw: str) -> int:
    raw = raw.strip().lower().replace(" ", "")
    match = re.match(r"^([\d,.]+)\s*([kmb])?$", raw)
    if not match:
        digits = re.sub(r"[^\d]", "", raw)
        return int(digits) if digits else 0

    num_str, suffix = match.group(1), match.group(2) or ""
    if suffix:
        num = float(num_str.replace(",", ""))
        mult = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[suffix]
        return int(num * mult)
    return int(num_str.replace(",", ""))


def load_cookie_header() -> str | None:
    if COOKIES_FILE.is_file():
        return COOKIES_FILE.read_text(encoding="utf-8").strip()
    return os.environ.get("INSTAGRAM_COOKIES")


def parse_cookie_pairs(cookie_header: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            pairs[name.strip()] = value.strip()
    return pairs


def _first_existing(paths: tuple[str, ...]) -> str | None:
    for path in paths:
        if path and os.path.isfile(path):
            return path
    return None


def create_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_bin = (
        os.environ.get("CHROME_BIN")
        or _first_existing(CHROME_CANDIDATES)
        or shutil.which("chromium-browser")
        or shutil.which("chromium")
        or shutil.which("google-chrome")
    )
    if not chrome_bin:
        raise WebDriverException("Chromium não encontrado")
    opts.binary_location = chrome_bin
    driver_path = (
        os.environ.get("CHROMEDRIVER")
        or _first_existing(CHROMEDRIVER_CANDIDATES)
        or shutil.which("chromedriver")
    )
    service = Service(driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=opts)


def inject_cookies(driver: webdriver.Chrome) -> None:
    cookie_header = load_cookie_header()
    if not cookie_header:
        return
    driver.get("https://www.instagram.com/")
    for name, value in parse_cookie_pairs(cookie_header).items():
        driver.add_cookie({"name": name, "value": value, "domain": ".instagram.com"})


def fetch_followers(driver: webdriver.Chrome) -> int:
    inject_cookies(driver)
    driver.set_page_load_timeout(40)
    driver.get(PROFILE_URL)

    if "/accounts/login" in driver.current_url:
        raise ValueError("Instagram redirecionou para login")

    WebDriverWait(driver, 35).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span[title]"))
    )

    def _extract_count() -> int | None:
        for el in driver.find_elements(By.CSS_SELECTOR, "span[title]"):
            title = (el.get_attribute("title") or "").strip()
            text = (el.text or "").strip()
            if re.fullmatch(r"[\d,]+", title) and re.match(r"^[\d,.]+[kmbKMB]?$", text):
                return parse_count(title)
        return None

    try:
        WebDriverWait(driver, 20).until(lambda d: _extract_count() is not None)
    except TimeoutException:
        pass

    exact = _extract_count()
    if exact is not None:
        return exact

    meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
    content = meta.get_attribute("content") or ""
    match = re.search(r"([\d.,]+[kmb]?)\s*followers", content, re.I)
    if match:
        return parse_count(match.group(1))

    raise ValueError("Não foi possível extrair a contagem de seguidores")


def main():
    init_csv()
    last_error = None

    for attempt in range(1, 4):
        driver = None
        try:
            driver = create_driver()
            followers = fetch_followers(driver)
            break
        except (TimeoutException, WebDriverException, ValueError) as e:
            last_error = e
            print(f"Tentativa {attempt}/3 falhou: {e}", file=sys.stderr)
            if attempt == 3:
                print(f"Erro ao buscar seguidores: {e}", file=sys.stderr)
                sys.exit(1)
        finally:
            if driver:
                driver.quit()
    else:
        print(f"Erro ao buscar seguidores: {last_error}", file=sys.stderr)
        sys.exit(1)

    last = get_last_snapshot()
    growth = followers - last["followers"] if last else 0
    ts = append_snapshots(followers)

    sign = "+" if growth >= 0 else ""
    print(f"[{ts}] @{USERNAME}: {followers:,} seguidores ({sign}{growth})")


if __name__ == "__main__":
    main()
