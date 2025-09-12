import requests
from urllib.parse import urlparse

initial_url = "https://d3.premiumvideo.click/uploads/encode/riy6adpvjg2bclb1ejp/master.m3u8"

base_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Origin": "https://dizifun5.com",
    "Referer": "https://dizifun5.com/"
}

try:
    # allow_redirects=False ile yönlendirme takip edilmez
    response = requests.get(initial_url, headers=base_headers, allow_redirects=False, timeout=10)

    print(f"İstek URL: {initial_url}")
    print(f"HTTP Durum Kodu: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', '')}")

    if response.status_code == 200 and "mpegurl" in response.headers.get("Content-Type", ""):
        print("✅ M3U8 içeriği başarıyla alındı:\n")
        print(response.text)
    elif response.status_code in [301, 302, 303, 307, 308]:
        # Yönlendirme var, Location header'ında yeni URL mevcut
        print(f"⚠️ Yönlendirme mevcut: {response.headers.get('Location')}")
        print("Yönlendirmeyi takip etmeden içerik alınamıyor.")
    else:
        print("⚠️ M3U8 içeriği alınamadı veya farklı bir durum var.")
        print(response.text[:500])

except Exception as e:
    print(f"Hata oluştu: {e}")
