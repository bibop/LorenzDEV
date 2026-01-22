#!/usr/bin/env python3
"""
Analisi migrazione SharePoint: verifica file migrati vs file già presenti sul NAS
"""

import os
import hashlib
from pathlib import Path
from collections import defaultdict
import json

# Configurazione
SHAREPOINT_DIR = "/Volumes/Hyperworks/Hypertransfer/09_ARCHIVES/SharePoint_HLI_Full"
NAS_SEARCH_PATHS = [
    "/Volumes/Hyperworks/Hypertransfer/01_GOVERNANCE",
    "/Volumes/Hyperworks/Hypertransfer/02_COMMERCIAL",
    "/Volumes/Hyperworks/Hypertransfer/03_FINANCIAL",
    "/Volumes/Hyperworks/Hypertransfer/04_PROJECTS",
    "/Volumes/Hyperworks/Hypertransfer/05_TECHNICAL",
    "/Volumes/Hyperworks/Hypertransfer/06_OPERATIONS",
    "/Volumes/Hyperworks/Hypertransfer/07_HR",
    "/Volumes/Hyperworks/Hypertransfer/08_COMMUNICATIONS",
    "/Volumes/Hyperworks/Hypertransfer/09_ARCHIVES/GoogleDrive_Full",
    "/Volumes/Hyperworks/Hypertransfer/09_ARCHIVES/OneDrive_HLI_Full",
    "/Volumes/Hyperworks/Hypertransfer/09_ARCHIVES/OneDrive_SRL_Full",
    "/Volumes/Hyperworks/Hypertransfer/09_ARCHIVES/iCloudDrive_Full",
]

REPORT_FILE = os.path.expanduser("~/Documents/AI/Scanner_Duplicati/sharepoint_analysis_report.txt")
JSON_FILE = os.path.expanduser("~/Documents/AI/Scanner_Duplicati/sharepoint_analysis.json")

def calculate_hash(file_path, quick=False):
    """Calcola hash MD5 del file"""
    try:
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            if quick:
                # Quick hash: primi e ultimi 64KB
                chunk = f.read(65536)
                hasher.update(chunk)
                f.seek(-min(65536, os.path.getsize(file_path)), 2)
                chunk = f.read(65536)
                hasher.update(chunk)
            else:
                # Full hash
                while chunk := f.read(65536):
                    hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        return None

def scan_sharepoint_files():
    """Scansiona tutti i file SharePoint"""
    print(f"\n📊 Scansione cartella SharePoint: {SHAREPOINT_DIR}")

    files = []
    total_size = 0

    for root, dirs, filenames in os.walk(SHAREPOINT_DIR):
        # Skip file di sistema
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in filenames:
            if filename in ['.DS_Store', 'Icon\r', 'Thumbs.db', 'desktop.ini']:
                continue

            file_path = os.path.join(root, filename)
            try:
                size = os.path.getsize(file_path)
                rel_path = os.path.relpath(file_path, SHAREPOINT_DIR)

                files.append({
                    'path': file_path,
                    'rel_path': rel_path,
                    'name': filename,
                    'size': size,
                    'hash': None
                })
                total_size += size

                if len(files) % 100 == 0:
                    print(f"  Trovati {len(files)} file... ({total_size / (1024**3):.2f} GB)")

            except Exception as e:
                print(f"  ⚠️ Errore lettura {filename}: {e}")

    print(f"✓ Trovati {len(files)} file SharePoint ({total_size / (1024**3):.2f} GB)")
    return files, total_size

def build_nas_hash_index():
    """Crea indice hash di tutti i file già presenti nel NAS"""
    print(f"\n🔍 Scansione file esistenti sul NAS...")

    hash_index = defaultdict(list)  # hash -> [(path, size), ...]
    total_files = 0

    for search_path in NAS_SEARCH_PATHS:
        if not os.path.exists(search_path):
            continue

        print(f"  Scansione: {os.path.basename(search_path)}")

        for root, dirs, filenames in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in filenames:
                if filename in ['.DS_Store', 'Icon\r', 'Thumbs.db', 'desktop.ini']:
                    continue

                file_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(file_path)
                    file_hash = calculate_hash(file_path, quick=True)

                    if file_hash:
                        hash_index[file_hash].append({
                            'path': file_path,
                            'size': size,
                            'name': filename
                        })
                        total_files += 1

                        if total_files % 500 == 0:
                            print(f"    Indicizzati {total_files} file...")

                except Exception as e:
                    pass

    print(f"✓ Indicizzati {total_files} file esistenti sul NAS")
    return hash_index

def analyze_sharepoint_vs_nas(sharepoint_files, nas_hash_index):
    """Confronta file SharePoint con quelli già presenti sul NAS"""
    print(f"\n🔬 Analisi duplicati e file unici...")

    unique_files = []
    duplicate_files = []

    for idx, file_info in enumerate(sharepoint_files):
        if idx % 100 == 0 and idx > 0:
            print(f"  Analizzati {idx}/{len(sharepoint_files)} file...")

        # Calcola hash del file SharePoint
        file_hash = calculate_hash(file_info['path'], quick=True)
        file_info['hash'] = file_hash

        if not file_hash:
            unique_files.append(file_info)
            continue

        # Cerca se esiste già nel NAS
        if file_hash in nas_hash_index:
            matches = nas_hash_index[file_hash]
            file_info['duplicates'] = matches
            duplicate_files.append(file_info)
        else:
            unique_files.append(file_info)

    return unique_files, duplicate_files

