"""Driver setup - VB-Cable auto-install and Felixx rename."""
import os, sys, zipfile, subprocess, winreg, urllib.request, tempfile
import pyaudiowpatch as pyaudio

SONIXX = "Sonixx"
SONIXX_FULL = "Sonixx by Felix-au"
VB_URL = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"


def find_wasapi(pa):
    for i in range(pa.get_host_api_count()):
        if pa.get_host_api_info_by_index(i)["type"] == pyaudio.paWASAPI:
            return i
    return 0


def is_cable_installed(pa):
    """Check if VB-Cable (or any virtual cable) is installed."""
    wi = find_wasapi(pa)
    for i in range(pa.get_device_count()):
        d = pa.get_device_info_by_index(i)
        if d["hostApi"] == wi and "cable" in d["name"].lower():
            return True
    return False


def get_cable_output_device(pa):
    """Get the CABLE Input device (where we WRITE audio TO)."""
    wi = find_wasapi(pa)
    for i in range(pa.get_device_count()):
        d = pa.get_device_info_by_index(i)
        if d["hostApi"] != wi:
            continue
        nl = d["name"].lower()
        if d["maxOutputChannels"] > 0 and ("cable input" in nl or ("cable" in nl and "input" in nl)):
            return {"index": i, "name": d["name"], "channels": d["maxOutputChannels"],
                    "rate": int(d["defaultSampleRate"])}
    # Fallback: any cable output device
    for i in range(pa.get_device_count()):
        d = pa.get_device_info_by_index(i)
        if d["hostApi"] == wi and d["maxOutputChannels"] > 0 and "cable" in d["name"].lower():
            return {"index": i, "name": d["name"], "channels": d["maxOutputChannels"],
                    "rate": int(d["defaultSampleRate"])}
    return None


def download_vbcable(dest_dir):
    """Download VB-Cable zip to dest_dir. Returns path to zip or None."""
    zip_path = os.path.join(dest_dir, "VBCABLE.zip")
    try:
        print("[Driver] Downloading VB-Cable...")
        urllib.request.urlretrieve(VB_URL, zip_path)
        return zip_path
    except Exception as e:
        print(f"[Driver] Download failed: {e}")
        return None


def extract_and_install(zip_path):
    """Extract and launch installer (needs admin)."""
    extract_dir = os.path.join(os.path.dirname(zip_path), "VBCABLE")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)

    # Find the 64-bit installer
    exe = None
    for f in os.listdir(extract_dir):
        if "setup" in f.lower() and "x64" in f.lower() and f.endswith(".exe"):
            exe = os.path.join(extract_dir, f)
            break
    if not exe:
        for f in os.listdir(extract_dir):
            if "setup" in f.lower() and f.endswith(".exe"):
                exe = os.path.join(extract_dir, f)
                break
    if exe:
        print(f"[Driver] Launching installer: {exe}")
        subprocess.Popen(["cmd", "/c", "start", "", exe], shell=True)
        return True
    return False


def rename_to_sonixx():
    """Rename VB-Cable Output capture device to 'Sonixx' in registry."""
    try:
        base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture"
        prop_name = "{a45c254e-df1c-4efd-8020-67d146a850e0},2"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_READ)
        for i in range(1000):
            try:
                guid = winreg.EnumKey(key, i)
                props_path = f"{base}\\{guid}\\Properties"
                pk = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, props_path, 0, winreg.KEY_READ)
                try:
                    val, vtype = winreg.QueryValueEx(pk, prop_name)
                    val_str = str(val).lower()
                    
                    # Check if already named Sonixx
                    if val == SONIXX:
                        winreg.CloseKey(pk)
                        winreg.CloseKey(key)
                        return True, f"Already renamed to {SONIXX}."

                    # Identify the device if it contains 'cable' or the old name 'felixx'
                    if "cable" in val_str or "felixx" in val_str:
                        winreg.CloseKey(pk)
                        pk = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, props_path, 0,
                                            winreg.KEY_SET_VALUE | winreg.KEY_READ)
                        winreg.SetValueEx(pk, prop_name, 0, vtype, SONIXX)
                        winreg.CloseKey(pk)
                        winreg.CloseKey(key)
                        return True, f"Renamed to {SONIXX}! Restart audio apps to see the change."
                except FileNotFoundError:
                    pass
                winreg.CloseKey(pk)
            except OSError:
                break
        winreg.CloseKey(key)
        return False, "CABLE device not found in registry"
    except PermissionError:
        return False, "Run as Administrator to rename"
    except Exception as e:
        return False, str(e)
