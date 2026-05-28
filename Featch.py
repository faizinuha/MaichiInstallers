"""
fetch_winget.py
===============
Auto-fetch top apps dari Chocolatey API (by download count)
lalu map ke Winget ID supaya bisa diinstall via winget.

Cara kerja:
  1. Ambil top apps per kategori dari Chocolatey API
  2. Map Chocolatey package ID → Winget package ID
  3. Simpan ke apps/windows.json

Jalankan:
  python3 scripts/fetch_winget.py           # fetch dari internet
  python3 scripts/fetch_winget.py --dry-run # test tanpa simpan
  python3 scripts/fetch_winget.py --offline # pakai data cache
"""

import json
import urllib.request
import urllib.parse
import sys
import os
import re
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# MAPPING: Chocolatey ID → Winget ID
# Ini perlu karena nama package bisa beda antar platform
# ─────────────────────────────────────────────────────────────────
CHOCO_TO_WINGET = {
    # Browser
    "googlechrome":          "Google.Chrome",
    "firefox":               "Mozilla.Firefox",
    "brave":                 "Brave.Brave",
    "microsoft-edge":        "Microsoft.Edge",
    "opera":                 "Opera.Opera",
    "operagx":               "Opera.OperaGX",
    "tor-browser":           "TorProject.TorBrowser",
    "vivaldi":               "Vivaldi.Vivaldi",

    # Media
    "vlc":                   "VideoLAN.VLC",
    "spotify":               "Spotify.Spotify",
    "obs-studio":            "OBSProject.OBSStudio",
    "handbrake":             "HandBrake.HandBrake",
    "audacity":              "Audacity.Audacity",
    "foobar2000":            "PeterPavlinek.foobar2000",
    "mpv":                   "mpv.net",
    "k-litecodecpackfull":   "CodecGuide.K-LiteCodecPack.Full",
    "mpc-hc":                "clsid2.mpc-hc",
    "itunes":                "Apple.iTunes",

    # Productivity
    "libreoffice-fresh":     "TheDocumentFoundation.LibreOffice",
    "notepadplusplus":       "Notepad++.Notepad++",
    "7zip":                  "7zip.7zip",
    "pdf24":                 "geeksoftwareGmbH.PDF24Creator",
    "obsidian":              "Obsidian.Obsidian",
    "notion":                "Notion.Notion",
    "sharex":                "ShareX.ShareX",
    "greenshot":             "Greenshot.Greenshot",
    "winrar":                "RARLab.WinRAR",
    "sumatrapdf":            "SumatraPDF.SumatraPDF",
    "foxitreader":           "Foxit.FoxitReader",
    "keepass":               "DominikReichl.KeePass",
    "bitwarden":             "Bitwarden.Bitwarden",

    # Developer
    "vscode":                "Microsoft.VisualStudioCode",
    "git":                   "Git.Git",
    "python3":               "Python.Python.3",
    "nodejs-lts":            "OpenJS.NodeJS.LTS",
    "nodejs":                "OpenJS.NodeJS",
    "microsoft-windows-terminal": "Microsoft.WindowsTerminal",
    "postman":               "Postman.Postman",
    "docker-desktop":        "Docker.DockerDesktop",
    "powershell-core":       "Microsoft.PowerShell",
    "putty":                 "PuTTY.PuTTY",
    "winscp":                "WinSCP.WinSCP",
    "filezilla":             "TimKosse.FileZilla.Client",
    "insomnia-rest-api-client": "Insomnia.Insomnia",
    "jetbrains-toolbox":     "JetBrains.Toolbox",
    "sublimetext4":          "SublimeHQ.SublimeText.4",

    # Communication
    "whatsapp":              "WhatsApp.WhatsApp",
    "telegram":              "Telegram.TelegramDesktop",
    "discord":               "Discord.Discord",
    "zoom":                  "Zoom.Zoom",
    "slack":                 "SlackTechnologies.Slack",
    "signal":                "OpenWhisperSystems.Signal",
    "skype":                 "Microsoft.Skype",
    "microsoft-teams":       "Microsoft.Teams",

    # Gaming
    "steam":                 "Valve.Steam",
    "epicgameslauncher":     "EpicGames.EpicGamesLauncher",
    "goggalaxy":             "GOG.Galaxy",
    "retroarch":             "Libretro.RetroArch",
    "pcsx2":                 "PCSX2.PCSX2",
    "rpcs3":                 "RPCS3.RPCS3",
    "ryujinx":               "Ryujinx.Ryujinx",
    "cemu":                  "Cemu.Cemu",
    "ppsspp":                "PPSSPP.PPSSPP",
    "dolphin":               "Dolphin.Dolphin",

    # Utility
    "cpu-z":                 "CPUID.CPU-Z",
    "gpu-z":                 "TechPowerUp.GPU-Z",
    "hwmonitor":             "CPUID.HWMonitor",
    "crystaldiskinfo":       "CrystalDewWorld.CrystalDiskInfo",
    "treesizefree":          "JAMSoftware.TreeSize.Free",
    "everything":            "voidtools.Everything",
    "bulk-rename-utility":   "TGRMN.BulkRenameUtility",
    "wiztree":               "AntibodySoftware.WizTree",
    "ccleaner":              "Piriform.CCleaner",
    "malwarebytes":          "Malwarebytes.Malwarebytes",
    "windirstat":            "WinDirStat.WinDirStat",
    "speccy":                "Piriform.Speccy",
    "recuva":                "Piriform.Recuva",
}

