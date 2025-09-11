import requests
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# === CONFIGURATION ===
M3U_SOURCE_FILE = 'M3U_list.txt'
SPECIAL_M3U_URLS = [
    "https://raw.githubusercontent.com/t23-02/bongda/refs/heads/main/bongda.m3u",
    "https://raw.githubusercontent.com/t23-02/bongda/refs/heads/main/bongda2.m3u"
]
EPG_SOURCES = [
    "https://lichphatsong.xyz/schedule/epg.xml",
    "https://raw.githubusercontent.com/AndKen14/EPG/refs/heads/main/guide.xml",
    "https://raw.githubusercontent.com/AndKen14/EPG/refs/heads/main/guide2.xml"
]
GROUP_ORDER = {
    "VTV Channels": 1,
    "Movies": 2,
    "Live": 3,
    "Sports": 4
}

# === FUNCTIONS ===

def load_m3u_urls():
    with open(M3U_SOURCE_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()] + SPECIAL_M3U_URLS

def parse_m3u(content):
    channels = []
    current = {}
    extra = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            if current and 'name' in current and 'url' in current:
                if extra:
                    current['extra'] = extra
                channels.append(current)
            current = {}
            extra = []
            params = dict(re.findall(r'([\w-]+)="([^"]+)"', line))
            current['params'] = {k.lower(): v for k, v in params.items()}
            name = line.split(',', 1)[-1].strip() if ',' in line else ''
            current['name'] = unquote(name) or current['params'].get('tvg-name', 'Unknown')
        elif line.startswith("http"):
            current['url'] = line
        elif line.startswith("#EXTVLCOPT") or line.startswith("#EXTGRP"):
            extra.append(line)

    if current and 'name' in current and 'url' in current:
        if extra:
            current['extra'] = extra
        channels.append(current)

    return channels

def normalize_name(name):
    return re.sub(r'\W+', '', name.lower())

def get_epg_mapping(url):
    mapping = {}
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        for channel in root.findall('.//channel'):
            tvg_id = channel.get('id')
            name = channel.find('display-name')
            if tvg_id and name is not None:
                mapping[normalize_name(name.text or '')] = tvg_id
    except Exception as e:
        print(f"Failed to load EPG from {url}: {e}")
    return mapping

def check_stream(url, timeout=3):
    try:
        headers = {'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18'}
        r = requests.get(url, headers=headers, timeout=timeout, stream=True)
        return r.status_code < 400
    except:
        return False

def is_low_quality(resolution):
    if not resolution:
        return False
    res = resolution.lower()
    if 'sd' in res:
        return True
    patterns = ['360p', '480p', '576p', '360', '480', '576', 'low']
    if any(p in res for p in patterns):
        return True
    numbers = re.findall(r'\d+', res)
    return any(int(n) < 720 for n in numbers)

def is_vtv_channel(name):
    patterns = [r'vtv[1-9]', r'vtv cần thơ']
    return any(re.search(p, name.lower()) for p in patterns)

def should_exclude(name, group):
    name = name.lower()
    exclude_patterns = {
        "VTV Channels": ['sfgo', 'mvtv'],
        "Movies": ['ajman tv', 'adsiz'],
        "Sports": ['cricket', 'rugby', 'nhl']
    }
    return any(p in name for p in exclude_patterns.get(group, []))

def detect_group(name):
    lname = name.lower()
    if is_vtv_channel(name):
        return "VTV Channels"
    elif any(x in lname for x in ['hbo', 'cinema', 'movie', 'dreamworks', 'hollywood', 'history', 'box']):
        return "Movies"
    elif any(x in lname for x in ['sport', 'football', 'live', 'epl', 'la liga', 'uefa', 'golf', 'tennis', 'match']):
        return "Sports"
    return "Live"  # fallback

def build_output(channels_by_group):
    lines = ['#EXTM3U']
    for group_name, channels in channels_by_group:
        channels.sort(key=lambda x: x['name'])
        for ch in channels:
            tvg_id = ch.get('tvg-id', '')
            logo = ch['params'].get('tvg-logo', '')
            resolution = ch.get('resolution', '')
            name_line = f"{ch['name']} - {resolution}" if resolution else ch['name']
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="{group_name}"'
            if logo:
                extinf += f' tvg-logo="{logo}"'
            extinf += f',{name_line}'
            lines.append(extinf)
            if 'extra' in ch:
                lines.extend([l for l in ch['extra'] if not l.startswith('#EXTINF')])
            lines.append(ch['url'])
    return '\n'.join(lines)

# === MAIN PROCESS ===

def main():
    start = time.time()
    all_channels = []
    m3u_urls = load_m3u_urls()

    # Load EPG maps
    epg_map = {}
    for epg_url in EPG_SOURCES:
        epg_map.update(get_epg_mapping(epg_url))

    for url in m3u_urls:
        try:
            print(f"Loading: {url}")
            content = requests.get(url, timeout=10).text
            channels = parse_m3u(content)

            for ch in channels:
                name = ch.get('name', '')
                res_match = re.search(r'(\d{3,4}[pP]|[1-8]K|HD|SD|FHD|UHD)', name)
                resolution = res_match.group(0).upper() if res_match else ''
                if is_low_quality(resolution):
                    continue
                group = detect_group(name)
                if should_exclude(name, group):
                    continue
                ch['group'] = group
                ch['resolution'] = resolution
                ch['tvg-id'] = epg_map.get(normalize_name(name), ch['params'].get('tvg-id', ''))
                all_channels.append(ch)
        except Exception as e:
            print(f"Failed to process {url}: {e}")

    print(f"\nRemoving duplicates...")
    seen_urls = set()
    unique_channels = []
    for ch in all_channels:
        if ch['url'] not in seen_urls:
            seen_urls.add(ch['url'])
            unique_channels.append(ch)

    print(f"Checking stream availability...")
    valid_channels = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_stream, ch['url']): ch for ch in unique_channels}
        for future in tqdm(as_completed(futures), total=len(futures)):
            ch = futures[future]
            if future.result():
                valid_channels.append(ch)

    # Grouping
    grouped = {}
    for ch in valid_channels:
        grp = ch['group']
        grouped.setdefault(grp, []).append(ch)

    sorted_groups = sorted(grouped.items(), key=lambda g: GROUP_ORDER.get(g[0], 99))

    # Save output
    with open("output.m3u", "w", encoding='utf-8') as f:
        f.write(build_output(sorted_groups))

    duration = time.time() - start
    print(f"\n✅ Done in {duration:.2f}s")
    print(f"Total valid channels: {len(valid_channels)}")
    for group, chs in sorted_groups:
        print(f"- {group}: {len(chs)} channels")

if __name__ == "__main__":
    main()
