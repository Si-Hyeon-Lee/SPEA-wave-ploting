"""
Wave‑plot watcher.
Reads scale factors from `scale_map.json` that sits NEXT TO the EXE (or next to
the .py file during normal interpretation).
"""

import sys, os, json, time, numpy as np
from copy import deepcopy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt

# ────────────────────────────────────────────────────────────────────────────────
# 1.  Where am I running from?
#    • normal run  → directory of this .py file
#    • frozen EXE  → directory of the launched executable
#      (sys.frozen is set by PyInstaller)  :contentReference[oaicite:0]{index=0}
# ────────────────────────────────────────────────────────────────────────────────
def get_base_dir() -> str:
    if getattr(sys, "frozen", False):               # PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
JSON_PATH = os.path.join(BASE_DIR, "scale_map.json")

# ────────────────────────────────────────────────────────────────────────────────
def load_scale_map(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k.upper(): (float(v[0]), str(v[1])) for k, v in raw.items()}

SCALE_MAP = load_scale_map(JSON_PATH)


def load_txt_file(txt_path: str):
    """Read plain‑text numeric vector; ignore non‑numeric lines."""
    data = []
    if not os.path.exists(txt_path):
        print(f"[WARN] {txt_path} not found")
        return data
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(float(line.strip()))
            except ValueError:
                continue
    return data


# ---------- naming helpers ---------------------------------------------------
def get_img_name(dir_path: str, is_high_side: bool):
    """Return descriptive JPEG name for a measurement folder."""
    test_item = {
        ("HK3", "400A", "000.50", "000.50"): "SW",
        ("HK3", "408A", "000.50", "000.50"): "SW",
        ("HK3", "780A", "000.50", "006.00"): "RBSOA1",
        ("HK3", "1000A", "000.50", "006.00"): "RBSOA2",
        ("HK3A", "400A", "000.50", "000.50"): "SW",
        ("HK3A", "408A", "000.50", "000.50"): "SW",
        ("HK3A", "780A", "000.50", "006.00"): "RBSOA1",
        ("HK3A", "1000A", "000.50", "006.00"): "RBSOA2",
        ("HK5", "200A", "000.50", "000.50"): "SW",
        ("HK5", "390A", "000.50", "006.00"): "RBSOA1",
        ("HK5", "500A", "000.50", "006.00"): "RBSOA2",
    }

    parts = dir_path.split("\\")
    bacord = parts[3].split("_")[3]
    tmp = parts[4].split("_")

    device_key = parts[2].split("_")[1] if "AC" in parts[2] else parts[2].split("_")[0]
    current_key = tmp[3]
    r1_key, r2_key = tmp[6].removesuffix("ohm"), tmp[7].removesuffix("ohm")

    test_type = (
        "SC"
        if "_SC" in dir_path
        else test_item.get((device_key, current_key, r1_key, r2_key), "UNKNOWN_TEST")
    )
    prefix = "High" if is_high_side else "Low"
    return f"{bacord}_AC_{test_type}_{prefix}_Side.jpg"


