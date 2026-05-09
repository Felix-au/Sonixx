<p align="center">
  <img src="assets/sonixx_logo.png" alt="Sonixx Logo" width="120" />
</p>

<h1 align="center">Sonixx</h1>
<p align="center">
  <strong>A high-performance virtual audio router for Windows</strong><br/>
  <em>Capture per-app audio &amp; microphones → mix → route to a single virtual mic</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?style=flat-square&logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/python-%3E%3D3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/audio_engine-WASAPI-blueviolet?style=flat-square" alt="WASAPI" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Why Sonixx?](#-why-sonixx)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Building a Standalone Executable](#-building-a-standalone-executable)
- [Usage Guide](#-usage-guide)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Dependencies](#-dependencies)
- [Troubleshooting](#-troubleshooting)
- [Author](#-author)

---

## 🔊 Overview

**Sonixx** is a lightweight, native Windows desktop application that acts as a virtual audio mixer and router. It lets you selectively capture audio from individual applications (games, browsers, music players, VoIP clients) and physical microphones, then blends them into a single **virtual microphone output** powered by VB-Cable.

> **Use-case example:** You're in a Discord or VALORANT voice call and want to play background music from Spotify *and* your mic simultaneously — Sonixx makes that seamless with per-source volume controls, muting, and real-time peak metering.

The entire stack runs locally with zero cloud dependencies — no accounts, no telemetry, no latency overhead.

---

## 🎯 Why Sonixx?

> **There is not a single soundboard on the market that routes live audio between applications.**

Every existing "soundboard" — Voicemod, Soundpad, EXP Soundboard, Resanance, you name it — works the same way: you load **pre-downloaded MP3/WAV files** and trigger them with hotkeys. They are glorified audio-file players wired to a virtual mic.

Sonixx is fundamentally different:

| | Traditional Soundboards | Sonixx |
|---|---|---|
| **Audio source** | Pre-downloaded `.mp3` / `.wav` files | **Live audio** from any running application |
| **How it works** | Plays a static file to a virtual mic | Captures real-time audio streams via Windows WASAPI per-process loopback and mixes them on-the-fly |
| **Use case** | Sound effects, memes, pre-recorded clips | Stream Spotify, browser audio, game sounds, or *any* app's live output directly into Discord/Zoom/OBS — alongside your mic |
| **Per-app control** | ❌ N/A | ✅ Independent volume, mute, and enable per process |
| **Mic passthrough** | ❌ Separate tool needed | ✅ Built-in — mix your mic with app audio in one pipeline |

If you've ever wanted to share a YouTube video's audio in a call, play your Spotify playlist through your mic in VALORANT, or route a DAW's output into OBS — without manually recording and re-uploading files — Sonixx is the tool that finally makes it possible.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Per-App Audio Capture** | Selectively capture audio from individual processes (Chrome, Spotify, VALORANT, OBS, etc.) using the `process-audio-capture` DLL via named pipes — no system-wide loopback needed. |
| **Microphone Mixing** | Add one or more physical microphones as input sources, each with independent volume and enable/disable toggles. |
| **Hardware-Synced Mixing** | All audio mixing runs inside PyAudio WASAPI callbacks, synced to the hardware clock. Zero background-thread drift. |
| **Jitter Buffering** | A 210 ms (~10 chunk) pre-buffer absorbs scheduling jitter, preventing glitches and dropouts. |
| **Mono → Stereo Upmix** | Mono microphones are automatically upmixed to stereo for consistent, high-quality output. |
| **Loopback Monitor** | A "Monitor Mix" toggle lets you hear exactly what is being sent to the virtual mic through your own headphones in real-time. |
| **Master Controls** | Global master volume slider (0–200%), master mute button, and a real-time peak meter with green/orange/red level indicators. |
| **Per-Source Controls** | Each application and microphone source has its own volume slider (0–200%), enable/disable switch, remove button, and peak meter. |
| **System Tray Integration** | Minimise to the system tray instead of closing. Restore with a double-click. |
| **Auto-Start with Windows** | Optional registry-based autostart so Sonixx launches on boot. |
| **VB-Cable Auto-Install** | If the VB-Cable driver is not detected, Sonixx offers a one-click silent installation from the bundled driver pack. |
| **Device Renaming** | Rename the VB-Cable device to "Sonixx" in the Windows audio registry so it appears as a branded device in apps like Discord. |
| **Hotkey Support** | `Ctrl+Alt+M` toggles master mute globally, even when the window is minimised. |
| **Dark UI** | A polished, dark-themed interface built with CustomTkinter — designed to feel like a native Windows 11 audio panel. |
| **Self-Exclusion** | Sonixx automatically excludes its own process from the audio capture scan to prevent feedback loops. |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Sonixx Application                 │
│                                                      │
│  ┌────────────┐   ┌────────────┐   ┌──────────────┐ │
│  │ App Source  │   │ App Source  │   │  Mic Source   │ │
│  │ (Chrome)   │   │ (Spotify)  │   │  (Realtek)   │ │
│  │            │   │            │   │              │ │
│  │ Named Pipe │   │ Named Pipe │   │ WASAPI Input │ │
│  │ + PAC DLL  │   │ + PAC DLL  │   │ (Callback)   │ │
│  └─────┬──────┘   └─────┬──────┘   └──────┬───────┘ │
│        │                │                  │         │
│        └────────┬───────┘                  │         │
│                 │                          │         │
│           ┌─────▼──────────────────────────▼───┐     │
│           │       AudioRouter._out_cb()        │     │
│           │   (Hardware-synced WASAPI callback) │     │
│           │                                    │     │
│           │  Mix all sources → master vol/mute │     │
│           │  → clip to [-1.0, 1.0]             │     │
│           └────────┬───────────────┬───────────┘     │
│                    │               │                 │
│            ┌───────▼───┐   ┌───────▼──────┐         │
│            │ VB-Cable  │   │   Monitor    │         │
│            │  Output   │   │  (Loopback)  │         │
│            │ (Virtual  │   │  Headphones  │         │
│            │   Mic)    │   │              │         │
│            └───────────┘   └──────────────┘         │
└──────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Role |
|---|---|
| **`main.py`** | Entry point. Requests admin elevation via `ShellExecuteW` and launches the UI. |
| **`app/ui.py`** | Full CustomTkinter GUI — header, source panels, output controls, system tray, settings. |
| **`app/audio_router.py`** | Audio engine: `AppAudioSource` (per-process capture via named pipes), `MicSource` (WASAPI mic input), `AudioRouter` (mixer + output callbacks). |
| **`app/driver.py`** | VB-Cable detection, silent installation, registry-based device renaming, and Windows autostart management. |

---

## 📦 Prerequisites

| Requirement | Details |
|---|---|
| **Windows 10 / 11** | WASAPI APIs are Windows-only. |
| **Python ≥ 3.13** | Required for the `uv` lockfile and modern typing features. |
| **[uv](https://github.com/astral-sh/uv)** | Fast Python package manager. Install via `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh`. |
| **Administrator privileges** | Required for VB-Cable installation, device renaming, and system-level audio hooks. |
| **VB-Cable** *(auto-installed)* | Virtual audio cable driver. Sonixx bundles `VBCABLE_Driver_Pack45.zip` and will offer to install it on first launch if not detected. |

---

## 🚀 Quick Start

### Option A — Using `run.bat` (Recommended)

Simply double-click the included batch file:

```
run.bat
```

This will:
1. Verify Python is installed.
2. Run `uv sync` to install all dependencies.
3. Launch Sonixx with `uv run main.py`.

> **Note:** The application will automatically request Administrator privileges on startup.

### Option B — Manual

```bash
# 1. Clone the repository
git clone https://github.com/Felix-au/Sonixx.git
cd Sonixx

# 2. Install dependencies
uv sync

# 3. Launch
uv run main.py
```

---

## 📦 Building a Standalone Executable

Create a single-file `.exe` with all assets bundled:

```bash
uv run pyinstaller SonixxAudioRouter.spec --noconfirm
```

The compiled executable will be at:

```
dist/SonixxAudioRouter.exe
```

The spec file automatically bundles:
- `assets/` — Logo, icons, and SVGs
- `VBCABLE_Driver_Pack45.zip` — VB-Cable installer
- `customtkinter` and `process_audio_capture` — Collected hidden imports

---

## 📖 Usage Guide

### 1. First Launch — Driver Setup

If VB-Cable is not detected, Sonixx displays a setup screen:

- Click **⚡ Install VB-Cable Driver** for a silent, automated install.
- Or install manually and click **⟳ Already installed — Refresh**.

### 2. Adding Application Sources

1. Play audio in the applications you want to capture (e.g., open Spotify, a YouTube tab, a game).
2. Click **⟳ Scan** in the Applications panel.
3. Detected processes appear as source rows with individual controls.
4. Toggle the **switch** on each source to include it in the mix.

> **Tip:** Scanning briefly pauses the audio router to ensure a clean process enumeration.

### 3. Adding Microphone Sources

1. Select your microphone from the dropdown in the **🎤 Microphones** section.
2. Click **+ Add** to create a mic source row.
3. Toggle it on and adjust volume.

### 4. Configuring Output

- **Loopback Source:** Select which output device to capture system-wide audio from (usually your speakers/headphones).
- **Monitor Mix:** Enable to hear the mixed output in your headphones.
- **Master Volume:** 0–200% with real-time peak metering.
- **Master Mute:** Click 🔊 or press `Ctrl+Alt+M`.

### 5. Starting the Router

1. Click **▶ Start** — the status indicator turns green: `● Routing`.
2. In your target application (Discord, VALORANT, etc.), select **"Sonixx"** or **"CABLE Output"** as the microphone input.
3. Click **■ Stop** to halt routing.

### 6. Device Renaming

Click **Rename to "Sonixx" (Admin)** to change the VB-Cable device name in the Windows audio registry. Applications will then display the device as "Sonixx" instead of "CABLE Output".

---

## ⌨ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + Alt + M` | Toggle master mute (works globally, even when minimised) |

---

## ⚙ Configuration

Settings are persisted at:

```
%APPDATA%\Sonixx\settings.json
```

| Key | Type | Default | Description |
|---|---|---|---|
| `tray` | `bool` | `true` | Minimise to system tray on window close |
| `startup` | `bool` | `false` | Launch Sonixx on Windows startup (registry entry) |
| `theme` | `string` | `"dark"` | UI theme (currently only dark is supported) |

---

## 📁 Project Structure

```
Sonixx/
├── main.py                     # Entry point (admin elevation + app launch)
├── run.bat                     # One-click launcher script
├── pyproject.toml              # Project metadata & dependencies (uv/pip)
├── requirements.txt            # Fallback pip requirements
├── settings.json               # Default settings template
├── SonixxAudioRouter.spec      # PyInstaller build specification
├── VBCABLE_Driver_Pack45.zip   # Bundled VB-Cable driver installer
│
├── app/
│   ├── __init__.py             # Package init
│   ├── ui.py                   # CustomTkinter GUI (538 lines)
│   ├── audio_router.py         # Audio engine & mixer (481 lines)
│   └── driver.py               # VB-Cable driver management (173 lines)
│
├── assets/
│   ├── sonixx_logo.png         # Application logo (high-res)
│   ├── sonixx_logo.ico         # Windows icon
│   ├── github.png / .svg       # Footer profile icon
│   └── email.png / .svg        # Footer profile icon
│
├── build/                      # PyInstaller build artifacts
├── dist/                       # Compiled executable output
└── .venv/                      # Python virtual environment
```

---

## 📚 Dependencies

| Package | Purpose |
|---|---|
| [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) | Modern, dark-themed Tkinter UI framework |
| [`pyaudiowpatch`](https://github.com/s0d3s/PyAudioWPatch) | PyAudio fork with WASAPI loopback support |
| [`process-audio-capture`](https://pypi.org/project/process-audio-capture/) | Per-process audio capture via Windows APIs |
| [`numpy`](https://numpy.org/) | High-performance audio buffer manipulation |
| [`pycaw`](https://github.com/AndreMiras/pycaw) | Python Core Audio Windows library |
| [`psutil`](https://github.com/giampaolo/psutil) | Cross-platform process utilities |
| [`comtypes`](https://github.com/enthought/comtypes) | COM interface access for Windows audio APIs |
| [`Pillow`](https://python-pillow.org/) | Image processing for UI assets |
| [`keyboard`](https://github.com/boppreh/keyboard) | Global hotkey registration |
| [`pystray`](https://github.com/moses-palmer/pystray) | System tray icon and menu |
| [`tksvg`](https://github.com/TkinterEP/tksvg) | SVG rendering in Tkinter |
| [`pyinstaller`](https://pyinstaller.org/) | Executable bundling (dev dependency) |

---

## 🔧 Troubleshooting

<details>
<summary><strong>VB-Cable not detected after installation</strong></summary>

- Reboot your PC — some systems require a restart for the driver to register.
- Open **Sound Settings → Input Devices** and verify "CABLE Output" appears.
- Click **⟳ Already installed — Refresh** in the Sonixx setup screen.

</details>

<details>
<summary><strong>No applications appear after scanning</strong></summary>

- Ensure the target application is actively producing audio (e.g., play a song, join a call).
- Windows Audio Device Graph Isolation (`audiodg.exe`) and Sonixx itself are automatically excluded from the scan.
- Try closing and re-scanning.

</details>

<details>
<summary><strong>Audio glitches or crackling</strong></summary>

- Ensure your audio sample rates match (default: 48000 Hz). Mismatched rates between loopback and output devices can cause artifacts.
- The 210 ms jitter buffer should absorb most scheduling delays. If issues persist, check CPU load.

</details>

<details>
<summary><strong>Rename to "Sonixx" fails</strong></summary>

- Ensure you are running as Administrator.
- The rename modifies `HKEY_LOCAL_MACHINE` registry keys, which requires elevated privileges.
- Restart your audio applications after renaming for the change to take effect.

</details>

<details>
<summary><strong>"Run as Administrator" prompt keeps appearing</strong></summary>

- This is by design. Sonixx requires admin rights for driver installation, device renaming, and system-level audio hooks.
- If building a standalone `.exe`, right-click → Properties → Compatibility → "Run this program as an administrator" to skip the UAC prompt.

</details>

---

## 👤 Author

**Felix-au** (Harshit Soni)

- 🔗 GitHub: [github.com/Felix-au](https://github.com/Felix-au)
- 📧 Email: [harshit.soni.23cse@bmu.edu.in](mailto:harshit.soni.23cse@bmu.edu.in)

---

<p align="center">
  <sub>Built with ❤️ and too many late nights debugging WASAPI callbacks.</sub>
</p>
