import os
import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ... [CHANNELS listesi aynı şekilde kalıyor]

def find_working_domain(start=6, end=100):
    print("sporcafe domainleri taranıyor")
    for i in range(start, end + 1):
        url = f"https://www.sporcafe{i}.xyz/"
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            if res.status_code == 200 and "uxsyplayer" in res.text:
                print(f"Aktif domain: {url}")
                return res.text, url
        except:
            continue
    print(" Aktif domain bulunamadı.")
    return None, None

def find_stream_domain(html):
    match = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html)
    return f"https://{match.group(1)}" if match else None

def extract_base_url(html):
    match = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', html)
    return match.group(1) if match else None

def fetch_streams(domain, referer):
    result = []
    for ch in CHANNELS:
        full_url = f"{domain}/index.php?id={ch['source_id']}"
        try:
            r = requests.get(full_url, headers={**HEADERS, "Referer": referer}, timeout=5)
            if r.status_code == 200:
                base = extract_base_url(r.text)
                if base:
                    stream = f"{base}{ch['source_id']}/playlist.m3u8"
                    print(f" {ch['name']} → {stream}")
                    result.append((ch, stream))
        except:
            pass
    return result

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)  # Dosya adı için geçersiz karakterleri temizle

def write_individual_m3u(links, referer="", folder="serbay"):
    if not os.path.exists(folder):
        os.makedirs(folder)

    for ch, url in links:
        filename = sanitize_filename(f"{ch['name']}.m3u")
        path = os.path.join(folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n')
            f.write(f"#EXTVLCOPT:http-referrer={referer}\n")
            f.write(url + "\n")
        print(f" Yazıldı: {path}")

def main():
    html, referer = find_working_domain()
    if not html:
        return
    stream_domain = find_stream_domain(html)
    if not stream_domain:
        print(" Yayın domaini bulunamadı.")
        return
    print(f"Yayın domaini: {stream_domain}")
    streams = fetch_streams(stream_domain, referer)
    if streams:
        write_individual_m3u(streams, referer=referer)
    else:
        print("Hiçbir yayın alınamadı.")

if __name__ == "__main__":
    main()