# ---------- plotting ---------------------------------------------------------
def plot_and_save_offset(
    data_dict: dict,
    output_path: str,
    title: str,
    line_color: str,
    is_sc: bool,
    scale_map: dict,
):
    """Plot waveforms using scale_map; add dynamic offset when is_sc."""
    local_scale = deepcopy(scale_map)  # prevent mutation
    if is_sc and "POW1" in local_scale:
        local_scale["POW1"] = (500000.0, "kW")

    plt.figure(figsize=(16, 8))
    plt.title(title)

    labels = list(data_dict.keys())

    # ---- determine time range ----
    sample_lengths = [len(data_dict[lbl]) - 1 for lbl in labels if data_dict[lbl]]
    max_len = max(sample_lengths) if sample_lengths else 0
    start_i, end_i = (int(max_len * 0.40), int(max_len * 0.70)) if is_sc else (0, max_len)

    fixed_offset = 8.0
    current_top = 0.0
    y_lim_top = 0.0
    line_objs = []

    for idx, label in enumerate(labels):
        raw = data_dict[label][1:]  # first element is length header
        if not raw:
            continue
        segment = raw[start_i:end_i]

        # ---- scaling ----
        scale_factor, unit_per_div = 1.0, "?"
        for key, (val_per_div, unit) in local_scale.items():
            if key in label.upper():
                scale_factor = 1.0 / val_per_div
                unit_per_div = f"{val_per_div} {unit}"
                break
        scaled = [v * scale_factor for v in segment]

        # ---- offset (dynamic for SC) ----
        if is_sc:
            offset = current_top - min(scaled) + 1.0
            current_top = offset + max(scaled)
        else:
            offset = idx * fixed_offset
        shifted = [v + offset for v in scaled]

        # ---- plot ----
        x_vals = [i / 1000.0 for i in range(start_i, end_i)]
        short = label[-4:].lstrip("_").upper()
        legend = (
            f"{short} (1 div = {local_scale['POW1'][0]/1000.0} {local_scale['POW1'][1]})"
            if short == "POW1"
            else f"{short} (1 div = {unit_per_div})"
        )

        (line_obj,) = plt.plot(x_vals, shifted, color=line_color, linewidth=1.0, label=legend)
        line_objs.append(line_obj)
        plt.text(x_vals[0], shifted[0], short + "   ", va="center", ha="right", fontsize=9)

        y_lim_top = max(y_lim_top, max(shifted))

    # ---- axes cosmetics ----
    plt.xlim(start_i / 1000.0, end_i / 1000.0)
    plt.ylim(-2, y_lim_top + 1.0)
    plt.yticks(np.arange(-2, y_lim_top + 2.0, 1.0))
    plt.tick_params(axis="y", labelleft=False)

    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(5.0))
    ax.xaxis.set_minor_locator(MultipleLocator(1.0))
    ax.xaxis.set_major_formatter(lambda val, _: f"{int(val)} us")
    ax.grid(True, which="major", linestyle="--", linewidth=0.5)
    ax.grid(True, which="minor", linestyle="--", linewidth=0.3)

    if line_objs:
        plt.legend(handles=line_objs, loc="lower right", fontsize=9, handlelength=0, handletextpad=0)

    plt.savefig(output_path)
    plt.close()
    print(f"[INFO] Saved Plot : {output_path}")


# ---------- directory traversal ---------------------------------------------
def process_directory(dir_path: str):
    """Depth‑first search; when .txt present, generate plots."""
    sub_items = os.listdir(dir_path)
    txt_files = [f for f in sub_items if f.endswith(".txt")]
    if not txt_files:
        for item in sub_items:
            sub_path = os.path.join(dir_path, item)
            if os.path.isdir(sub_path):
                process_directory(sub_path)
        return

    is_sc = "_SC" in dir_path
    # ---- High side ----
    h_files = list(reversed(["IGBT1_HS_VGE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_ICE.txt", "IGBT1_HS_POW1.txt"]))
    data_h = {f[:-4]: load_txt_file(os.path.join(dir_path, f)) for f in h_files}
    out_h = os.path.join(dir_path, get_img_name(dir_path, True))
    plot_and_save_offset(data_h, out_h, os.path.basename(out_h), "red", is_sc, SCALE_MAP)

    # ---- Low side ----
    l_files = list(reversed(["IGBT2_LS_VGE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_ICE.txt", "IGBT2_LS_POW1.txt"]))
    data_l = {f[:-4]: load_txt_file(os.path.join(dir_path, f)) for f in l_files}
    out_l = os.path.join(dir_path, get_img_name(dir_path, False))
    plot_and_save_offset(data_l, out_l, os.path.basename(out_l), "blue", is_sc, SCALE_MAP)


# ---------- watchdog handler -------------------------------------------------
class NewDirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            print(f"[INFO] New Folder Detected : {event.src_path}")
            time.sleep(3)
            process_directory(event.src_path)


# ---------- main -------------------------------------------------------------
def main():
    watch_path = r"C:\!FAIL_WFM"
    observer = Observer()
    observer.schedule(NewDirectoryHandler(), watch_path, recursive=True)
    observer.start()
    print(f"[INFO] Observing Folder : {watch_path}")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
