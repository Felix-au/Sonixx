# Sonixx by Felix-au — Virtual Audio Router Guide

Sonixx by Felix-au is a high-performance virtual audio router that allows you to capture audio from individual applications and microphones, mixing them into a single virtual microphone output.

## 🚀 How to Run (Development)

To run the application from source code using the **uv** package manager:

1. Ensure you have [uv](https://github.com/astral-sh/uv) installed (`pip install uv`).
2. Sync the environment and dependencies:
   ```bash
   uv sync
   ```
3. Run the application:
   ```bash
   uv run main.py
   ```

> [!NOTE]
> The application will automatically request Administrator privileges on startup. This is required for system-level audio hooks and driver identification.

## 📦 How to Build (.EXE)

To create a standalone Windows executable using the provided spec file:

1. Build using PyInstaller through uv:
   ```bash
   uv run pyinstaller Sonixx by Felix-auAudioRouter.spec --noconfirm
   ```
2. The finished executable will be located in the `dist/Sonixx by Felix-auAudioRouter/` directory.

## 🛠 Features

- **Per-App Capture**: Mix audio from specific games, browsers, or music players without capturing system-wide sounds.
- **Jitter Buffering**: Implements hardware-synced mixing and 210ms buffering for glitch-free, high-fidelity audio.
- **Monitor Mix**: A toggle to hear exactly what is being sent to the virtual microphone through your own headphones.
- **Mono-to-Stereo**: Automatically up-mixes mono microphones to stereo for consistent quality.

## ⚠️ Important Notes

- **VB-Cable**: The app requires the VB-Cable driver. If not found, the app will offer to download and install it for you.
- **Admin Rights**: Required for renaming the virtual device to "Sonixx by Felix-au" and for certain system-level audio hooks.
- **Scanning**: Clicking "Scan" will briefly stop the audio router to ensure a clean capture of new application processes.
