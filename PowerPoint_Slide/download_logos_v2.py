#!/usr/bin/env python3
"""
Script per scaricare loghi aziendali da fonti multiple
con fallback e retry per Hyperworks Slide
"""

import os
import requests
from pathlib import Path
import time

# Directory di lavoro
LOGOS_DIR = Path("/Users/bibop/Documents/AI/Lorenz/PowerPoint_Slide/logos")
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

# Headers per simulare browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
    'Referer': 'https://www.google.com/',
}

# Loghi con fonti multiple (ordinate per priorità)
LOGO_SOURCES = {
    # Technology Supply Chain
    "thyssenkrupp": [
        "https://www.thyssenkrupp.com/media/images/logos/thyssenkrupp_logo_blue_rgb.png",
        "https://brand-logos.s3.amazonaws.com/thyssenkrupp-ag-logo.png",
    ],
    "hardt": [
        "https://hardt.global/wp-content/uploads/2023/03/Hardt-logo.png",
        "https://hardt.global/wp-content/themes/hardt/assets/images/logo.svg",
    ],
    "zeleros": [
        "https://zeleros.com/wp-content/uploads/2021/03/zeleros-logo.png",
        "https://zeleros.com/wp-content/themes/zeleros/images/logo.svg",
    ],
    "swisspod": [
        "https://swisspod.com/wp-content/uploads/2023/01/swisspod-logo.png",
        "https://swisspod.ch/wp-content/themes/swisspod/images/logo.svg",
    ],

    # Financial Structuring
    "unicredit": [
        "https://www.unicreditgroup.eu/content/dam/unicreditgroup/images/logo/UniCredit_logo_new.png",
        "https://brand-logos.s3.amazonaws.com/unicredit-logo.png",
    ],
    "brookfield": [
        "https://bfrealtyservices.com/wp-content/uploads/2023/04/Brookfield-Logo.png",
        "https://brand-logos.s3.amazonaws.com/brookfield-logo.png",
    ],
    "macquarie": [
        "https://www.macquarie.com/assets/macq/images/logo/macquarie-logo.svg",
        "https://brand-logos.s3.amazonaws.com/macquarie-group-logo.png",
    ],
    "eib": [
        "https://www.eib.org/img/eib-logo.png",
        "https://brand-logos.s3.amazonaws.com/eib-logo.png",
    ],

    # Operations
    "italferr": [
        "https://www.italferr.it/content/dam/italferr/images/logo_italferr.png",
        "https://brand-logos.s3.amazonaws.com/italferr-logo.png",
    ],

    # Project Management
    "webuild": [
        "https://www.webuildgroup.com/var/webuild/storage/images/media/images/webuild-logo/1234-1-ita-IT/webuild-logo.png",
        "https://brand-logos.s3.amazonaws.com/webuild-logo.png",
    ],
    "leonardo": [
        "https://www.leonardo.com/documents/20142/0/Leonardo_logo.png",
        "https://brand-logos.s3.amazonaws.com/leonardo-logo.png",
    ],
    "fastweb": [
        "https://www.fastweb.it/corporate/wp-content/themes/fastweb-corporate/images/logo.svg",
        "https://brand-logos.s3.amazonaws.com/fastweb-logo.png",
    ],
    "unito": [
        "https://www.unito.it/sites/default/files/logo_unito.png",
        "https://brand-logos.s3.amazonaws.com/universita-torino-logo.png",
    ],
}

def download_logo(name: str, urls: list) -> bool:
    """Scarica un logo provando più fonti"""
    filepath = LOGOS_DIR / f"{name}.png"

    if filepath.exists():
        print(f"  [SKIP] {name} - già esistente")
        return True

    for url in urls:
        try:
            print(f"  [PROVO] {name} da {url[:50]}...")
            response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)

            if response.status_code == 200 and len(response.content) > 1000:
                # Verifica che sia effettivamente un'immagine
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type or url.endswith(('.png', '.svg', '.jpg')):
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"  [OK] {name} - scaricato ({len(response.content) // 1024}KB)")
                    return True

        except Exception as e:
            print(f"  [FAIL] {url[:40]}... - {str(e)[:50]}")

        time.sleep(0.5)  # Rispetto rate limiting

    print(f"  [ERRORE] {name} - nessuna fonte disponibile")
    return False

def main():
    print("=" * 60)
    print("Download Loghi per Slide Hyperworks v2")
    print("=" * 60)

    success = []
    failed = []

    for name, urls in LOGO_SOURCES.items():
        result = download_logo(name, urls)
        if result:
            success.append(name)
        else:
            failed.append(name)

    print("\n" + "=" * 60)
    print(f"Completato: {len(success)}/{len(LOGO_SOURCES)} loghi scaricati")

    if success:
        print(f"\n✅ Scaricati con successo:")
        for name in success:
            print(f"  - {name}")

    if failed:
        print(f"\n❌ Loghi da scaricare manualmente:")
        for name in failed:
            print(f"  - {name}")
        print("\n📌 Scarica manualmente da:")
        print("  - https://seeklogo.com")
        print("  - https://worldvectorlogo.com")
        print("  - Siti ufficiali (sezione Press/Media)")
        print("  - Cerca su Google: 'logo nome_azienda PNG transparent'")

    print(f"\n📁 Cartella loghi: {LOGOS_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
