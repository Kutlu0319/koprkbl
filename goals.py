import requests
import re
import os
import shutil
import sys
import time
from urllib.parse import quote

HEADERS = {"User-Agent": "Mozilla/5.0"}

def run_pygoals_script():
    print("🚀 PyGoals M3U8 Kanal İndirici Başlatılıyor...")
    
    base = "https://trgoals"
    domain = ""
    
    print("\n🔍 Domain aranıyor: trgoals1393.xyz → trgoals2100.xyz")
    for i in range(1393, 2101):
        test_domain = f"{base}{i}.xyz"
        try:
            response = requests.head(test_domain, timeout=3)
            if response.status_code == 200:
                domain = test_domain
                print(f"✅ Domain bulundu: {domain}")
                break
            else:
                print(f"⏳ Denenen domain: {test_domain} (Status: {response.status_code})")
        except Exception as e:
            print(f"⏳ Denenen domain: {test_domain} (Hata: {str(e)[:30]}...)")
            continue
    
    channel_ids = {
        "yayinzirve": "beIN Sports 1 ☪️",
        "yayininat": "beIN Sports 1 ⭐",
        "yayin1": "beIN Sports 1 ♾️",
        "yayinb2": "beIN Sports 2",
        "yayinb3": "beIN Sports 3",
        "yayinb4": "beIN Sports 4",
        "yayinb5": "beIN Sports 5",
        "yayinbm1": "BeIN Sports 1 Max",
        "yayinbm2": "BeIN Sports 2 Max",
        "yayinss": "Saran Sports 1",
        "yayinss2": "Saran Sports 2",
        "yayint1": "Tivibu Sports 1",
        "yayint2": "Tivibu Sports 2",
        "yayint3": "Tivibu Sports 3",
        "yayint4": "Tivibu Sports 4",
        "yayinsmarts": "Smart Sports",
        "yayinsms2": "Smart Sports 2",
        "yayintrtspor": "TRT Spor",
        "yayintrtspor2": "TRT Spor 2",
        "yayinas": "A Spor",
        "yayinatv": "ATV",
        "yayintv8": "TV8",
        "yayintv85": "TV8.5",
        "yayinnbatv": "NBA TV",
        "yayinex1": "Tâbii 1",
        "yayinex2": "Tâbii 2",
        "yayinex3": "Tâbii 3",
        "yayinex4": "Tâbii 4",
        "yayinex5": "Tâbii 5",
        "yayinex6": "Tâbii 6",
        "yayinex7": "Tâbii 7",
        "yayinex8": "Tâbii 8"
    }
    
    folder_name = "channels_files"
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    os.makedirs(folder_name, exist_ok=True)
    
    if not domain:
        print("❌ Domain bulunamadı, işlem durduruldu.")
        return
    
    created = 0
    failed = 0
    
    for i, (channel_id, channel_name) in enumerate(channel_ids.items(), 1):
        try:
            print(f"\n[{i}/{len(channel_ids)}] {channel_name} işleniyor...")
            url = f"{domain}/channel.html?id={channel_id}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"❌ HTTP Hatası: {response.status_code}")
                failed += 1
                continue
            match = re.search(r'const baseurl = "(.*?)"', response.text)
            if not match:
                print("❌ BaseURL bulunamadı")
                failed += 1
                continue
            baseurl = match.group(1)
            encoded_url = quote(f"{baseurl}{channel_id}.m3u8", safe='')
            full_url = f"http://proxylendim101010.mywire.org/proxy.php?url={encoded_url}"
            
            content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25
{full_url}
"""
            safe_name = re.sub(r'[^\w\s.-]', '_', channel_name).replace(' ', '_') + ".m3u8"
            path = os.path.join(folder_name, safe_name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ {channel_name} → {safe_name}")
            created += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ Hata: {e}")
            failed += 1
    
    print(f"\nPyGoals: Başarılı: {created}, Başarısız: {failed}, Klasör: {os.path.abspath(folder_name)}")



CHANNELS = [
    {"id": "bein1", "source_id": "selcukbeinsports1", "name": "BeIN Sports 1", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/5rhmw31628798883.png", "group": "Spor"},
    {"id": "bein2", "source_id": "selcukbeinsports2", "name": "BeIN Sports 2", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/7uv6x71628799003.png", "group": "Spor"},
    {"id": "bein3", "source_id": "selcukbeinsports3", "name": "BeIN Sports 3", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/u3117i1628798857.png", "group": "Spor"},
    {"id": "bein4", "source_id": "selcukbeinsports4", "name": "BeIN Sports 4", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/2ktmcp1628798841.png", "group": "Spor"},
    {"id": "bein5", "source_id": "selcukbeinsports5", "name": "BeIN Sports 5", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/BeIn_Sports_5_US.png", "group": "Spor"},
    {"id": "beinmax1", "source_id": "selcukbeinsportsmax1", "name": "BeIN Sports Max 1", "logo": "https://assets.bein.com/mena/sites/3/2015/06/beIN_SPORTS_MAX1_DIGITAL_Mono.png", "group": "Spor"},
    {"id": "beinmax2", "source_id": "selcukbeinsportsmax2", "name": "BeIN Sports Max 2", "logo": "http://tvprofil.com/img/kanali-logo/beIN_Sports_MAX_2_TR_logo_v2.png?1734011568", "group": "Spor"},
    {"id": "tivibu1", "source_id": "selcuktivibuspor1", "name": "Tivibu Spor 1", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/qadnsi1642604437.png", "group": "Spor"},
    {"id": "tivibu2", "source_id": "selcuktivibuspor2", "name": "Tivibu Spor 2", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/kuasdm1642604455.png", "group": "Spor"},
    {"id": "tivibu3", "source_id": "selcuktivibuspor3", "name": "Tivibu Spor 3", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/slwrz41642604502.png", "group": "Spor"},
    {"id": "tivibu4", "source_id": "selcuktivibuspor4", "name": "Tivibu Spor 4", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/59bqi81642604517.png", "group": "Spor"},
    {"id": "ssport1", "source_id": "selcukssport", "name": "S Sport 1", "logo": "https://itv224226.tmp.tivibu.com.tr:6430/images/poster/20230302923239.png", "group": "Spor"},
    {"id": "ssport2", "source_id": "selcukssport2", "name": "S Sport 2", "logo": "https://itv224226.tmp.tivibu.com.tr:6430/images/poster/20230302923321.png", "group": "Spor"},
    {"id": "smart1", "source_id": "selcuksmartspor", "name": "Smart Spor 1", "logo": "https://dsmart-static-v2.ercdn.net//resize-width/1920/content/p/el/11909/Thumbnail.png", "group": "Spor"},
    {"id": "smart2", "source_id": "selcuksmartspor2", "name": "Smart Spor 2", "logo": "https://www.dsmart.com.tr/api/v1/public/images/kanallar/SPORSMART2-gri.png", "group": "Spor"},
    {"id": "aspor", "source_id": "selcukaspor", "name": "A Spor", "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/9d28401f-2d4e-4862-85e2-69773f6f45f4.png", "group": "Spor"},
    {"id": "eurosport1", "source_id": "selcukeurosport1", "name": "Eurosport 1", "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/54cad412-5f3a-4184-b5fc-d567a5de7160.png", "group": "Spor"},
    {"id": "eurosport2", "source_id": "selcukeurosport2", "name": "Eurosport 2", "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/a4cbdd15-1509-408f-a108-65b8f88f2066.png", "group": "Spor"},
]

if __name__ == "__main__":
    run_pygoals_script()