# ─────────────────────────────────────────────────────────────────
# KATEGORI: search terms untuk Chocolatey API per kategori
# ─────────────────────────────────────────────────────────────────
CATEGORIES_CONFIG = {
    "browser": {
        "label":   "🌐 Browser",
        "queries": ["browser", "chrome", "firefox"],
        "top":     8,
    },
    "media": {
        "label":   "🎵 Media & Player",
        "queries": ["media player", "video", "audio editor", "screen recorder"],
        "top":     10,
    },
    "productivity": {
        "label":   "📋 Productivity",
        "queries": ["office", "pdf", "note", "screenshot"],
        "top":     10,
    },
    "developer": {
        "label":   "🛠️  Developer Tools",
        "queries": ["developer", "git", "ide", "terminal", "nodejs"],
        "top":     12,
    },
    "communication": {
        "label":   "💬 Komunikasi",
        "queries": ["chat", "messaging", "video conference"],
        "top":     8,
    },
    "gaming": {
        "label":   "🎮 Gaming & Emulator",
        "queries": ["game launcher", "emulator", "steam"],
        "top":     10,
    },
    "utility": {
        "label":   "⚙️  Utility & System",
        "queries": ["system tool", "disk", "cpu", "cleaner"],
        "top":     10,
    },
}

RECOMMENDED_IDS = [
    "Google.Chrome",
    "VideoLAN.VLC",
    "Notepad++.Notepad++",
    "7zip.7zip",
    "Microsoft.VisualStudioCode",
    "Git.Git",
    "Discord.Discord",
    "ShareX.ShareX",
    "WhatsApp.WhatsApp",
    "Valve.Steam",
]

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "apps", "windows.json"
)


# ─────────────────────────────────────────────────────────────────
# Chocolatey API
# ─────────────────────────────────────────────────────────────────
CHOCO_API = "https://community.chocolatey.org/api/v2/Search()"

def fetch_choco(query: str, top: int = 30) -> list[dict]:
    """Fetch packages dari Chocolatey API sorted by download count."""
    params = urllib.parse.urlencode({
        "$filter": "IsLatestVersion",
        "$orderby": "DownloadCount desc",
        "$top": top,
        "searchTerm": query,
        "$select": "Id,Title,Summary,DownloadCount,Tags",
    })
    url = f"{CHOCO_API}?{params}"

    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "PocketNinite/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode())
            return raw.get("value", [])
    except Exception as e:
        print(f"  ⚠️  Gagal fetch '{query}': {e}")
        return []


