import sys
import os
import time
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

###############################
# 1. TXT 파일 로딩 (변경 없음)
###############################
def load_txt_file(txt_path):
    data = []
    if not os.path.exists(txt_path):
        print(f"[Warning] Could not find file: {txt_path}")
        return data
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    value = float(line)
                    data.append(value)
                except ValueError:
                    pass
    print(f'{txt_path} LOADED. Len : {len(data)}')
    return data


###############################
# 2. 출력 이미지 이름 구성 (변경 없음)
###############################
def get_img_name(dir_path: str):
    return dir_path  # 그대로 유지


###############################
# 3. 단일 Plot (변경 없음)
###############################
def plot_and_save_offset_merged(data_dict, output_path, title, is_sc=False):
    scale_map = {
        'VGE':  (10.0, 'V'),
        'VCE':  (200.0, 'V'),
        'ICE':  (200.0, 'A'),
        'VCE2': (200.0, 'V')
    }
    if is_sc == True:
        scale_map.pop('VCE2')
    if 'H_ICE' in data_dict and 'L_ICE' in data_dict:
        all_ice_data = []
        if data_dict['H_ICE']:
            all_ice_data.extend(data_dict['H_ICE'])
        if data_dict['L_ICE']:
            all_ice_data.extend(data_dict['L_ICE'])
        if all_ice_data:
            max_ice_value = max(all_ice_data)
            if max_ice_value > 2000.0:
                scale_map['ICE'] = (500.0, 'A')

    groupings = [
        (["H_VGE",  "L_VGE"],  'VGE'),
        (["H_VCE",  "L_VCE"],  'VCE'),
        (["H_ICE",  "L_ICE"],  'ICE'),
        (["H_VCE2", "L_VCE2"], 'VCE2'),
    ]
    if is_sc == True:
        groupings = [
            (["H_VGE",  "L_VGE"],  'VGE'),
            (["H_VCE",  "L_VCE"],  'VCE'),
            (["H_ICE",  "L_ICE"],  'ICE'),
        ]
    groupings.reverse()

    plt.figure(figsize=(16, 8))

    # 가장 긴 배열 길이
    max_len = 0
    for wave_key in data_dict:
        arr = data_dict[wave_key]
        if arr:
            real_len = len(arr) - 1
            if real_len > max_len:
                max_len = real_len

    offset_step = 8.0
    y_lim_top = 0.0
    already_labeled = set()

    for g_i, (group_keys, group_type) in enumerate(groupings):
        group_offset = g_i * offset_step

        # scale factor
        scale_factor = 1.0
        unit_per_div = '?'
        for key, val in scale_map.items():
            if key in group_type.upper():
                scale_factor = 1.0 / val[0]
                unit_per_div = f"{val[0]} {val[1]}"
                break

        for wave_key in group_keys:
            if wave_key not in data_dict:
                continue

            raw_data = data_dict[wave_key]
            raw_data = raw_data[1:]
            wave_len = len(raw_data)

            if wave_len > max_len:
                partial_data = raw_data[:max_len]
                wave_len = max_len
            else:
                partial_data = raw_data

            scaled_data = [val * scale_factor for val in partial_data]
            offset_data = [val + group_offset for val in scaled_data]

            x_vals = [i / 1000.0 for i in range(wave_len)]
            color = 'red' if wave_key.startswith('H_') else 'blue'

            short_label = wave_key[2:]
            if short_label not in already_labeled:
                legend_str = f"{short_label} (1 div = {unit_per_div})"
            else:
                legend_str = None

            plt.plot(x_vals, offset_data, color=color, linewidth=1.0, label=legend_str)

            if wave_len > 0 and short_label not in already_labeled:
                plt.text(
                    x_vals[0],
                    offset_data[0],
                    short_label + '   ',
                    va='center',
                    ha='right',
                    fontsize=9,
                    color='k'
                )
                already_labeled.add(short_label)

            local_data_max = max(offset_data) if offset_data else 0
            if local_data_max > y_lim_top:
                y_lim_top = local_data_max

    plt.ylim(-2, y_lim_top + 1.0)
    y_ticks = np.arange(-2, y_lim_top + 2.0, 1.0)
    plt.yticks(y_ticks)
    plt.tick_params(axis='y', labelleft=False)

    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(5.0))
    ax.xaxis.set_minor_locator(MultipleLocator(1.0))
    ax.xaxis.set_major_formatter(lambda val, pos: f"{int(val)} us")

    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)
    ax.grid(True, which='minor', axis='both', linestyle='--', linewidth=0.3)

    plt.legend(loc='lower right', fontsize=9, handlelength=0, handletextpad=0)
    plt.savefig(output_path)
    plt.close()
    print(f"[INFO] Saved Plot : {output_path}")


