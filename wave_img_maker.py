import os
import time
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------
# 1) 유틸 함수: Min-Max 스케일링
# --------------------------------------------------------------------------
def preprocessing(data):
    """
    주어진 1차원 데이터 리스트를 0~1 구간으로 Min-Max 스케일링
    """
    if not data:
        return []
    d_min = min(data)
    d_max = max(data)
    if d_max == d_min:
        # 모든 값이 동일하면 0으로 처리(혹은 전부 0.5 처리 등 가능)
        print('[X] Error : Wrong DATA Max and Min val is same')
        return [0 for _ in data]
    return [(x - d_min) / (d_max - d_min) for x in data]

# --------------------------------------------------------------------------
# 2) TXT 파일 로드 함수
# --------------------------------------------------------------------------
def load_txt_file(txt_path):
    """
    txt_path 경로의 텍스트 파일에서 한 줄에 하나씩 숫자를 읽어서
    float 리스트로 반환.
    """
    data = []
    if not os.path.exists(txt_path):
        print('no txt file in load_txt_file func')
        return data  # 파일 없으면 빈 리스트 반환
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # 공백 라인 제거
                try:
                    value = float(line)
                    data.append(value)
                except ValueError:
                    # 숫자로 변환이 안 되면 스킵 (상황에 따라 처리)
                    pass
    return data

# --------------------------------------------------------------------------
# 3) Plot 함수 (Min-Max 스케일링 + 오프셋 + 라벨 표시)
# --------------------------------------------------------------------------
def plot_and_save_offset(data_dict, output_path, title, line_color='red'):
    """
    data_dict: { "h_a": [values...], "h_b": [values...], ... }
    output_path: 저장할 jpg 파일 경로
    title: 그래프 제목
    line_color: 라인 색상 ('red' or 'blue' etc.)

    변경 요약:
    1) x축: (인덱스) 0~40000 => 0~40 (us)로 간주하여 보여주기
    2) x축, y축 모두 일정 간격 Grid
    3) y축 라벨 숨기기(labelleft=False), 대신 각 라인의 offset(=0 스케일 값) 근처에 텍스트 표시
    4) 정사각형 격자를 위해 set_aspect('equal') 적용
    """
    plt.figure(figsize=(16, 8))
    plt.title(title)

    labels = list(data_dict.keys())
    offsets = [i * 1.25 for i in range(len(labels))]
    max_len = 0

    for idx, label in enumerate(labels):
        # 예시: data_dict[label]에서 앞부분 1개 버리는 로직
        raw_data = data_dict[label][1:]
        scaled_data = preprocessing(raw_data)  # 사용자 정의 함수 (0~1 스케일)
        offset_val = offsets[idx]
        offset_data = [val + offset_val for val in scaled_data]

        if len(offset_data) > max_len:
            max_len = len(offset_data)

        if offset_data:
            # x 인덱스 -> 0~40,000 => 0~40.0 us
            x_vals = [i / 1000.0 for i in range(len(offset_data))]

            plt.plot(x_vals, offset_data, color=line_color, linewidth=1.0)
            plot_text = label[-4:].removeprefix('_')+'   ' 
            # offset(스케일 0 위치)에 텍스트 표시
            plt.text(
                0, offset_val,
                plot_text,
                va='center',
                ha='right',
                fontsize=9,
                color='k'
            )
        else:
            print(f"[경고] '{label}' 데이터가 없음.")

    # ---------------------------
    # 1) x축 범위
    # ---------------------------
    x_max_us = (max_len - 1)/1000.0 if max_len > 0 else 1.0
    plt.xlim(0, x_max_us)

    # ---------------------------
    # 2) y축 범위 및 Tick
    # ---------------------------
    if offsets:
        y_lim_top = offsets[-1] + 1.0
    else:
        y_lim_top = 1.0
    plt.ylim(0, y_lim_top)

    y_ticks = np.arange(0, y_lim_top + 0.25, 0.25)
    plt.yticks(y_ticks)
    # y축 레이블 숨기기
    plt.tick_params(axis='y', labelleft=False)

    # ---------------------------
    # 3) Grid, Ticks 설정 (주요 부분)
    # ---------------------------
    ax = plt.gca()

    # (a) Major Ticks (5us 간격) - 라벨 표시용
    major_step = 5.0
    ax.xaxis.set_major_locator(MultipleLocator(major_step))
    # 라벨 포맷: "0 us", "5 us", "10 us" ...
    ax.xaxis.set_major_formatter(lambda val, pos: f"{int(val)} us")

    # (b) Minor Ticks (1us 간격) - Grid 선 촘촘히
    minor_step = 1.0
    ax.xaxis.set_minor_locator(MultipleLocator(minor_step))

    # Grid: major/minor 둘 다
    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)
    ax.grid(True, which='minor', axis='both', linestyle='--', linewidth=0.3)

    # ---------------------------
    # 4) 그래프 저장
    # ---------------------------
    plt.savefig(output_path)
    plt.close()
    print(f"[INFO] 그래프 저장 완료: {output_path}")

