import re
import sys
import time
import requests
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

# --- GLOBAL USER-AGENT ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"


# ---------------------------------------------------------------------
# ✔️ GÜNCELLENMİŞ FONKSİYON: GÜNCEL DOMAIN TXT DOSYASINDAN ÇEKİLİYOR
# ---------------------------------------------------------------------
def find_working_domain(page=None):
    """
    GitHub üzerinde bulunan TXT dosyasından güncel domain'i çeker.
    """
    print("\n🔎 Güncel domain GitHub TXT dosyasından alınıyor...")

    try:
        url = "https://raw.githubusercontent.com/koprulu555/selcuk-full-domain-kontrol/main/selcuk_sports_guncel_domain.txt"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print("❌ TXT dosyasına ulaşılamadı!")
            return None

        domain = response.text.strip()

        if not domain:
            print("❌ TXT dosyası boş!")
            return None
        
        # https ekle (yoksa)
        if not domain.startswith("http"):
            domain = "https://" + domain

        domain = domain.rstrip("/")
        print(f"✅ Güncel domain bulundu: {domain}")
        return domain

    except Exception as e:
        print(f"❌ Domain okunamadı: {e}")
        return None



# ---------------------------------------------------------------------
#   (DEVAM EDEN KODUN — AYNI ŞEKİLDE SENİN ORİJİNALİN)
# ---------------------------------------------------------------------

def get_channel_group(channel_name):
    channel_name_lower = channel_name.lower()
    group_mappings = {
        'BeinSports': ['bein sports', 'beın sports'],
        'S Sports': ['s sport'],
        'Tivibu': ['tivibu spor', 'tivibu'],
        'Ulusal Kanallar': ['a spor', 'trt spor', 'trt 1', 'tv8', 'atv'],
        'Diğer Spor': ['smart spor', 'nba tv', 'eurosport'],
        'Belgesel': ['national geographic', 'nat geo', 'discovery', 'dmax', 'bbc earth', 'history'],
        'Film & Dizi': ['bein series', 'bein movies', 'movie smart']
    }
    for group, keywords in group_mappings.items():
        for keyword in keywords:
            if keyword in channel_name_lower:
                return group

    if "7/24" in channel_name_lower:
        return "Ulusal Kanallar"

    if not re.search(r'\d{2}:\d{2}', channel_name):
         return "7/24 Kanallar"

    return "Maç Yayınları"



def scrape_channel_links(page, domain_to_scrape):
    print(f"\n📡 Kanallar {domain_to_scrape} adresinden çekiliyor...")
    channels = []
    try:
        page.goto(domain_to_scrape, timeout=25000, wait_until='domcontentloaded')
        
        link_elements = page.query_selector_all("a[data-url]")
        
        if not link_elements:
            print("❌ Ana sayfada 'data-url' içeren link bulunamadı.")
            return []
            
        for link in link_elements:
            player_url = link.get_attribute('data-url')
            name_element = link.query_selector('div.name')
            
            if name_element and player_url:
                channel_name = name_element.inner_text().strip()
                
                if player_url.startswith('/'):
                    base_domain = domain_to_scrape.rstrip('/')
                    player_url = f"{base_domain}{player_url}"
                
                try:
                    parsed_player_url = urlparse(player_url)
                    player_origin = f"{parsed_player_url.scheme}://{parsed_player_url.netloc}"
                except Exception:
                    player_origin = None 
                
                if not player_origin:
                    continue 

                time_element = link.query_selector('time.time')
                if time_element:
                    time_str = time_element.inner_text().strip()
                    if time_str != "7/24":
                        channel_name = f"{channel_name} - {time_str}"
                    else:
                        channel_name = channel_name.replace(time_str, "").strip()

                group_name = get_channel_group(channel_name)
                
                channels.append({
                    'name': channel_name,
                    'url': player_url,
                    'group': group_name,
                    'origin': player_origin
                })

        print(f"✅ {len(channels)} kanal bulundu.")
        return channels
        
    except PlaywrightError as e:
        print(f"❌ Ana sayfaya ulaşılamadı. Hata: {e.__class__.__name__}")
        return []



def extract_m3u8_from_page(page, player_url):
    try:
        page.goto(player_url, timeout=20000, wait_until="domcontentloaded")
        content = page.content()
        base_url_match = re.search(r"this\.baseStreamUrl\s*=\s*['\"](https?://.*?)['\"]", content)
        if not base_url_match:
            print(" -> ❌ 'baseStreamUrl' bulunamadı.", end="")
            return None
        base_url = base_url_match.group(1)
        
        parsed_url = urlparse(player_url)
        query_params = parse_qs(parsed_url.query)
        stream_id = query_params.get('id', [None])[0]
        if not stream_id:
            print(" -> ❌ 'id' parametresi bulunamadı.", end="")
            return None

        m3u8_link = f"{base_url}{stream_id}/playlist.m3u8"
        return m3u8_link

    except Exception:
        print(" -> ❌ Sayfa yüklenirken hata oluştu.", end="")
        return None



def main():
    with sync_playwright() as p:
        print("🚀 Playwright ile Xyz_srb M3U8 Kanal İndirici Başlatılıyor...")
        
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT
        )
        page = context.new_page()

        # ✔️ Güncel domain artık TXT'den geliyor
        xyz_domain = find_working_domain()

        if not xyz_domain:
            print("❌ Güncel domain bulunamadı!")
            browser.close()
            sys.exit(1)

        channels = scrape_channel_links(page, xyz_domain)

        if not channels:
            print("❌ Kanal bulunamadı!")
            browser.close()
            sys.exit(1)
        
        m3u_content = []
        output_filename = "xyzsports_kanallar.m3u8"
        print(f"\n📺 {len(channels)} kanal işleniyor...")
        created = 0

        player_origin_host = channels[0]['origin']
        player_referer = player_origin_host + '/'
        
        m3u_header_lines = [
            "#EXTM3U",
            f"#EXT-X-USER-AGENT:{USER_AGENT}",
            f"#EXT-X-REFERER:{player_referer}",
            f"#EXT-X-ORIGIN:{player_origin_host}"
        ]
        
        for i, channel_info in enumerate(channels, 1):
            channel_name = channel_info['name']
            player_url = channel_info['url']
            group_name = channel_info['group']
            
            print(f"[{i}/{len(channels)}] {channel_name} (Grup: {group_name})...", end="")
            
            m3u8_link = extract_m3u8_from_page(page, player_url)
            
            if m3u8_link:
                print(" -> ✅")
                m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{group_name}",{channel_name}')
                m3u_content.append(m3u8_link)
                created += 1
            else:
                print(" -> ❌")
        
        browser.close()

        if created > 0:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_header_lines))
                f.write("\n\n")
                f.write("\n".join(m3u_content))
            print(f"\n📂 {created} kanal '{output_filename}' dosyasına kaydedildi.")
        else:
            print("\nℹ️ Hiçbir M3U8 linki oluşturulamadı.")

        print("\n🎉 Tamamlandı!")



if __name__ == "__main__":
    main()