###############################
# 4. 디렉토리 처리 (변경 없음)
###############################
last_dir = ''
def process_directory(dir_path):
    global last_dir
    if dir_path == last_dir:
        return
    else:
        last_dir = dir_path

    print(f"[Process] Directory: {dir_path}")

    possible_keys = ["H_VGE","H_VCE","H_ICE","H_VCE2","L_VGE","L_VCE","L_ICE","L_VCE2"]
    possible_keys.reverse()
    data_dict = {}

    sub_items = os.listdir(dir_path)
    for item in sub_items:
        if item.endswith('.txt'):
            for pk in possible_keys:
                if pk in item:
                    full_path = os.path.join(dir_path, item)
                    data_dict[pk] = load_txt_file(full_path)
                    break

    is_sc = ('_SC' in dir_path)
    output_img_path = get_img_name(dir_path) + '.jpg'
    title_str = os.path.basename(output_img_path)

    plot_and_save_offset_merged(data_dict, output_img_path, title=title_str, is_sc=is_sc)

    # GUI에 이미지 표시
    if os.path.exists(output_img_path):
        add_image_to_gallery(output_img_path)


###############################
# 5. Watchdog Handler (변경 없음)
###############################
class TxtFileModifiedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            time.sleep(0.2)
            dir_of_file = os.path.dirname(event.src_path)
            process_directory(dir_of_file)


###############################
# === [여기부터 GUI 수정] ===
###############################

# 기존: 2×2 ScrolledImageViewer 제거
# 새로: 하나의 윈도우+Label에 3.5초간 이미지를 표시

root = None
image_label = None

def setup_gui():
    """
    하나의 메인 윈도우와 Label만 생성.
    """
    global root, image_label

    root = tk.Tk()
    root.title("Single Window Image Viewer")
    # 창 크기 설정 (필요 시 조절)
    root.geometry("1000x800")

    # Label 하나만 메인 윈도우에 배치
    image_label = tk.Label(root)
    image_label.pack(expand=True, fill="both")

    return root

def add_image_to_gallery(img_path):
    """
    새로 생성된 .jpg 파일이 들어오면
    메인 윈도우에 이미지를 표시한 후 3.5초간 유지.
    """
    global image_label, root

    if not os.path.exists(img_path):
        return

    # PIL 이미지를 Label에 표시
    pil_img = Image.open(img_path)
    tk_img = ImageTk.PhotoImage(pil_img)
    image_label.config(image=tk_img)
    image_label.image = tk_img

    # 즉시 화면 갱신
    root.update()

    # 3.5초간 대기
    time.sleep(3.5)


###############################
# 8. main (필수 로직 그대로)
###############################
def main():
    watch_pathes = [
    r"C:\!AC_SC_Waves_01",
    r"C:\!AC_SC_Waves_02",
    r"C:\!AC_SC_Waves_03",
    r"C:\!AC_SW_IGBT_Waves_01",    #RBSOA DP IGBT1,2 
    r"C:\!AC_SW_IGBT_Waves_02",    #RBSOA MP SICFET3,4 
    r"C:\!AC_SW_IGBT_Waves_03",    #RBSOA MP SICFET6 
    r"C:\!AC_SW_IGBT_Waves_04",    #DPT IGBT1,2 
    r"C:\!AC_SW_IGBT_Waves_05",    #DPT SICFET3,4 
    r"C:\!AC_SW_IGBT_Waves_06"     #DPT SICFET6
    ]

    root_window = setup_gui()

    event_handler = TxtFileModifiedHandler()
    observer = Observer()

    for path in watch_pathes:
        observer.schedule(event_handler, path, recursive=True)
        print(f"[INFO] Monitoring for .txt file modifications in: {path}")

    observer.start()

    try:
        root_window.mainloop()
    except KeyboardInterrupt:
        print("[INFO] Stopping...")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
