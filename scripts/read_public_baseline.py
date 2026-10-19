"""Read public pages only; retain HTML and a compact JSON-LD baseline."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
import json, re

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'evidence' / '2026-10-19'
ROOT.mkdir(parents=True, exist_ok=True)
PATHS = ['/', '/faq-irelax-au/', '/product/ogawa-biovis/', '/product/healer-x-4d-massage-chair/', '/robots.txt', '/llms.txt', '/sitemap_index.xml']

def read(path):
    result = {'url': 'https://irelax.com.au' + path}
    try:
        with urlopen(Request(result['url'], headers={'User-Agent': 'Mozilla/5.0 (compatible; SiteReview/1.0)'}), timeout=35) as response:
            raw = response.read().decode('utf-8', errors='replace')
            result.update(status=response.status, final_url=response.url)
        name = path.strip('/').replace('/', '_') or 'home'
        (ROOT / (name + '.txt')).write_text(raw, encoding='utf-8')
        blocks = re.findall(r'<script\b[^>]*type=[\"\x27]application/ld\+json[\"\x27][^>]*>(.*?)</script\s*>', raw, re.I | re.S)
        result['jsonld_blocks'] = len(blocks)
        result['jsonld_errors'] = []
        nodes = []
        def walk(v):
            if isinstance(v, dict):
                if '@type' in v: nodes.append(v)
                for value in v.values(): walk(value)
            elif isinstance(v, list):
                for value in v: walk(value)
        for i, block in enumerate(blocks):
            try: walk(json.loads(block))
            except ValueError as e: result['jsonld_errors'].append({'block': i+1, 'error': str(e)})
        result['entities'] = [{k:n[k] for k in ['@type','name','brand','sku','mpn','latitude','longitude','sameAs'] if k in n} for n in nodes if n.get('@type') in ['ProductGroup','Product','Organization','GeoCoordinates','Person']]
        result['types'] = [n['@type'] for n in nodes]
    except Exception as e:
        result['error'] = str(e)
    return result

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(read, PATHS))
(ROOT / 'baseline.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(results, ensure_ascii=False, indent=2))