# --------------------------------------------------------------------------
# 4) 실제 디렉토리 처리 (DFS)
# --------------------------------------------------------------------------
def process_directory(dir_path):
    # print(f"DFS : {dir_path}")
    # print(r"{}".format(dir_path))
    
    """
    dir_path 하위에 TXT 파일이 있는 '말단 디렉토리'를 찾아서,
    디렉토리명에 따라 plot을 생성한다.
    """
    print(f"[*] process_directory: {dir_path}")  # 디버그
    sub_items = os.listdir(dir_path)
    print(sub_items)
    txt_files = [f for f in sub_items if f.endswith('.txt')]
    print(f"    └─> txt_files: {txt_files}")  # 디버그
    # txt 파일이 없다면, 더 깊이 들어가서 탐색
    if not txt_files:
        for item in sub_items:
            sub_path = os.path.join(dir_path, item)
            if os.path.isdir(sub_path):
                process_directory(sub_path)
        return

    # ---- txt 파일이 있는 디렉토리라면 ----
    dir_name = os.path.basename(dir_path)  # 예: "A", "B", "C", ...

    # case 1) 디렉토리 이름이 "A"인 경우: h_a,b,c,d 와 l_a,b,c,d
    if "AC_L7_600V_400A" in dir_name :
        plt_name = dir_name[:dir_name.find("A_")+1]
        # h 시리즈
        h_files = ["IGBT1_HS_ICE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_VGE.txt","IGBT1_HS_POW1.txt"]
        data_dict_h = {}
        for hf in h_files:
            full_path = os.path.join(dir_path, hf)
            label = hf.replace(".txt", "")  # 예: "h_a"
            data_dict_h[label] = load_txt_file(full_path)
        # 플롯 그리기 (Color=Red)
        output_h = os.path.join(dir_path, f"{plt_name}_High_Side.jpg")
        plot_and_save_offset(data_dict_h, output_h, title=f"{plt_name}_High_Side", line_color='red')

        # l 시리즈
        l_files = ["IGBT2_LS_ICE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_VGE.txt","IGBT2_LS_POW1.txt"]
        data_dict_l = {}
        for lf in l_files:
            full_path = os.path.join(dir_path, lf)
            label = lf.replace(".txt", "")
            data_dict_l[label] = load_txt_file(full_path)
        # 플롯 그리기 (Color=Blue)
        output_l = os.path.join(dir_path, f"{plt_name}_Low_Side.jpg")
        plot_and_save_offset(data_dict_l, output_l, title=f"{plt_name}_Low_Side", line_color='blue')

    else:
        plt_name = dir_name[:dir_name.find("A_")+1]
        # case 2) 그 외 디렉토리: h_a,b,c 와 l_a,b,c
        # h 시리즈
        h_files = ["IGBT1_HS_ICE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_VGE.txt"]
        data_dict_h = {}
        for hf in h_files:
            full_path = os.path.join(dir_path, hf)
            label = hf.replace(".txt", "")
            data_dict_h[label] = load_txt_file(full_path)
        output_h = os.path.join(dir_path, f"{plt_name}_High_Side.jpg")
        plot_and_save_offset(data_dict_h, output_h, title=f"{plt_name}_High_Side", line_color='red')

        # l 시리즈
        l_files = ["IGBT2_LS_ICE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_VGE.txt"]
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
        """
        새로운 파일/폴더가 생성되었을 때 호출.
        폴더일 경우 process_directory를 통해 작업 수행
        """
        if event.is_directory:
            new_dir_path = event.src_path
            print(f"[INFO] 새 디렉토리 생성 감지: {new_dir_path}")
            # WORKS here 10 35
            time.sleep(10)
            process_directory(new_dir_path)

# --------------------------------------------------------------------------
# 6) 메인 함수 (Watchdog 구동)
# --------------------------------------------------------------------------
def main():
    # 실제 감시할 R 폴더 경로로 수정
    watch_path = r"C:\!FAIL_WFM"

    # 옵저버 생성
    event_handler = NewDirectoryHandler()
    observer = Observer()
    # recursive=False: R 하위의 '직계' 디렉토리 생성만 감시.
    # 하위 폴더 생성까지 전부 감시하려면 True로.
    observer.schedule(event_handler, watch_path, recursive=True)

    # 옵저버 시작
    observer.start()
    print(f"[INFO] 디렉토리 감시 시작: {watch_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # test_path = r"C:\!FAIL_WFM\AC_HK3_OSAT_V2\20250524\_20250224\A"
    # print(os.path.exists(test_path))
    # print(os.listdir(test_path))
    main()
