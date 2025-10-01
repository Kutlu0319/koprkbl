import requests
import json
import gzip
from io import BytesIO
import time
import os

def get_canli_tv_m3u():
    """
    Canlı TV kanal verilerini alır ve M3U playlist dosyası (yeni.m3u) oluşturur.
    """

    url = "https://core-api.kablowebtv.com/api/channels"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"
    }

    try:
        print("📡 API'den canlı TV verileri alınıyor...")

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode("utf-8")
        except:
            content = response.content.decode("utf-8")

        data = json.loads(content)

        if not data.get("IsSucceeded") or not data.get("Data", {}).get("AllChannels"):
            print("❌ Geçerli kanal verisi alınamadı.")
            return False

        channels = data["Data"]["AllChannels"]
        print(f"✅ {len(channels)} kanal bulundu.")

        with open("yeni.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# OluşturulmaZamani: {time.time()}\n")  # Sürekli değişen satır

            kanal_sayisi = 0
            kanal_index = 1

            for channel in channels:
                name = channel.get("Name")
                stream_data = channel.get("StreamData", {})
                hls_url = stream_data.get("HlsStreamUrl") if stream_data else None
                logo = channel.get("PrimaryLogoImageUrl", "")
                categories = channel.get("Categories", [])

                if not name or not hls_url:
                    continue

                group = categories[0].get("Name", "Genel") if categories else "Genel"

                if group == "Bilgilendirme":
                    continue

                tvg_id = str(kanal_index)

                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f"{hls_url}\n")

                kanal_sayisi += 1
                kanal_index += 1

        if os.path.exists("yeni.m3u"):
            print("✅ srbyknl.m3u dosyası başarıyla oluşturuldu.")
        else:
            print("❌ srbyknl.m3u dosyası oluşturulamadı.")

        print(f"📺 M3U dosyası oluşturuldu: srbyknl.m3u ({kanal_sayisi} kanal)")
        return True

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        return False

if __name__ == "__main__":
    get_canli_tv_m3u()
