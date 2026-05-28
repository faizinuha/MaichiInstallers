# ============================================================
#   Maichi - Windows App Installer
#   https://github.com/faizinuha/MaichiInstallers
# ============================================================

param(
    [switch]$Offline,
    [switch]$Recommended
)

# ── Config ───────────────────────────────────────────────────
$REPO_RAW   = "https://raw.githubusercontent.com/faizinuha/MaichiInstallers/main"
$JSON_URL   = "$REPO_RAW/apps/windows.json"
$SCRIPT_DIR = $PSScriptRoot
if (-not $SCRIPT_DIR) {
    $SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
$JSON_LOCAL = Join-Path $SCRIPT_DIR "apps\windows.json"
if (-not (Test-Path $JSON_LOCAL)) {
    $JSON_LOCAL = Join-Path $SCRIPT_DIR "..\apps\windows.json"
}
$TEMP_JSON  = "$env:TEMP\Maichi_windows.json"
$VERSION    = "1.0.0"

# ── Colors ───────────────────────────────────────────────────
function Write-Color {
    param([string]$Text, [string]$Color = "White", [switch]$NoNewline)
    if ($NoNewline) { Write-Host $Text -ForegroundColor $Color -NoNewline }
    else            { Write-Host $Text -ForegroundColor $Color }
}

function Write-Banner {
    Clear-Host
    Write-Color ""
    Write-Color "  ╔══════════════════════════════════════════╗" Cyan
    Write-Color "  ║       📦 Maichi v$VERSION           ║" Cyan
    Write-Color "  ║    Install apps Windows in one shot      ║" Cyan
    Write-Color "  ╚══════════════════════════════════════════╝" Cyan
    Write-Color ""
}

# ── Check winget ─────────────────────────────────────────────
function Check-Winget {
    try {
        $null = Get-Command winget -ErrorAction Stop
        return $true
    } catch {
        Write-Color "  ❌ winget tidak ditemukan!" Red
        Write-Color "  👉 Install dari: https://aka.ms/getwinget" Yellow
        Write-Color "     atau update Windows ke versi terbaru" Yellow
        Write-Color ""
        Read-Host "  Tekan Enter untuk keluar"
        exit 1
    }
}

# ── Load JSON ─────────────────────────────────────────────────
function Load-AppData {
    # Coba dari internet dulu
    if (-not $Offline) {
        try {
            Write-Color "  🔄 Mengambil data terbaru..." DarkGray
            $response = Invoke-WebRequest -Uri $JSON_URL -TimeoutSec 5 -ErrorAction Stop
            $response.Content | Out-File -FilePath $TEMP_JSON -Encoding UTF8
            Write-Color "  ✅ Data berhasil diperbarui" DarkGreen
            return (Get-Content $TEMP_JSON -Raw | ConvertFrom-Json)
        } catch {
            Write-Color "  ⚠️  Tidak bisa ambil data online, pakai data lokal..." Yellow
        }
    }

    # Fallback ke cache
    if (Test-Path $TEMP_JSON) {
        return (Get-Content $TEMP_JSON -Raw | ConvertFrom-Json)
    }

    # Fallback ke file lokal
    if (Test-Path $JSON_LOCAL) {
        return (Get-Content $JSON_LOCAL -Raw | ConvertFrom-Json)
    }

    Write-Color "  ❌ Tidak ada data app ditemukan!" Red
    exit 1
}

# ── Show Category Menu ────────────────────────────────────────
function Show-CategoryMenu {
    param($AppData)

    $categories = $AppData.categories.PSObject.Properties
    $keys = @()

    Write-Color "  Pilih kategori:" White
    Write-Color ""

    $i = 1
    foreach ($cat in $categories) {
        $label = $cat.Value.label
        $count = $cat.Value.apps.Count
        Write-Color "   $i)" Cyan -NoNewline
        Write-Color " $label " White -NoNewline
        Write-Color "($count apps)" DarkGray
        $keys += $cat.Name
        $i++
    }

    Write-Color ""
    Write-Color "   A)" Yellow -NoNewline
    Write-Color " ⭐ Recommended (paket terbaik)" White
    Write-Color "   B)" Yellow -NoNewline
    Write-Color " 🔍 Pilih semua dari semua kategori" White
    Write-Color "   0)" Red -NoNewline
    Write-Color " ❌ Keluar" White
    Write-Color ""

    $choice = Read-Host "  Pilihan kamu"

    switch ($choice.ToUpper()) {
        "0" { exit 0 }
        "A" { return "RECOMMENDED" }
        "B" { return "ALL" }
        default {
            $idx = [int]$choice - 1
            if ($idx -ge 0 -and $idx -lt $keys.Count) {
                return $keys[$idx]
            } else {
                Write-Color "  ⚠️  Pilihan tidak valid" Yellow
                Start-Sleep -Seconds 1
                return $null
            }
        }
    }
}

# ── Show App Checklist ────────────────────────────────────────
function Show-AppChecklist {
    param($Apps, [string]$Title)

    Write-Banner
    Write-Color "  $Title" Cyan
    Write-Color "  ─────────────────────────────────────────────" DarkGray
    Write-Color ""
    Write-Color "  Pilih app (pisahkan dengan koma, contoh: 1,3,5)" DarkGray
    Write-Color "  Ketik 'A' untuk pilih semua" DarkGray
    Write-Color ""

    $i = 1
    foreach ($app in $Apps) {
        Write-Color "   $i)" Cyan -NoNewline
        Write-Color " $($app.name)" White -NoNewline
        Write-Color " — $($app.desc)" DarkGray
        $i++
    }

    Write-Color ""
    Write-Color "   0)" Red -NoNewline
    Write-Color " ← Kembali" White
    Write-Color ""

    $input = Read-Host "  Pilihan kamu"

    if ($input -eq "0") { return @() }
    if ($input.ToUpper() -eq "A") { return $Apps }

    $selected = @()
    $parts = $input -split ","
    foreach ($p in $parts) {
        $p = $p.Trim()
        if ($p -match "^\d+$") {
            $idx = [int]$p - 1
            if ($idx -ge 0 -and $idx -lt $Apps.Count) {
                $selected += $Apps[$idx]
            }
        }
    }

    return $selected
}

# ── Install Apps ──────────────────────────────────────────────
function Install-Apps {
    param($SelectedApps)

    if ($SelectedApps.Count -eq 0) {
        Write-Color "  ⚠️  Tidak ada app yang dipilih" Yellow
        return
    }

    Write-Banner
    Write-Color "  🚀 Mulai instalasi $($SelectedApps.Count) app..." Cyan
    Write-Color "  ─────────────────────────────────────────────" DarkGray
    Write-Color ""

    $success = 0
    $failed  = 0
    $skipped = 0

    foreach ($app in $SelectedApps) {
        Write-Color "  📦 Installing: " White -NoNewline
        Write-Color $app.name Cyan

        # Cek apakah sudah terinstall
        $installed = winget list --id $app.id --exact -q 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Color "     ✅ Sudah terinstall, skip" DarkGreen
            $skipped++
            continue
        }

        # Install
        winget install --id $app.id --exact --silent --accept-package-agreements --accept-source-agreements
        
        if ($LASTEXITCODE -eq 0) {
            Write-Color "     ✅ Berhasil!" Green
            $success++
        } else {
            Write-Color "     ❌ Gagal (exit code: $LASTEXITCODE)" Red
            $failed++
        }

        Write-Color ""
    }

    # Summary
    Write-Color ""
    Write-Color "  ╔══════════════════════════════╗" Cyan
    Write-Color "  ║        HASIL INSTALASI       ║" Cyan
    Write-Color "  ╠══════════════════════════════╣" Cyan
    Write-Color "  ║  ✅ Berhasil  : " Cyan -NoNewline; Write-Color "$success" Green -NoNewline; Write-Color "             ║" Cyan
    Write-Color "  ║  ⏭️  Di-skip   : " Cyan -NoNewline; Write-Color "$skipped" Yellow -NoNewline; Write-Color "             ║" Cyan
    Write-Color "  ║  ❌ Gagal     : " Cyan -NoNewline; Write-Color "$failed" Red -NoNewline; Write-Color "             ║" Cyan
    Write-Color "  ╚══════════════════════════════╝" Cyan
    Write-Color ""
}

