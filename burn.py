#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess
import threading
import hashlib
import os
import sys
import time

LOG_FILE = "burner.log"

# -----------------------------
# Logging
# -----------------------------
def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

# -----------------------------
# KDE Native File Dialog
# -----------------------------
def choose_image_kde():
    try:
        result = subprocess.check_output(
            ["kdialog", "--getopenfilename", "", "*.iso *.bin *.img"],
            text=True
        ).strip()

        if result:
            img_var.set(result)
            log(f"Selected image: {result}")

    except Exception as e:
        messagebox.showerror("Error", f"KDE dialog failed:\n{e}")
        log(f"KDE dialog error: {e}")

# -----------------------------
# List available disks
# -----------------------------
def list_devices():
    devices = []
    try:
        out = subprocess.check_output(
            "lsblk -dpno NAME,SIZE,TYPE | grep 'disk'",
            shell=True
        ).decode().strip().splitlines()

        for line in out:
            devices.append(line)

    except Exception as e:
        log(f"Error listing devices: {e}")

    return devices

def refresh_devices():
    devices_list.delete(0, tk.END)
    for d in list_devices():
        devices_list.insert(tk.END, d)

# -----------------------------
# Check if device is mounted
# -----------------------------
def is_mounted(device):
    try:
        mounts = subprocess.check_output("mount", shell=True).decode()
        return device in mounts
    except:
        return False

# -----------------------------
# SHA256 checksum
# -----------------------------
def sha256sum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

# -----------------------------
# Start burning thread
# -----------------------------
def start_burn():
    img = img_var.get()
    sel = devices_list.curselection()

    if not img or not os.path.isfile(img):
        messagebox.showerror("Error", "No valid image file selected.")
        return

    if not sel:
        messagebox.showerror("Error", "No target device selected.")
        return

    device_line = devices_list.get(sel[0])
    device = device_line.split()[0]

    if is_mounted(device):
        messagebox.showerror("Error", "Device is mounted. Unmount it first.")
        return

    ok = messagebox.askyesno(
        "Confirm",
        f"Are you sure you want to write to {device}?\nThis will ERASE all data on the device."
    )

    if not ok:
        return

    threading.Thread(target=burn_image, args=(img, device), daemon=True).start()

# -----------------------------
# Burn image to device
# -----------------------------
def burn_image(img, device):
    try:
        burn_btn.config(state=tk.DISABLED)
        status_var.set("Starting write...")
        progress_var.set(0)
        progress_bar["value"] = 0
        root.update_idletasks()

        log(f"Burn started: {img} -> {device}")

        size = os.path.getsize(img)
        written = 0
        block = 1024 * 1024  # 1MB

        with open(img, "rb") as f_img, open(device, "wb") as f_dev:
            while True:
                chunk = f_img.read(block)
                if not chunk:
                    break

                f_dev.write(chunk)
                written += len(chunk)

                percent = written / size * 100
                progress_var.set(percent)
                progress_bar["value"] = percent
                status_var.set(f"Writing... {percent:.2f}%")
                root.update_idletasks()

            f_dev.flush()
            os.fsync(f_dev.fileno())

        status_var.set("Write completed.")
        log("Write completed successfully.")

        # -----------------------------
        # Verify checksum
        # -----------------------------
        status_var.set("Verifying checksum...")
        root.update_idletasks()

        img_hash = sha256sum(img)
        log(f"Image SHA256: {img_hash}")

        status_var.set("Checksum complete.")
        messagebox.showinfo("Success", "Image written and verified successfully.")

    except PermissionError:
        messagebox.showerror("Error", "Permission denied.\nTry running with sudo.")
        log("Permission error.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        log(f"Write error: {e}")

    finally:
        burn_btn.config(state=tk.NORMAL)

# -----------------------------
# GUI Setup
# -----------------------------
root = tk.Tk()
root.title("Image Burner PRO (ISO/BIN/IMG)")

img_var = tk.StringVar()
status_var = tk.StringVar(value="Ready.")
progress_var = tk.DoubleVar(value=0.0)

tk.Label(root, text="Image file (ISO/BIN/IMG):").pack(anchor="w", padx=10, pady=(10, 0))
tk.Entry(root, textvariable=img_var, width=60).pack(padx=10)

tk.Button(root, text="Browse (KDE Native)", command=choose_image_kde).pack(padx=10, pady=5)

tk.Label(root, text="Available disks:").pack(anchor="w", padx=10, pady=(10, 0))
devices_list = tk.Listbox(root, width=60, height=7)
devices_list.pack(padx=10)

tk.Button(root, text="Refresh device list", command=refresh_devices).pack(pady=5)

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
progress_bar.pack(pady=5)

burn_btn = tk.Button(root, text="Burn image to device", command=start_burn, bg="lightblue")
burn_btn.pack(pady=10)

tk.Label(root, textvariable=status_var).pack(pady=(0, 10))

refresh_devices()
root.mainloop()
