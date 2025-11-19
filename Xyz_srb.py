import re
import sys
import time
import urllib.request
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError


# GLOBAL USER-AGENT
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"



# ---------------------------------------------------------------------
# ✔️ GÜNCEL DOMAIN — GitHub TXT DOSYASINDAN (requests yok!)
# ---------------------------------------------------------------------
def find_working_domain(page=None):
    """
    GitHub TXT dosyasından güncel domain'i urllib ile alır.
    """
    print("\n🔎 Güncel domain GitHub TXT dosyasından alınıyor...")

    url = "https://raw.githubusercontent.com/koprulu555/selcuk-full-domain-kontrol/main/selcuk_sports_guncel_domain.txt"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            domain = response.read().decode().strip()

        if not domain:
            print("❌ TXT dosyası boş!")
            return None

        if not domain.startswith("http"):
            domain = "https://" + domain

        domain = domain.rstrip("/")
        print(f"✅ Güncel domain bulundu: {domain}")
        return domain

    except Exception as e:
        print(f"❌ Domain okunamadı: {e}")
        return None



# ---------------------------------------------------------------------
# ✔️ KANAL GRUPLANDIRMA
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



# ---------------------------------------------------------------------
# ✔️ KANALLARI ÇEKME
# ---------------------------------------------------------------------
def scrape_channel_links(page, domain_to_scrape):
    print(f"\n📡 Kanallar {domain_to_scrape} adresinden çekiliyor...")
    channels = []

    try:
        page.goto(domain_to_scrape, timeout=25000, wait_until='domcontentloaded')
        link_elements = page.query_selector_all("a[data-url]")

        if not link_elements:
            print("❌ 'data-url' içeren kanal linki bulunamadı.")
            return []

        for link in link_elements:
            player_url = link.get_attribute('data-url')
            name_element = link.query_selector('div.name')

            if name_element and player_url:
                channel_name = name_element.inner_text().strip()

                if player_url.startswith('/'):
                    base_domain = domain_to_scrape.rstrip('/')
                    player_url = f"{base_domain}{player_url}"

                # ORIGIN çek
                try:
                    parsed_player_url = urlparse(player_url)
                    player_origin = f"{parsed_player_url.scheme}://{parsed_player_url.netloc}"
                except Exception:
                    player_origin = None

                if not player_origin:
                    continue

                # Zaman etiketi
                time_element = link.query_selector('time.time')
                if time_element:
                    t = time_element.inner_text().strip()
                    if t != "7/24":
                        channel_name = f"{channel_name} - {t}"

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
        print(f"❌ Kanallar çekilirken hata: {e}")
        return []



# ---------------------------------------------------------------------
# ✔️ M3U8 OLUŞTURMA
# ---------------------------------------------------------------------
def extract_m3u8_from_page(page, player_url):
    try:
        page.goto(player_url, timeout=20000, wait_until="domcontentloaded")
        content = page.content()

        base_url_match = re.search(r"this\.baseStreamUrl\s*=\s*['\"](https?://.*?)['\"]", content)
        if not base_url_match:
            print(" -> ❌ baseStreamUrl bulunamadı.", end="")
            return None

        base_url = base_url_match.group(1)

        parsed_url = urlparse(player_url)
        query_params = parse_qs(parsed_url.query)
        stream_id = query_params.get('id', [None])[0]
        if not stream_id:
            print(" -> ❌ 'id' parametresi yok.", end="")
            return None

        return f"{base_url}{stream_id}/playlist.m3u8"

    except Exception:
        print(" -> ❌ Sayfa hatası.", end="")
        return None



# ---------------------------------------------------------------------
# ✔️ MAIN
# ---------------------------------------------------------------------
def main():
    with sync_playwright() as p:
        print("🚀 XyzSports M3U8 Oluşturucu Başlatıldı...")

        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        # DOMAIN TXT'DEN
        xyz_domain = find_working_domain()
        if not xyz_domain:
            print("❌ Domain bulunamadı, çıkılıyor.")
            browser.close()
            sys.exit(1)

        channels = scrape_channel_links(page, xyz_domain)
        if not channels:
            print("❌ Kanal bulunamadı.")
            browser.close()
            sys.exit(1)

        m3u_content = []
        output_filename = "Xyz_srb.m3u"   # ✔️ SENİN İSTEDİĞİN AD
        created = 0

        # GLOBAL HEADERS
        origin = channels[0]['origin']
        referer = origin + "/"

        m3u_header = [
            "#EXTM3U",
            f"#EXT-X-USER-AGENT:{USER_AGENT}",
            f"#EXT-X-REFERER:{referer}",
            f"#EXT-X-ORIGIN:{origin}"
        ]

        print(f"\n📺 {len(channels)} kanal işleniyor...\n")

        for i, ch in enumerate(channels, 1):
            print(f"[{i}/{len(channels)}] {ch['name']} (Grup: {ch['group']})...", end="")

            m3u8 = extract_m3u8_from_page(page, ch['url'])

            if m3u8:
                print(" ✔️")
                m3u_content.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}')
                m3u_content.append(m3u8)
                created += 1
            else:
                print(" ❌")

        browser.close()

        if created > 0:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_header) + "\n\n")
                f.write("\n".join(m3u_content))

            print(f"\n📂 {created} kanal '{output_filename}' dosyasına kaydedildi.")
        else:
            print("\nℹ️ Hiçbir link oluşturulamadı.")

        print("\n🎉 Tamamlandı!")



if __name__ == "__main__":
    main()
