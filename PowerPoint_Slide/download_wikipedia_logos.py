#!/usr/bin/env python3
"""
Script per scaricare loghi da Wikipedia/Wikimedia Commons
Fonti pubbliche con download diretto permesso
"""

import os
import requests
from pathlib import Path
import time

LOGOS_DIR = Path("/Users/bibop/Documents/AI/Lorenz/PowerPoint_Slide/logos")
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': 'LorenzBot/1.0 (Educational project; contact@example.com)',
    'Accept': 'image/*,*/*',
}

# URL diretti da Wikimedia Commons (thumb URLs che funzionano)
WIKIPEDIA_LOGOS = {
    # ThyssenKrupp - Logo blu
    "thyssenkrupp": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/ThyssenKrupp_AG_Logo_2015.svg/300px-ThyssenKrupp_AG_Logo_2015.svg.png",

    # UniCredit
    "unicredit": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Logo_UniCredit.svg/300px-Logo_UniCredit.svg.png",

    # Brookfield Asset Management
    "brookfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Brookfield_Asset_Management_logo.svg/300px-Brookfield_Asset_Management_logo.svg.png",

    # Macquarie Group
    "macquarie": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Macquarie_Group_logo.svg/300px-Macquarie_Group_logo.svg.png",

    # European Investment Bank (EIB)
    "eib": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/European_Investment_Bank_logo.svg/300px-European_Investment_Bank_logo.svg.png",

    # Italferr (Gruppo FS)
    "italferr": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Italferr_logo.svg/300px-Italferr_logo.svg.png",

    # Webuild (ex Salini Impregilo)
    "webuild": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Webuild_logo.svg/300px-Webuild_logo.svg.png",

    # Leonardo S.p.A.
    "leonardo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Leonardo_logo.svg/300px-Leonardo_logo.svg.png",

    # Fastweb
    "fastweb": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Fastweb_logo_2022.svg/300px-Fastweb_logo_2022.svg.png",

    # Università di Torino
    "unito": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Logo_Universit%C3%A0_di_Torino.svg/200px-Logo_Universit%C3%A0_di_Torino.svg.png",

    # Hardt Hyperloop - provo URL alternativo
    "hardt": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Hardt_Hyperloop_logo.svg/300px-Hardt_Hyperloop_logo.svg.png",

    # Zeleros - no Wikipedia, provo sito
    "zeleros": "https://zeleros.com/wp-content/uploads/2023/10/cropped-zeleros-logo-h-768x142.png",
}

def download_logo(name: str, url: str) -> bool:
    """Scarica un logo"""
    filepath = LOGOS_DIR / f"{name}.png"

    if filepath.exists():
        size = filepath.stat().st_size
        if size > 5000:  # Se già esiste ed è > 5KB, skip
            print(f"  [SKIP] {name} - già esistente ({size//1024}KB)")
            return True

    try:
        print(f"  [SCARICO] {name}...")
        response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            size = len(response.content)

            if size > 1000:  # Minimo 1KB
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"  [OK] {name} - {size//1024}KB")
                return True
            else:
                print(f"  [FAIL] {name} - file troppo piccolo ({size}B)")
        else:
            print(f"  [FAIL] {name} - HTTP {response.status_code}")

    except Exception as e:
        print(f"  [ERRORE] {name} - {str(e)[:60]}")

    return False

def main():
    print("=" * 60)
    print("Download Loghi da Wikipedia/Wikimedia Commons")
    print("=" * 60)

    success = []
    failed = []

    for name, url in WIKIPEDIA_LOGOS.items():
        result = download_logo(name, url)
        if result:
            success.append(name)
        else:
            failed.append(name)
        time.sleep(0.3)

    print("\n" + "=" * 60)
    print(f"Scaricati: {len(success)}/{len(WIKIPEDIA_LOGOS)}")

    if failed:
        print(f"\n❌ Mancanti: {', '.join(failed)}")

    # Verifica tutti i file
    print("\n📁 File nella cartella:")
    for f in sorted(LOGOS_DIR.glob("*.png")):
        size = f.stat().st_size
        print(f"  - {f.name} ({size//1024}KB)")

if __name__ == "__main__":
    main()
