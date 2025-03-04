import sys
import os
import time
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------
# 1) Min-Max 스케일링 함수 (사용 안 함) - 필요시 참조
# --------------------------------------------------------------------------
def preprocessing(data):
    """
    (기존) 0~1 범위로 Min-Max 스케일링
    """
    if not data:
        return []
    d_min = min(data)
    d_max = max(data)
    if d_max == d_min:
        print('[X] Error : Wrong DATA Max and Min val is same')
        return [0 for _ in data]
    return [(x - d_min) / (d_max - d_min) for x in data]

# --------------------------------------------------------------------------
# 2) TXT 파일 로드 함수
# --------------------------------------------------------------------------
def load_txt_file(txt_path):
    data = []
    if not os.path.exists(txt_path):
        print('no txt file in load_txt_file func')
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
    return data

# --------------------------------------------------------------------------
# 3) (수정본) Plot 함수: "파일 이름에 따라" 서로 다른 실제 단위/그리드로 스케일링
#    + 범례(legend) 표시
# --------------------------------------------------------------------------
def plot_and_save_offset(data_dict, output_path, title, line_color='red'):
    """
    data_dict: { "IGBT1_HS_VGE": [...], "IGBT1_HS_VCE": [...], ... }
    output_path: 저장할 jpg 파일 경로
    title: 그래프 제목
    line_color: 라인 색상
    """

    # (1) 파일타입별 스케일링 규칙 정의
    #     - 1 grid 당 몇 단위를 의미하는지.
    #     - 예: VGE -> 10 V, VCE -> 200 V, ICE -> 200 A, POW1 -> 100 kW
    scale_map = {
        'VGE': (10.0, 'V'),    # 10 V / div
        'VCE': (200.0, 'V'),   # 200 V / div
        'ICE': (200.0, 'A'),   # 200 A / div
        'POW1': (100000.0 ,'kW') #(100.0, 'kW'), # 100 kW / div
    }

    plt.figure(figsize=(16, 8))
    plt.title(title)

    labels = list(data_dict.keys())

    # Offset 간격(크게 잡아서 파형 겹침 방지)
    offset_distance = 8.0  
    offsets = [i * offset_distance for i in range(len(labels))]

    # y축 최댓값 추적 (동적으로 결정)
    y_lim_top = 0.0

    # 범례 출력을 위해 라인 객체를 모아둘 리스트
    line_objs = []

    for idx, label in enumerate(labels):
        raw_data = data_dict[label][1:]  # 앞부분 1개 샘플 버리기 (기존 로직)
        if not raw_data:
            print(f"[Warning] '{label}' has no data.")
            continue

        # (2) 스케일 선택: label 내에 VGE, VCE, ICE, POW1 등을 탐색
        #     - 못 찾으면(기본값) 1:1로 둠
        scale_factor = 1.0
        unit_per_div = '?'
        for key in scale_map:
            if key in label.upper():
                scale_factor = 1.0 / scale_map[key][0]  # 예: 1/10.0
                unit_per_div = f"{scale_map[key][0]} {scale_map[key][1]}"
                break

        # (3) 실제 스케일링 수행 => '1 div' 기준으로 몇 배인지
        scaled_data = [val * scale_factor for val in raw_data]

        # (4) Offset 적용 => 서로 다른 파형이 겹치지 않도록
        offset_val = offsets[idx]
        offset_data = [val + offset_val for val in scaled_data]

        # x 인덱스 -> 0~40,000 => 0~40.0 us
        x_vals = [i / 1000.0 for i in range(len(offset_data))]

        # (5) 플롯 (범례 표시를 위해 label 지정)
        #     - 범례: 예) "VGE (1 div = 10 V)"
        #     - label[-4:].removeprefix('_') => VGE, VCE 등
        short_name = label[-4:].removeprefix('_').upper()  # "VGE", "VCE" ...
        legend_str = f"{short_name} (1 div = {unit_per_div})"
        if short_name == 'POW1': legend_str = f"{short_name} (1 div = {scale_map[short_name][0]/1000.0} {scale_map[short_name][1]})"

        line_obj, = plt.plot(x_vals, offset_data, color=line_color, linewidth=1.0,
                             label=legend_str)
        line_objs.append(line_obj)

        # (6) 왼쪽에 작은 텍스트 표시 (기존 로직 유지)
        plt.text(
            0, offset_val,  # offset(스케일 0 위치)에 텍스트 표시
            short_name + '   ',
            va='center',
            ha='right',
            fontsize=9,
            color='k'
        )

        # y축 최대값 갱신
        local_max = max(offset_data) if offset_data else 0
        if local_max > y_lim_top:
            y_lim_top = local_max

    # ---------------------------
    # X축 범위
    # ---------------------------
    # 위에서 x_vals를 만든 최대 길이 기반으로 결정
    max_len = max((len(data_dict[lbl]) for lbl in labels), default=1)
    x_max_us = (max_len - 1) / 1000.0 if max_len > 1 else 1.0
    plt.xlim(0, x_max_us)

    # ---------------------------
    # Y축 범위 및 Tick
    #  -> 1.0 간격씩 grid가 보이도록 설정(1칸 = 1 div)
    # ---------------------------
    plt.ylim(-2, y_lim_top + 1.0)
    y_ticks = np.arange(-2, y_lim_top + 2.0, 1.0)  # 1 단위씩
    plt.yticks(y_ticks)
    plt.tick_params(axis='y', labelleft=False)  # y축 레이블 숨기기

    # ---------------------------
    # Grid, Ticks 설정
    #  (x축은 기존과 동일, major=5us, minor=1us)
    # ---------------------------
    ax = plt.gca()
    major_step = 5.0
    minor_step = 1.0
    ax.xaxis.set_major_locator(MultipleLocator(major_step))
    ax.xaxis.set_minor_locator(MultipleLocator(minor_step))

    # 라벨 포맷: "0 us", "5 us", ...
    ax.xaxis.set_major_formatter(lambda val, pos: f"{int(val)} us")

    # Grid: major/minor 둘 다
    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)
    ax.grid(True, which='minor', axis='both', linestyle='--', linewidth=0.3)

    # ---------------------------
    # (새로 추가) 범례 표시
    # ---------------------------
    if line_objs:
        plt.legend(handles=line_objs, loc='lower right', fontsize=9,handlelength=0, handletextpad=0,) #bbox_to_anchor=(1.1, 1.05)

    # ---------------------------
    # 그래프 저장
    # ---------------------------
    plt.savefig(output_path)
    plt.close()
    print(f"[INFO] Saved Plot : {output_path}")

