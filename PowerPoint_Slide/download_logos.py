#!/usr/bin/env python3
"""
Script per scaricare loghi aziendali e creare la slide PowerPoint
con cerchi sovrapposti per Hyperworks
"""

import os
import requests
from pathlib import Path

# Directory di lavoro
LOGOS_DIR = Path("/Users/bibop/Documents/AI/Lorenz/PowerPoint_Slide/logos")
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

# Loghi da scaricare (fonti Wikipedia/Wikimedia Commons quando disponibili)
LOGO_SOURCES = {
    # Technology Supply Chain
    "thyssenkrupp": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/ThyssenKrupp_AG_Logo_2015.svg/1200px-ThyssenKrupp_AG_Logo_2015.svg.png",
        "category": "technology"
    },
    "hardt": {
        "url": "https://hardt.global/wp-content/uploads/2023/03/Hardt-logo.png",
        "category": "technology"
    },
    "zeleros": {
        "url": "https://zeleros.com/wp-content/uploads/2021/03/zeleros-logo.png",
        "category": "technology"
    },
    "swisspod": {
        "url": "https://swisspod.com/wp-content/uploads/2023/01/swisspod-logo.png",
        "category": "technology"
    },

    # Financial Structuring
    "unicredit": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Logo_UniCredit.svg/1200px-Logo_UniCredit.svg.png",
        "category": "financial"
    },
    "brookfield": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Brookfield_Asset_Management_logo.svg/1200px-Brookfield_Asset_Management_logo.svg.png",
        "category": "financial"
    },
    "macquarie": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Macquarie_Group_logo.svg/1200px-Macquarie_Group_logo.svg.png",
        "category": "financial"
    },
    "eib": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/European_Investment_Bank_logo.svg/1200px-European_Investment_Bank_logo.svg.png",
        "category": "financial"
    },

    # Operations
    "italferr": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Italferr_logo.svg/1200px-Italferr_logo.svg.png",
        "category": "operations"
    },

    # Project Management
    "webuild": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Webuild_logo.svg/1200px-Webuild_logo.svg.png",
        "category": "management"
    },
    "leonardo": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Leonardo_logo.svg/1200px-Leonardo_logo.svg.png",
        "category": "management"
    },
    "fastweb": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Fastweb_logo_2022.svg/1200px-Fastweb_logo_2022.svg.png",
        "category": "management"
    },
    "unito": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Logo_Universit%C3%A0_di_Torino.svg/1200px-Logo_Universit%C3%A0_di_Torino.svg.png",
        "category": "management"
    },
}

def download_logo(name: str, url: str) -> bool:
    """Scarica un logo e lo salva nella cartella logos"""
    filepath = LOGOS_DIR / f"{name}.png"

    if filepath.exists():
        print(f"  [SKIP] {name} - già esistente")
        return True

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"  [OK] {name} - scaricato ({len(response.content) // 1024}KB)")
        return True

    except Exception as e:
        print(f"  [ERRORE] {name} - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("Download Loghi per Slide Hyperworks")
    print("=" * 60)

    success = 0
    failed = []

    for name, info in LOGO_SOURCES.items():
        result = download_logo(name, info["url"])
        if result:
            success += 1
        else:
            failed.append(name)

    print("\n" + "=" * 60)
    print(f"Completato: {success}/{len(LOGO_SOURCES)} loghi scaricati")

    if failed:
        print(f"\nLoghi mancanti da scaricare manualmente:")
        for name in failed:
            print(f"  - {name}")
        print("\nCerca questi loghi su:")
        print("  - https://brandsoftheworld.com")
        print("  - https://seeklogo.com")
        print("  - Sito ufficiale dell'azienda (sezione Media/Press)")

    print("\nLoghi salvati in:", LOGOS_DIR)
    print("=" * 60)

if __name__ == "__main__":
    main()
