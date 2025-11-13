# build_m3u_playwright_updated.py
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re

BASE_URL = "https://macizlevip741.sbs/"
OUTPUT_FILE = "playlist.m3u"

def extract_links_from_page(page):
    urls = set()

    # Sayfadaki tüm a[href] linkleri
    for a in page.query_selector_all("a[href]"):
        href = a.get_attribute("href")
        if not href:
            continue
        href = href.strip()
        if href.startswith("/"):
            href = urljoin(BASE_URL, href)
        if re.search(r"\.m3u8?$", href, re.I):
            urls.add(href)

    # Sayfanın tüm metin içeriğinde link arama
    body_text = page.inner_text("body")
    for m in re.findall(r"https?://[^\s'\"<>]+?\.(?:m3u|m3u8)(?:\?[^\s'\"<>]*)?", body_text, flags=re.I):
        urls.add(m)

    # HTML içeriğinde gizlenmiş linkler
    html_content = page.evaluate("() => document.documentElement.outerHTML")
    for m in re.findall(r"https?://[^\s'\"<>]+?\.(?:m3u|m3u8)(?:\?[^\s'\"<>]*)?", html_content, flags=re.I):
        urls.add(m)

    # iframe içeriği varsa tarama
    for iframe in page.query_selector_all("iframe"):
        try:
            frame = iframe.content_frame()
            if frame:
                urls |= extract_links_from_page(frame)
        except Exception:
            continue

    return urls

def main():
    found = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Ana sayfayı aç
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_load_state("networkidle")  # JS ile yüklenen içerik için

        found |= extract_links_from_page(page)

        # Sayfadaki tüm linkleri tarama
        anchors = page.query_selector_all("a[href]")
        hrefs = []
        for a in anchors:
            href = a.get_attribute("href")
            if not href:
                continue
            href = href.strip()
            if href.startswith("/"):
                href = urljoin(BASE_URL, href)
            hrefs.append(href)
        hrefs = list(dict.fromkeys(hrefs))  # tekrarları sil

        for link in hrefs:
            try:
                page.goto(link, timeout=30000)
                page.wait_for_load_state("networkidle")
                found |= extract_links_from_page(page)
            except Exception:
                continue

        browser.close()

    uniq = sorted(found)
    if uniq:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for u in uniq:
                f.write(f"#EXTINF:-1,{u}\n")
                f.write(u + "\n")
        print(f"[+] {len(uniq)} m3u/m3u8 link bulundu ve '{OUTPUT_FILE}' dosyasına yazıldı.")
    else:
        print("[!] Hiç m3u/m3u8 link bulunamadı.")

if __name__ == "__main__":
    main()
