# 📦 MaichiNinite

> Install semua app favorit kamu dalam satu command — Windows & Android

---

## ⚡ Cara Pakai

### Windows (PowerShell)

Buka **PowerShell as Administrator**, lalu jalankan:

```powershell
irm https://raw.githubusercontent.com/USERNAME/Maichi-ninite/main/windows/Maichi.ps1 | iex
```

Atau kalau mau langsung install recommended package:

```powershell
$s = irm https://raw.githubusercontent.com/USERNAME/Maichi-ninite/main/windows/Maichi.ps1
iex "& { $s } -Recommended"
```

### Android (Termux)
*Coming soon...*

---

## 📋 Daftar App

### 🌐 Browser
| App | Winget ID |
|-----|-----------|
| Google Chrome | `Google.Chrome` |
| Firefox | `Mozilla.Firefox` |
| Brave | `Brave.Brave` |
| Opera GX | `Opera.OperaGX` |

### 🎵 Media
| App | Winget ID |
|-----|-----------|
| VLC | `VideoLAN.VLC` |
| OBS Studio | `OBSProject.OBSStudio` |
| Audacity | `Audacity.Audacity` |
| Spotify | `Spotify.Spotify` |

### 🛠️ Developer
| App | Winget ID |
|-----|-----------|
| VS Code | `Microsoft.VisualStudioCode` |
| Git | `Git.Git` |
| Node.js | `OpenJS.NodeJS.LTS` |
| Python | `Python.Python.3` |
| Docker | `Docker.DockerDesktop` |

### 🎮 Gaming
| App | Winget ID |
|-----|-----------|
| Steam | `Valve.Steam` |
| Epic Games | `EpicGames.EpicGamesLauncher` |
| RetroArch | `Libretro.RetroArch` |
| PCSX2 | `PCSX2.PCSX2` |
| Ryujinx | `Ryujinx.Ryujinx` |

---

## 🔧 Requirements

### Windows
- Windows 10 1809+ atau Windows 11
- [winget](https://aka.ms/getwinget) (biasanya sudah ada)
- PowerShell 5.1+

### Android
- Termux (dari F-Droid, **bukan Play Store**)

---

## 🤝 Kontribusi

Mau tambah app? Edit `apps/windows.json` atau `apps/android.json` dan buat Pull Request!

Format entry baru:
```json
{
  "name": "Nama App",
  "id": "Publisher.AppName",
  "desc": "Deskripsi singkat"
}
```

---

## 📄 License

MIT — bebas dipakai & dimodifikasi