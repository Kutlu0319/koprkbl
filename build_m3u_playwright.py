# build_m3u_deep_network.py
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re
import time

BASE_URL = "https://macizlevip741.sbs/"
OUTPUT_FILE = "playlist.m3u"

def collect_links(page, found, visited):
    # URL'yi ziyaret ettiysek tekrar gitme
    if page.url in visited:
        return
    visited.add(page.url)

    # Network trafiğini dinle
    def log_request(request):
        url = request.url
        if re.search(r"\.m3u8?$", url, flags=re.I):
            found.add(url)
    page.on("request", log_request)

    # Sayfanın yüklenmesini bekle
    page.wait_for_load_state("networkidle")
    time.sleep(1)  # JS ile yüklenen içerikler için ekstra bekleme

    # iframe içeriğini tarama
    for iframe in page.query_selector_all("iframe"):
        try:
            frame = iframe.content_frame()
            if frame:
                collect_links(frame, found, visited)
        except Exception:
            continue

    # Sayfadaki tüm linkleri takip et
    anchors = page.query_selector_all("a[href]")
    for a in anchors:
        href = a.get_attribute("href")
        if not href:
            continue
        href = href.strip()
        if href.startswith("/"):
            href = urljoin(BASE_URL, href)
        if href.startswith("http") and href not in visited:
            try:
                page.goto(href, timeout=30000)
                collect_links(page, found, visited)
            except Exception:
                continue

def main():
    found = set()
    visited = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Ana sayfayı aç
        page.goto(BASE_URL, timeout=30000)
        collect_links(page, found, visited)

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