def generate_report(sharepoint_files, unique_files, duplicate_files, total_size):
    """Genera report testuale e JSON"""

    # Report testuale
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ANALISI MIGRAZIONE SHAREPOINT → NAS\n")
        f.write("="*80 + "\n\n")

        f.write(f"📊 RIEPILOGO GENERALE\n")
        f.write(f"─" * 80 + "\n")
        f.write(f"File totali SharePoint:     {len(sharepoint_files)}\n")
        f.write(f"Dimensione totale:          {total_size / (1024**3):.2f} GB\n")
        f.write(f"File unici (nuovi):         {len(unique_files)} ({len(unique_files)/len(sharepoint_files)*100:.1f}%)\n")
        f.write(f"File duplicati (già su NAS): {len(duplicate_files)} ({len(duplicate_files)/len(sharepoint_files)*100:.1f}%)\n")
        f.write("\n")

        # Statistiche dimensioni
        unique_size = sum(f['size'] for f in unique_files)
        dup_size = sum(f['size'] for f in duplicate_files)

        f.write(f"💾 DIMENSIONI\n")
        f.write(f"─" * 80 + "\n")
        f.write(f"File unici:                 {unique_size / (1024**3):.2f} GB\n")
        f.write(f"File duplicati:             {dup_size / (1024**3):.2f} GB\n")
        f.write(f"Spazio risparmiato:         {dup_size / (1024**3):.2f} GB (se si cancellassero i duplicati)\n")
        f.write("\n")

        # Top 20 file duplicati per dimensione
        if duplicate_files:
            f.write(f"\n📁 TOP 20 FILE DUPLICATI PIÙ GRANDI\n")
            f.write(f"─" * 80 + "\n")
            dup_sorted = sorted(duplicate_files, key=lambda x: x['size'], reverse=True)[:20]

            for i, dup in enumerate(dup_sorted, 1):
                f.write(f"\n{i}. {dup['name']}\n")
                f.write(f"   Dimensione: {dup['size'] / (1024**2):.2f} MB\n")
                f.write(f"   SharePoint: {dup['rel_path']}\n")
                f.write(f"   Già presente in:\n")
                for match in dup.get('duplicates', [])[:3]:
                    f.write(f"     - {match['path']}\n")

        # Esempi file unici importanti
        f.write(f"\n📝 ESEMPI FILE UNICI (NON ANCORA SUL NAS)\n")
        f.write(f"─" * 80 + "\n")

        # Filtra per estensioni importanti
        important_ext = {'.docx', '.xlsx', '.pptx', '.pdf', '.doc', '.xls', '.ppt'}
        important_unique = [f for f in unique_files if any(f['name'].lower().endswith(ext) for ext in important_ext)]
        important_unique_sorted = sorted(important_unique, key=lambda x: x['size'], reverse=True)[:30]

        for i, file in enumerate(important_unique_sorted, 1):
            f.write(f"{i}. {file['rel_path']} ({file['size'] / (1024**2):.2f} MB)\n")

    # Report JSON (per elaborazioni successive)
    json_data = {
        'summary': {
            'total_files': len(sharepoint_files),
            'total_size_gb': round(total_size / (1024**3), 2),
            'unique_files': len(unique_files),
            'duplicate_files': len(duplicate_files),
            'unique_size_gb': round(sum(f['size'] for f in unique_files) / (1024**3), 2),
            'duplicate_size_gb': round(sum(f['size'] for f in duplicate_files) / (1024**3), 2),
        },
        'unique_files': [
            {
                'path': f['rel_path'],
                'name': f['name'],
                'size_mb': round(f['size'] / (1024**2), 2)
            }
            for f in unique_files[:1000]  # Primi 1000
        ],
        'duplicate_files': [
            {
                'path': f['rel_path'],
                'name': f['name'],
                'size_mb': round(f['size'] / (1024**2), 2),
                'duplicate_locations': [m['path'] for m in f.get('duplicates', [])[:5]]
            }
            for f in duplicate_files[:1000]  # Primi 1000
        ]
    }

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Report salvati:")
    print(f"   - {REPORT_FILE}")
    print(f"   - {JSON_FILE}")

def main():
    print("\n" + "="*80)
    print("ANALISI MIGRAZIONE SHAREPOINT")
    print("="*80)

    # 1. Scansiona file SharePoint
    sharepoint_files, total_size = scan_sharepoint_files()

    # 2. Costruisci indice hash NAS
    nas_hash_index = build_nas_hash_index()

    # 3. Confronta e trova duplicati
    unique_files, duplicate_files = analyze_sharepoint_vs_nas(sharepoint_files, nas_hash_index)

    # 4. Genera report
    generate_report(sharepoint_files, unique_files, duplicate_files, total_size)

    print("\n" + "="*80)
    print("ANALISI COMPLETATA")
    print("="*80)
    print(f"\n📊 File totali: {len(sharepoint_files)}")
    print(f"✨ File unici (nuovi): {len(unique_files)} ({len(unique_files)/len(sharepoint_files)*100:.1f}%)")
    print(f"🔄 File duplicati (già su NAS): {len(duplicate_files)} ({len(duplicate_files)/len(sharepoint_files)*100:.1f}%)")
    print(f"\n💡 Vedi dettagli in: {REPORT_FILE}")

if __name__ == '__main__':
    main()