# ── Main Loop ─────────────────────────────────────────────────
function Main {
    Write-Banner
    Check-Winget

    Write-Color "  ⚡ Checking winget version..." DarkGray
    $wgVersion = (winget --version) 2>$null
    Write-Color "  ✅ winget $wgVersion ditemukan" DarkGreen
    Write-Color ""

    $appData = Load-AppData
    Write-Color ""

    # Mode recommended langsung
    if ($Recommended) {
        $allApps = @()
        $recIds  = $appData.recommended
        foreach ($cat in $appData.categories.PSObject.Properties) {
            foreach ($app in $cat.Value.apps) {
                if ($recIds -contains $app.id) {
                    $allApps += $app
                }
            }
        }
        Install-Apps $allApps
        Read-Host "  Tekan Enter untuk keluar"
        return
    }

    # Menu loop
    while ($true) {
        Write-Banner
        $choice = Show-CategoryMenu $appData

        if ($null -eq $choice) { continue }

        $appsToShow = @()
        $title = ""

        if ($choice -eq "RECOMMENDED") {
            $recIds = $appData.recommended
            foreach ($cat in $appData.categories.PSObject.Properties) {
                foreach ($app in $cat.Value.apps) {
                    if ($recIds -contains $app.id) {
                        $appsToShow += $app
                    }
                }
            }
            $title = "⭐ Recommended Apps"
        }
        elseif ($choice -eq "ALL") {
            foreach ($cat in $appData.categories.PSObject.Properties) {
                $appsToShow += $cat.Value.apps
            }
            $title = "📦 Semua Apps"
        }
        else {
            $appsToShow = $appData.categories.$choice.apps
            $title      = $appData.categories.$choice.label
        }

        $selected = Show-AppChecklist $appsToShow $title

        if ($selected.Count -gt 0) {
            Write-Banner
            Write-Color "  📋 App yang akan diinstall:" Cyan
            Write-Color ""
            foreach ($app in $selected) {
                Write-Color "     • $($app.name)" White
            }
            Write-Color ""

            $confirm = Read-Host "  Lanjut install? (Y/n)"
            if ($confirm.ToUpper() -ne "N") {
                Install-Apps $selected

                $again = Read-Host "  Install lagi? (Y/n)"
                if ($again.ToUpper() -eq "N") { break }
            }
        }
    }
}

Main