# --------------------------------------------------------------------------
# 4) 디렉토리 처리 함수
# --------------------------------------------------------------------------
def process_directory(dir_path):
    print(f"[*] process_directory: {dir_path}")
    sub_items = os.listdir(dir_path)
    txt_files = [f for f in sub_items if f.endswith('.txt')]
    if not txt_files:
        # 재귀적으로 하위 폴더 탐색
        for item in sub_items:
            sub_path = os.path.join(dir_path, item)
            if os.path.isdir(sub_path):
                process_directory(sub_path)
        return

    dir_name = os.path.basename(dir_path)

    # 예시: AC_L7_600V_400A 라면, 4개 파일(HS_VGE, HS_VCE, HS_ICE, HS_POW1) / (LS_VGE, LS_VCE, LS_ICE, LS_POW1) 처리
    # 아니면, 3개 파일(HS_VGE, HS_VCE, HS_ICE) / (LS_VGE, LS_VCE, LS_ICE) 처리 (기존 로직)

    if "AC_L7_600V_40" in dir_name: # 원래는 400A 였으나 408A 도 있어서 이렇게 수정. 
        plt_name = dir_name[:dir_name.find("A_")+1] if "A_" in dir_name else dir_name

        # High Side
        h_files = ["IGBT1_HS_VGE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_ICE.txt", "IGBT1_HS_POW1.txt"]
        h_files.reverse()
        data_dict_h = {}
        for hf in h_files:
            full_path = os.path.join(dir_path, hf)
            label = hf.replace(".txt", "")
            data_dict_h[label] = load_txt_file(full_path)
        output_h = os.path.join(dir_path, f"{plt_name}_High_Side.jpg")
        plot_and_save_offset(data_dict_h, output_h, title=f"{plt_name}_High_Side", line_color='red')

        # Low Side
        l_files = ["IGBT2_LS_VGE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_ICE.txt", "IGBT2_LS_POW1.txt"]
        l_files.reverse()
        data_dict_l = {}
        for lf in l_files:
            full_path = os.path.join(dir_path, lf)
            label = lf.replace(".txt", "")
            data_dict_l[label] = load_txt_file(full_path)
        output_l = os.path.join(dir_path, f"{plt_name}_Low_Side.jpg")
        plot_and_save_offset(data_dict_l, output_l, title=f"{plt_name}_Low_Side", line_color='blue')

    else:
        plt_name = dir_name[:dir_name.find("A_")+1] if "A_" in dir_name else dir_name
        
        # High Side
        h_files = ["IGBT1_HS_VGE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_ICE.txt"]
        h_files.reverse()
        data_dict_h = {}
        for hf in h_files:
            full_path = os.path.join(dir_path, hf)
            label = hf.replace(".txt", "")
            data_dict_h[label] = load_txt_file(full_path)
        output_h = os.path.join(dir_path, f"{plt_name}_High_Side.jpg")
        plot_and_save_offset(data_dict_h, output_h, title=f"{plt_name}_High_Side", line_color='red')

        # Low Side
        l_files = ["IGBT2_LS_VGE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_ICE.txt"]
        l_files.reverse()
        data_dict_l = {}
        for lf in l_files:
            full_path = os.path.join(dir_path, lf)
            label = lf.replace(".txt", "")
            data_dict_l[label] = load_txt_file(full_path)
        output_l = os.path.join(dir_path, f"{plt_name}_Low_Side.jpg")
        plot_and_save_offset(data_dict_l, output_l, title=f"{plt_name}_Low_Side", line_color='blue')

# --------------------------------------------------------------------------
# 5) Watchdog 핸들러
# --------------------------------------------------------------------------
class NewDirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            new_dir_path = event.src_path
            print(f"[INFO] New Folder Detected : {new_dir_path} .")
            time.sleep(5)
            process_directory(new_dir_path)

# --------------------------------------------------------------------------
# 6) 메인 함수
# --------------------------------------------------------------------------
def main():
    watch_path = r"C:\!FAIL_WFM"

    event_handler = NewDirectoryHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)

    observer.start()
    print(f"[INFO] Observing Folder : {watch_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

class StreamToLogger(object):
    def __init__(self, file_path):
        self.log_file = open(file_path, 'a', encoding='utf-8')
    
    def write(self, message):
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        pass

# 로그 리다이렉트 예시(필요 시 사용)
# sys.stderr = StreamToLogger("wave_img_maker_stderr.log")

if __name__ == "__main__":
    main()
