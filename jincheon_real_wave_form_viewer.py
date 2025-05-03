#!/usr/bin/env python
"""
Real‑time waveform plotter — dynamic image resize, debounced redraw & non‑blocking GUI.

Changes since previous revision
-------------------------------
1. **Dynamic resizing**: the displayed plot now scales automatically when the
   user resizes the main Tk window.  A `<Configure>` binding triggers
   `resize_and_show()`, which re‑renders the current PIL image to fit the new
   window dimensions while maintaining the aspect ratio.
2. **Globals added**: `current_img_pil`, `current_img_tk`, and `_resize_job`
   manage image state and debounce resize events.
3. All other fixes (debounce for watchdog, `after()` timer, Agg backend) are
   retained.
"""

import os
import sys
import time
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Matplotlib headless backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# Tk GUI
import tkinter as tk
from PIL import Image, ImageTk

################################################################################
# 1. TXT loader
################################################################################

def load_txt_file(txt_path: str):
    data = []
    if not os.path.exists(txt_path):
        print(f"[Warning] Could not find file: {txt_path}")
        return data
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(float(line))
                except ValueError:
                    pass
    print(f"{txt_path} LOADED. Len : {len(data)}")
    return data

################################################################################
# 2. Output image name
################################################################################

def get_img_name(dir_path: str):
    return dir_path

################################################################################
# 3. Plot helper
################################################################################

def plot_and_save_offset_merged(data_dict, output_path, title, is_sc=False):
    scale_map = {
        "VGE":  (10.0, "V"),
        "VCE":  (200.0, "V"),
        "ICE":  (200.0, "A"),
        "VCE2": (200.0, "V"),
    }
    if is_sc:
        scale_map.pop("VCE2", None)

    if "H_ICE" in data_dict and "L_ICE" in data_dict:
        all_ice = (data_dict.get("H_ICE") or []) + (data_dict.get("L_ICE") or [])
        if all_ice and max(all_ice) > 2000.0:
            scale_map["ICE"] = (500.0, "A")

    groupings = [
        (["H_VGE", "L_VGE"], "VGE"),
        (["H_VCE", "L_VCE"], "VCE"),
        (["H_ICE", "L_ICE"], "ICE"),
        (["H_VCE2", "L_VCE2"], "VCE2"),
    ]
    if is_sc:
        groupings.pop()
    groupings.reverse()

    plt.figure(figsize=(16, 8))

    max_len = max((len(arr) - 1) for arr in data_dict.values() if arr) if data_dict else 0
    offset_step = 8.0
    y_lim_top = 0.0
    labelled = set()

    for g_i, (keys, g_type) in enumerate(groupings):
        group_offset = g_i * offset_step
        sf, unit = scale_map.get(g_type, (1.0, "?"))
        scale_factor = 1.0 / sf
        unit_per_div = f"{sf} {unit}"

        for k in keys:
            if k not in data_dict:
                continue
            raw = data_dict[k][1:][:max_len]
            shifted = [(v * scale_factor) + group_offset for v in raw]
            x = [i / 1000.0 for i in range(len(shifted))]
            color = "red" if k.startswith("H_") else "blue"
            short = k[2:]
            label = f"{short} (1 div = {unit_per_div})" if short not in labelled else None
            plt.plot(x, shifted, color=color, linewidth=1.0, label=label)
            if shifted and short not in labelled:
                plt.text(x[0], shifted[0], f"{short}   ", ha="right", va="center", fontsize=9)
                labelled.add(short)
            if shifted:
                y_lim_top = max(y_lim_top, max(shifted))

    plt.ylim(-2, y_lim_top + 1)
    plt.yticks(np.arange(-2, y_lim_top + 2, 1))
    plt.tick_params(axis="y", labelleft=False)

    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(5.0))
    ax.xaxis.set_minor_locator(MultipleLocator(1.0))
    ax.xaxis.set_major_formatter(lambda v, p: f"{int(v)} us")
    ax.grid(True, which="major", linestyle="--", linewidth=0.5)
    ax.grid(True, which="minor", linestyle="--", linewidth=0.3)

    plt.legend(loc="lower right", fontsize=9, handlelength=0, handletextpad=0)
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Saved Plot : {output_path}")