def parse_package(pkg: dict) -> dict | None:
    """Convert Chocolatey package → format kita."""
    choco_id   = pkg.get("Id", "").lower()
    title      = pkg.get("Title", pkg.get("Id", ""))
    summary    = pkg.get("Summary", "")
    downloads  = pkg.get("DownloadCount", 0)

    # Cari winget ID dari mapping
    winget_id = CHOCO_TO_WINGET.get(choco_id)
    if not winget_id:
        return None  # Skip kalau tidak ada mapping

    # Bersihkan summary
    desc = re.sub(r'<[^>]+>', '', summary).strip()
    desc = desc[:80] + "..." if len(desc) > 80 else desc
    if not desc:
        desc = f"Downloaded {downloads:,} times on Chocolatey"

    return {
        "name":      title,
        "id":        winget_id,
        "choco_id":  choco_id,
        "desc":      desc,
        "downloads": downloads,
    }


# ─────────────────────────────────────────────────────────────────
# Main build
# ─────────────────────────────────────────────────────────────────
def build_from_api() -> dict:
    """Fetch semua kategori dari Chocolatey API."""
    result = {}

    for cat_key, config in CATEGORIES_CONFIG.items():
        print(f"\n  📂 Fetching: {config['label']}")
        seen_ids = set()
        apps     = []

        for query in config["queries"]:
            print(f"     🔍 Query: '{query}'", end="", flush=True)
            packages = fetch_choco(query, top=30)
            added = 0

            for pkg in packages:
                parsed = parse_package(pkg)
                if parsed and parsed["id"] not in seen_ids:
                    seen_ids.add(parsed["id"])
                    apps.append(parsed)
                    added += 1

                if len(apps) >= config["top"]:
                    break

            print(f" → +{added} apps")
            if len(apps) >= config["top"]:
                break

        # Sort by download count
        apps.sort(key=lambda x: x.get("downloads", 0), reverse=True)

        # Hapus field internal sebelum simpan
        clean_apps = []
        for app in apps[:config["top"]]:
            clean_apps.append({
                "name": app["name"],
                "id":   app["id"],
                "desc": app["desc"],
            })

        result[cat_key] = {
            "label": config["label"],
            "apps":  clean_apps,
        }
        print(f"     ✅ {len(clean_apps)} apps saved")

    return result


def build_fallback() -> dict:
    """Fallback: pakai existing windows.json kalau API gagal."""
    fallback_path = OUTPUT_PATH
    if os.path.exists(fallback_path):
        print("  ⚠️  Pakai data cache yang ada...")
        with open(fallback_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("categories", {})
    
    print("  ❌ Tidak ada cache! Pakai data minimal...")
    # Data minimal hardcode kalau semua gagal
    return {
        "browser": {
            "label": "🌐 Browser",
            "apps": [
                {"name": "Google Chrome", "id": "Google.Chrome",   "desc": "Browser paling populer"},
                {"name": "Firefox",       "id": "Mozilla.Firefox", "desc": "Open source browser"},
                {"name": "Brave",         "id": "Brave.Brave",     "desc": "Privacy browser"},
            ]
        }
    }


def save_json(categories: dict, dry_run: bool = False):
    total = sum(len(cat["apps"]) for cat in categories.values())
    data = {
        "version":    "1.0",
        "updated":    datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "source":     "chocolatey-api",
        "total_apps": total,
        "categories": categories,
        "recommended": RECOMMENDED_IDS,
    }

    if dry_run:
        print("\n  🧪 DRY RUN — tidak disimpan")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "\n  ...")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n  ✅ Tersimpan: {OUTPUT_PATH}")
    print(f"  📦 Total: {total} apps di {len(categories)} kategori")


def main():
    dry_run = "--dry-run" in sys.argv
    offline = "--offline" in sys.argv

    print("=" * 50)
    print("  PocketNinite — App Data Fetcher")
    print("=" * 50)

    if offline:
        print("\n  📴 Mode offline — pakai cache")
        categories = build_fallback()
    else:
        try:
            categories = build_from_api()
        except KeyboardInterrupt:
            print("\n\n  ⚠️  Dibatalkan, pakai fallback...")
            categories = build_fallback()

    save_json(categories, dry_run=dry_run)


if __name__ == "__main__":
    main()