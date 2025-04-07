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
# 1. TXT 파일 로딩
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
# 2. 출력 이미지 이름 구성
###############################
def get_img_name(dir_path: str):
    # d = {
    #         '!AC_SW_IGBT_Waves_01' : 'IGBT12_RBSOA',
    #         '!AC_SW_IGBT_Waves_02' : 'SICFET34_RBSOA',
    #         '!AC_SC_Waves_01' : 'IGBT12_SC',
    #         '!AC_SC_Waves_02' : 'SICFET34_SC',
    #     }
    # dirs = dir_path.split('\\')

    return dir_path#os.path.join(dir_path,str(d[dirs[1]]))


###############################
# 3. 단일 Plot (H_* vs L_*)
###############################
def plot_and_save_offset_merged(data_dict, output_path, title, is_sc=False):
    """
    파일명에 'H_VGE', 'L_VGE' 등으로 구분된 데이터를 하나의 Plot에 그리되,
    H/L 구분은 색상으로만 하고, legend에는 측정항목(VCE, VGE, ICE, VCE2)만 표시.
    """

    scale_map = {
        'VGE':  (10.0, 'V'),
        'VCE':  (200.0, 'V'),
        'ICE':  (200.0, 'A'),
        'VCE2': (200.0, 'V')
    }
    if is_sc==True:
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
    groupings.reverse()

    plt.figure(figsize=(16, 8))
    #plt.title(title)



    # 여러 데이터 중 "가장 긴" 배열 길이를 찾는다
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
            if wave_key not in data_dict :
                print(wave_key)
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
# 4. 디렉토리 처리 (중복 처리 방지)
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
                    #print(f"[DEBUG] Matched {item} -> key={pk}")
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
# 5. Watchdog Handler
###############################
class TxtFileModifiedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            time.sleep(1)
            dir_of_file = os.path.dirname(event.src_path)
            process_directory(dir_of_file)


###############################
# 6. 이미지 뷰어 클래스
###############################
class ScrolledImageViewer(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # 스크롤바 + 캔버스 구성
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.hbar = tk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.vbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")

        # 행/열 확대 되도록 설정
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.bind_events()

        self.image_id = None
        self.original_image = None  # 원본 PIL 이미지
        self.zoom_level = 1.0

    def bind_events(self):
        # 마우스 휠 Zoom
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)   # Linux
        self.canvas.bind("<Button-5>", self.on_mousewheel)   # Linux

        # 키보드 화살표 Pan
        self.canvas.bind_all("<Up>", self.on_arrow_key)
        self.canvas.bind_all("<Down>", self.on_arrow_key)
        self.canvas.bind_all("<Left>", self.on_arrow_key)
        self.canvas.bind_all("<Right>", self.on_arrow_key)

    def set_image(self, pil_image):
        """
        이미지를 현재 뷰어에 표시.
        """
        self.original_image = pil_image
        self.zoom_level = 1.0
        self.show_image()

    def show_image(self):
        """
        현재 zoom_level에 맞춰 이미지를 표시.
        """
        if not self.original_image:
            return

        # 현재 Frame 크기에 맞춰 일단 기본적으로 resize 후, zoom_level을 곱해줌
        frame_width = max(self.winfo_width(), 1)
        frame_height = max(self.winfo_height(), 1)

        # 원본 이미지 크기
        orig_w, orig_h = self.original_image.size

        # 기본적으로 Frame에 '맞춰서' 먼저 스케일 결정
        ratio_w = frame_width / orig_w
        ratio_h = frame_height / orig_h
        base_scale = min(ratio_w, ratio_h)

        new_width = int(orig_w * base_scale * self.zoom_level)
        new_height = int(orig_h * base_scale * self.zoom_level)

        resized_img = self.original_image.resize((new_width, new_height), Image.ANTIALIAS)
        self.tk_image = ImageTk.PhotoImage(resized_img)

        # Canvas 이미지를 갱신
        if self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor='nw')
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)

        # Scroll region 재조정
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))

    def on_mousewheel(self, event):
        """
        마우스 휠로 zoom_level 변경
        """
        # Windows 기준: event.delta > 0 이면 위로 스크롤(확대), <0 이면 아래로 스크롤(축소)
        # Linux 기준: Button-4는 확대, Button-5는 축소
        if event.num == 4 or event.delta > 0:
            self.zoom_level *= 1.1
        elif event.num == 5 or event.delta < 0:
            self.zoom_level *= 0.9

        # 너무 작은 값으로 가지 않도록 제한
        if self.zoom_level < 0.1:
            self.zoom_level = 0.1
        if self.zoom_level > 10.0:
            self.zoom_level = 10.0

        self.show_image()

    def on_arrow_key(self, event):
        """
        화살표 키로 이미지 화면 이동
        """
        move_px = 50  # 이동량
        if event.keysym == 'Up':
            self.canvas.yview_scroll(-move_px, "units")
        elif event.keysym == 'Down':
            self.canvas.yview_scroll(move_px, "units")
        elif event.keysym == 'Left':
            self.canvas.xview_scroll(-move_px, "units")
        elif event.keysym == 'Right':
            self.canvas.xview_scroll(move_px, "units")


###############################
# 7. 전체 화면 GUI 초기화
###############################
MAX_IMAGES = 4
displayed_viewers = []  # ScrolledImageViewer의 리스트
current_index = 0        # 어느 뷰어에 이미지를 넣을지

def setup_gui():
    global root
    root = tk.Tk()
    root.title("Waveform Image Viewer (4-slot)")

    # 일반적인 윈도우 창 크기 설정 (예: 1200x800)
    root.geometry("1000x800")  # 너비x높이, 필요에 따라 조절 가능

    # 창 크기 조절 가능하게 (기본값이 True지만 명시적으로 설정해도 좋음)
    root.resizable(True, True)

    # 2×2 Grid Layout
    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    # 4개의 이미지 뷰어 생성
    for r in range(2):
        for c in range(2):
            viewer = ScrolledImageViewer(root)
            viewer.grid(row=r, column=c, sticky="nsew")
            displayed_viewers.append(viewer)

    return root

def add_image_to_gallery(img_path):
    """
    새 이미지가 들어오면 가장 먼저 들어왔던 이미지를 표시 중인 View를 덮어쓰는(Queue처럼) 방식
    """
    global current_index
    global displayed_viewers

    pil_img = Image.open(img_path)

    # 현재 index 위치에 이미지 세팅
    displayed_viewers[current_index].set_image(pil_img)

    # 다음 index로 이동
    current_index = (current_index + 1) % MAX_IMAGES


###############################
# 8. main
###############################
def main():
    watch_pathes = [
        r"C:\!AC_SC_Waves_01",
        r"C:\!AC_SC_Waves_02",
        r"C:\!AC_SW_IGBT_Waves_01",
        r"C:\!AC_SW_IGBT_Waves_02"
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
