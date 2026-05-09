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


def _get_bundled_zip():
    """Locate the VB-Cable zip bundled inside the application."""
    # When frozen (PyInstaller), the zip lives in sys._MEIPASS
    # When running from source, it lives in the project root
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(".")
    zip_path = os.path.join(base, "VBCABLE_Driver_Pack45.zip")
    if os.path.exists(zip_path):
        return zip_path
    return None


def silent_install_vbcable():
    """Extract bundled VB-Cable zip and install silently. Returns (success, message)."""
    zip_path = _get_bundled_zip()
    if not zip_path:
        return False, "Bundled driver zip not found."

    extract_dir = os.path.join(tempfile.mkdtemp(), "VBCABLE")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
    except Exception as e:
        return False, f"Failed to extract driver: {e}"

    # Find the 64-bit setup exe (preferred), fallback to 32-bit
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
    if not exe:
        return False, "Setup executable not found in driver pack."

    # Run the installer silently: -i = install, -h = hide (no GUI)
    print(f"[Driver] Silent-installing VB-Cable: {exe}")
    try:
        result = subprocess.run([exe, "-i", "-h"], capture_output=True, timeout=60)
        if result.returncode == 0:
            return True, "VB-Cable installed successfully."
        else:
            return True, "VB-Cable installer finished (may need reboot)."
    except subprocess.TimeoutExpired:
        return False, "Driver install timed out."
    except Exception as e:
        return False, f"Install error: {e}"


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


def set_startup(enabled=True):
    """Enable or disable 'Start with Windows' for Sonixx."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "Sonixx"
    
    try:
        # Get current executable path
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            reg_val = f'"{exe_path}"'
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            reg_val = f'"{python_exe}" "{script_path}"'
            
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, reg_val)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Driver] Startup toggle failed: {e}")
        return False
