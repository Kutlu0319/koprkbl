# build_m3u_playwright.py
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re

BASE_URL = "https://macizlevip741.sbs/"
OUTPUT_FILE = "playlist.m3u"

def extract_links_from_page(page):
    urls = set()
    for a in page.query_selector_all("a[href]"):
        href = a.get_attribute("href")
        if not href:
            continue
        href = href.strip()
        if href.startswith("/"):
            href = urljoin(BASE_URL, href)
        if re.search(r"\.m3u8?$", href, re.I):
            urls.add(href)
    body_text = page.inner_text("body")
    for m in re.findall(r"https?://[^\s'\"<>]+?\.(?:m3u|m3u8)(?:\?[^\s'\"<>]*)?", body_text, flags=re.I):
        urls.add(m)
    return urls

def main():
    found = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_timeout(1500)

        found |= extract_links_from_page(page)

        anchors = page.query_selector_all("a[href]")
        hrefs = []
        for a in anchors:
            href = a.get_attribute("href")
            if not href:
                continue
            href = href.strip()
            if href.startswith("/"):
                href = urljoin(BASE_URL, href)
            if BASE_URL.split("//")[-1] in href or href.startswith("http"):
                hrefs.append(href)
        hrefs = list(dict.fromkeys(hrefs))

        for link in hrefs:
            try:
                page.goto(link, timeout=30000)
                page.wait_for_timeout(800)
                found |= extract_links_from_page(page)
            except Exception:
                continue

        browser.close()

    uniq = sorted(found)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for u in uniq:
            f.write(f"#EXTINF:-1,{u}\n")
            f.write(u + "\n")

if __name__ == "__main__":
    main()