################################################################################
# 4. Directory processing (debounced)
################################################################################

_last_call = {}

def process_directory(dir_path: str, debounce_ms: int = 300):
    now = time.time()
    if now - _last_call.get(dir_path, 0) < debounce_ms / 1000:
        return
    _last_call[dir_path] = now

    print(f"[Process] Directory: {dir_path}")
    keys = [
        "H_VGE", "H_VCE", "H_ICE", "H_VCE2",
        "L_VGE", "L_VCE", "L_ICE", "L_VCE2",
    ]
    data_dict = {}
    for item in os.listdir(dir_path):
        if item.endswith(".txt"):
            for pk in keys:
                if pk in item:
                    data_dict[pk] = load_txt_file(os.path.join(dir_path, item))
                    break

    output_img = get_img_name(dir_path) + ".jpg"
    plot_and_save_offset_merged(data_dict, output_img, title=os.path.basename(output_img), is_sc="_SC" in dir_path)
    if os.path.exists(output_img):
        add_image_to_gallery(output_img)

################################################################################
# 5. Watchdog handler
################################################################################

class TxtFileModifiedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".txt"):
            time.sleep(0.1)
            process_directory(os.path.dirname(event.src_path))

################################################################################
# 6. GUI helpers (dynamic resize)
################################################################################

root = None
image_label = None
current_img_pil = None  # original PIL image
current_img_tk = None   # current Tk image
_resize_job = None      # debounce id


def resize_and_show():
    global current_img_tk
    if current_img_pil is None:
        return
    w, h = root.winfo_width(), root.winfo_height()
    if w < 10 or h < 10:
        return
    img = current_img_pil.copy()
    img.thumbnail((w, h), Image.LANCZOS)
    current_img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=current_img_tk)
    image_label.image = current_img_tk  # keep reference


def on_configure(event):
    global _resize_job
    if _resize_job is not None:
        root.after_cancel(_resize_job)
    _resize_job = root.after(100, resize_and_show)


def setup_gui():
    global root, image_label
    root = tk.Tk()
    root.title("Single Window Image Viewer")
    root.geometry("1000x800")
    image_label = tk.Label(root)
    image_label.pack(expand=True, fill="both")
    root.bind("<Configure>", on_configure)
    return root


def add_image_to_gallery(img_path: str):
    global current_img_pil
    if not os.path.exists(img_path):
        return
    current_img_pil = Image.open(img_path)
    resize_and_show()
    # hold for 3.5 s without blocking
    if hasattr(image_label, "_timer_id"):
        root.after_cancel(image_label._timer_id)
    image_label._timer_id = root.after(3500, lambda: None)

################################################################################
# 7. main
################################################################################

def main():
    watch_paths = [
        r"C:\jincheon\!AC_SC_Waves_01",
        r"C:\jincheon\!AC_SC_Waves_02",
        r"C:\jincheon\!AC_SC_Waves_03",
        r"C:\jincheon\!AC_SW_IGBT_Waves_01",
        r"C:\jincheon\!AC_SW_IGBT_Waves_02",
        r"C:\jincheon\!AC_SW_IGBT_Waves_03",
        r"C:\jincheon\!AC_SW_IGBT_Waves_04",
        r"C:\jincheon\!AC_SW_IGBT_Waves_05",
        r"C:\jincheon\!AC_SW_IGBT_Waves_06",
    ]

    root_window = setup_gui()
    observer = Observer()
    handler = TxtFileModifiedHandler()
    for p in watch_paths:
        observer.schedule(handler, p, recursive=True)
        print(f"[INFO] Monitoring: {p}")
    observer.start()

    try:
        root_window.mainloop()
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
