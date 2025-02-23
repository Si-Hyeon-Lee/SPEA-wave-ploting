#C:\Users\go122\Desktop\waveiwer\SPEA_waviewer\Analysis HK3-HK3A-HK4\378000E130JNB10002\New gate Driver\AC_ILM_L7_600V_780A_+15.0V_-05.0V_000.50ohm_006.00ohm_000.00ohm
#C:\Users\go122\Desktop\waveiwer\SPEA_waviewer\Analysis HK3-HK3A-HK4\378000E130JNB10002\Old Gate Driver\AC_ILM_L7_600V_780A_+15.0V_-05.0V_000.47ohm_006.20ohm_000.00ohm
#C:\Users\go122\Desktop\waveiwer\SPEA_waviewer\MOBIS\HK4_waveform data\OLD_WF\AC_ILM_L7_350V_400A_+15.0V_-05.0V_000.47ohm_010.00ohm_000.00ohm

# Log 뒤져보기.

import os
import sys
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from tkinter import filedialog, messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as ticker
from PIL import Image
from matplotlib.font_manager import FontProperties
from tkinter import Toplevel

def resource_path(relative_path):
    """ PyInstaller에서 파일 경로를 처리하는 함수 """
    try:
        # PyInstaller는 임시 폴더를 만들고 그 경로를 _MEIPASS에 저장합니다.
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# 전역 변수
plt_name = ""
file_paths = []
entry_widgets = []
browse_buttons = []
test_datas = []
test_datas_scaled = []  # 스케일된 데이터 저장
test_datas_qutor = []
test_names = []
test_unit_names = []

def read_waveform(file_path):
    """파형 데이터를 읽어 numpy 배열로 반환합니다."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    data = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        try:
            value = float(line.strip())
            data.append(value)
        except ValueError:
            break
    return np.array(data)

def minmax(x):
    return (x - min(x)) / (max(x) - min(x))

def get_qutor(x):
    return int((max(x) - min(x)) / 4)

def open_file(index):
    global file_paths
    # 파일 탐색기에서 파일 선택
    title = ['Old Driver', 'New Driver', 'Mobis']
    file_path = filedialog.askopenfilename(
        title=title[index],
        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")),
        parent=root
    )
    
    if file_path:
        file_paths[index].set(file_path)
        print(f"File {index + 1} Path: {file_path}")

def create_file_selection_window(file_count):
    # 파일 선택 창 생성
    selection_window = tk.Toplevel(root)
    selection_window.transient(root)  # 메인 윈도우보다 앞에 있도록 설정
    selection_window.focus_set()      # 창에 포커스 설정
    selection_window.title("File Selection")

    # 전역 경로 관리
    global file_paths
    file_paths.clear()

    for i in range(file_count):
        if i == 0:
            tmp_txt = "Old Driver Wave File Path"
        elif i == 1:
            tmp_txt = "New Driver Wave File Path"
        elif i == 2:
            tmp_txt = "Mobis Wave File Path"
        else:
            tmp_txt = f"File {i+1} Path"

        # 경로 저장용 StringVar
        file_path_var = tk.StringVar()
        file_paths.append(file_path_var)

        # 경로 입력 라벨
        entry_label = tk.Label(selection_window, text=tmp_txt)
        entry_label.grid(row=i, column=0, padx=10, pady=5)

        # 경로 입력 박스
        entry = tk.Entry(selection_window, width=50, textvariable=file_path_var)
        entry.grid(row=i, column=1, padx=10, pady=5)
        entry_widgets.append(entry)

        # 찾아보기 버튼
        browse_button = tk.Button(selection_window, text="찾아보기", command=lambda idx=i: open_file(idx))
        browse_button.grid(row=i, column=2, padx=10, pady=5)
        browse_buttons.append(browse_button)

    # 테스트 이름 입력 필드 추가
    test_label = tk.Label(selection_window, text="테스트 이름 ex) VGE :")
    test_label.grid(row=file_count, column=0, padx=10, pady=5)

    test_name_var = tk.StringVar()
    test_entry = tk.Entry(selection_window, textvariable=test_name_var, width=50)
    test_entry.grid(row=file_count, column=1, padx=10, pady=5)
    
    # 테스트 단위 필드
    test_unit_label = tk.Label(selection_window, text="테스트 단위 ex) A or V :")
    test_unit_label.grid(row=file_count+1, column=0, padx=10, pady=5)

    test_unit_var = tk.StringVar()
    test_unit_entry = tk.Entry(selection_window, textvariable=test_unit_var, width=50)
    test_unit_entry.grid(row=file_count+1, column=1, padx=10, pady=5)

    def confirm_paths_local():
        test_names.append(test_name_var.get())
        test_unit_names.append(test_unit_var.get())

        # 원본 데이터와 스케일된 데이터 모두 저장
        datas = [read_waveform(path.get()) for path in file_paths]
        scaled_datas = [minmax(data) for data in datas]
        test_datas.append(datas)  # 원본 데이터 저장
        test_datas_scaled.append(scaled_datas)  # 스케일된 데이터 저장

        datas_qutor = get_qutor(datas[0])
        test_datas_qutor.append(str(datas_qutor))

        # 파일 선택 창 닫기
        selection_window.destroy()

    confirm_button = tk.Button(selection_window, text="파일 경로 입력 완료.", command=confirm_paths_local)
    confirm_button.grid(row=file_count+2, column=1, columnspan=5, pady=10)

def ask_file_count():
    file_count_window = tk.Toplevel(root)
    file_count_window.transient(root)  # 메인 윈도우보다 앞에 있도록 설정
    file_count_window.focus_set()      # 창에 포커스 설정
    file_count_window.title("파형 갯수 선택")

    label_file_count = tk.Label(file_count_window, text="파형 갯수:")
    label_file_count.pack(pady=10)

    entry_file_count = tk.Entry(file_count_window)
    entry_file_count.pack(pady=5)

    def on_submit():
        try:
            file_count = int(entry_file_count.get())
            if file_count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "올바른 숫자를 입력하세요.", parent=file_count_window)
            return
        
        global file_paths, entry_widgets, browse_buttons
        file_paths.clear()
        entry_widgets.clear()
        browse_buttons.clear()

        create_file_selection_window(file_count)
        file_count_window.destroy()

    submit_button = tk.Button(file_count_window, text="확인", command=on_submit)
    submit_button.pack(pady=10)

def draw_ddp_plot():
    vertical_offset = 1.5  # y축 오프셋
    # 기존 기능 유지: 새로운 윈도우 창 두 개 생성
    window1 = Toplevel()
    window1.title("Turn Off")
    
    window2 = Toplevel()
    window2.title("Turn On")
    
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    
    total_length = 2000  # 필요한 길이로 조정 가능
    half_length = total_length // 2
    
    # 범례를 위한 레이블 설정
    labels_plotted = set()
    color_labels = {0: 'Old Driver', 1: 'New Driver', 2: 'Mobis'}
    
    # 데이터 저장을 위한 리스트
    plotted_data_main = []
    plotted_data_window1 = []
    plotted_data_window2 = []
    p1s,p2s = [],[]

    for i, (datas, scaled_datas) in enumerate(zip(test_datas, test_datas_scaled)):
        data_mins = []
        data_maxs = []
        for j, (data, scaled_data) in enumerate(zip(datas, scaled_datas)):
            if i== 0: # ICE 파형 3개.
                
                # p2 찾기
                p2 = np.argmax(scaled_data)
            

                # p1 찾기
                p_mid = p2
                while p_mid > 0 and scaled_data[p_mid] > 0.05:
                    p_mid -= 1

                p1 = np.argmax(scaled_data[:p_mid]) if p_mid > 0 else 0
                p1s.append(p1)
                p2s.append(p2)
                print(f'Found p1, p2 [{j}]')

            color = ['r', 'g', 'b', 'violet'][j] if j < 4 else 'violet'
            label = color_labels.get(j, None)
            if label in labels_plotted:
                label = None
            else:
                labels_plotted.add(label)

            # 스케일링을 위한 최소값과 최대값 저장
            data_min = min(data)
            data_max = max(data)
            data_mins.append(data_min)
            data_maxs.append(data_max)

            # 첫 번째 윈도우 Turn Off (p1_start를 중앙에 위치)
            start_index1 = max(p1s[j] - half_length, 0)
            end_index1 = min(p1s[j] + half_length, len(scaled_data))
            x_values1 = np.arange(start_index1, end_index1) - p1s[j]
            data_segment1 = scaled_data[start_index1:end_index1] + 1.5 * i
            ax1.plot(x_values1, data_segment1, color=color, label=label)

            # window1의 데이터 저장 (키 이름 수정)
            plotted_data_window1.append({
                'x_scaled': x_values1,
                'y_scaled': data_segment1,
                'x_original': np.arange(start_index1, end_index1),
                'y_original': data[start_index1:end_index1],
                'data_min': data_min,
                'data_max': data_max,
                'i': i
            })

            # 두 번째 윈도우 Turn On (p2_start를 중앙에 위치)
            start_index2 = max(p2s[j] - half_length, 0)
            end_index2 = min(p2s[j] + half_length, len(scaled_data))
            x_values2 = np.arange(start_index2, end_index2) - p2s[j]
            data_segment2 = scaled_data[start_index2:end_index2] + 1.5 * i
            ax2.plot(x_values2, data_segment2, color=color, label=label)

            # window2의 데이터 저장 (키 이름 수정)
            plotted_data_window2.append({
                'x_scaled': x_values2,
                'y_scaled': data_segment2,
                'x_original': np.arange(start_index2, end_index2),
                'y_original': data[start_index2:end_index2],
                'data_min': data_min,
                'data_max': data_max,
                'i': i
            })
                
        # 주석 추가
        y_pos = 0.5 + 1.5 * i
        x_annotate_pos = -800  # 필요한 경우 x 위치 조정
        ax1.annotate(f'{test_names[i]} {test_datas_qutor[i]} {test_unit_names[i]}/div', (x_annotate_pos, y_pos), fontsize=15)
        ax2.annotate(f'{test_names[i]} {test_datas_qutor[i]} {test_unit_names[i]}/div', (x_annotate_pos, y_pos), fontsize=15)

    # 범례 추가
    ax1.legend()
    ax2.legend()
    
    # x축과 y축의 tick 수 줄이기 및 y축 라벨 숨기기
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(300))
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax1.yaxis.set_major_formatter(ticker.NullFormatter())
    ax1.xaxis.set_major_formatter(ticker.NullFormatter())

    ax2.xaxis.set_major_locator(ticker.MultipleLocator(300))
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax2.yaxis.set_major_formatter(ticker.NullFormatter())
    ax2.xaxis.set_major_formatter(ticker.NullFormatter())

    # 폰트 설정 (필요한 경우)
    font_path = resource_path("TimesNewerRoman-Italic.otf")
    font_prop = FontProperties(fname=font_path, size=25)

    # 그리드 추가 및 제목 설정
    ax1.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
    ax1.set_title("Turn Off Plot", fontproperties=font_prop, loc='left')

    ax2.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
    ax2.set_title("Turn On Plot", fontproperties=font_prop, loc='left')

    # 이미지 로드 및 추가 (필요한 경우)
    img_path = resource_path("spea.png")
    my_img = Image.open(img_path)
    my_img_np = np.array(my_img)

    # 이미지 그리기 (축의 우상단에 배치)
    x_pos = 0.80  # 상대적인 x 위치 (0 ~ 1 사이 값)
    y_pos = 0.87  # 상대적인 y 위치 (0 ~ 1 사이 값)
    width_ratio = 0.10  # 상대적인 너비
    height_ratio = 0.10  # 상대적인 높이

    # 첫 번째 플롯에 이미지 추가
    ax1_inset = fig1.add_axes([x_pos, y_pos, width_ratio, height_ratio], anchor='NE')
    ax1_inset.imshow(my_img_np)
    ax1_inset.axis('off')  # 축을 숨김

    # 두 번째 플롯에 이미지 추가
    ax2_inset = fig2.add_axes([x_pos, y_pos, width_ratio, height_ratio], anchor='NE')
    ax2_inset.imshow(my_img_np)
    ax2_inset.axis('off')  # 축을 숨김

    # 첫 번째 창에 캔버스와 툴바 추가
    canvas1 = FigureCanvasTkAgg(fig1, master=window1)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    toolbar_frame1 = tk.Frame(window1)
    toolbar_frame1.pack(side=tk.BOTTOM, fill=tk.X)
    toolbar1 = NavigationToolbar2Tk(canvas1, toolbar_frame1)
    toolbar1.update()

    # 두 번째 창에 캔버스와 툴바 추가
    canvas2 = FigureCanvasTkAgg(fig2, master=window2)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    toolbar_frame2 = tk.Frame(window2)
    toolbar_frame2.pack(side=tk.BOTTOM, fill=tk.X)
    toolbar2 = NavigationToolbar2Tk(canvas2, toolbar_frame2)
    toolbar2.update()

    # 메인 윈도우의 캔버스에 플롯 추가
    # 먼저 캔버스 지우기
    for widget in canvas_frame.winfo_children():
        widget.destroy()
    
    # 메인 윈도우 플롯 생성
    fig_main, ax_main = plt.subplots(figsize=(10, 5))
    
    # 데이터 플로팅 (전체 데이터를 플롯)
    test_cnt = len(test_datas)
    labels_plotted_main = set()
    for i, (datas, scaled_datas) in enumerate(zip(test_datas, test_datas_scaled)):
        for j, (data, scaled_data) in enumerate(zip(datas, scaled_datas)):
            color = ['r', 'g', 'b', 'violet'][j] if j < 4 else 'violet'
            label = color_labels.get(j, None)
            if label in labels_plotted_main:
                label = None
            else:
                labels_plotted_main.add(label)
            #y_values = scaled_data + 1.5 * i
            y_values = scaled_data + vertical_offset * i
            x_values = np.arange(len(scaled_data))
            ax_main.plot(x_values, y_values, color=color, label=label)
            plotted_data_main.append({
                'x_scaled': x_values,
                'y_scaled': y_values,
                'x_original': x_values,  # 샘플 인덱스
                'y_original': data,  # 원본 y 값
                'data_min': min(data),
                'data_max': max(data),
                'i': i
            })
        ax_main.annotate(f'{test_names[i]} {test_datas_qutor[i]} {test_unit_names[i]}/div', [1500, 0.5+1.5 * i], fontsize=15)

    # 범례 추가
    ax_main.legend()

    # x축과 y축의 tick 수 줄이기 및 축 라벨 숨기기
    ax_main.xaxis.set_major_locator(ticker.MultipleLocator(3000))
    ax_main.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax_main.xaxis.set_major_formatter(ticker.NullFormatter())
    ax_main.yaxis.set_major_formatter(ticker.NullFormatter())

    # 폰트 설정 및 그리드 추가
    ax_main.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
    ax_main.set_title(plt_name, fontproperties=font_prop, loc='left')

    # 이미지 추가
    ax_main_inset = fig_main.add_axes([x_pos, y_pos, width_ratio, height_ratio], anchor='NE')
    ax_main_inset.imshow(my_img_np)
    ax_main_inset.axis('off')  # 축을 숨김

    # 메인 윈도우의 캔버스에 플롯 추가
    canvas_main = FigureCanvasTkAgg(fig_main, master=canvas_frame)
    canvas_main.draw()
    canvas_main.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    # 메인 윈도우의 툴바 추가
    toolbar_frame_main = tk.Frame(canvas_frame)
    toolbar_frame_main.pack(side=tk.BOTTOM, fill=tk.X)
    toolbar_main = NavigationToolbar2Tk(canvas_main, toolbar_frame_main)
    toolbar_main.update()

    # 원래 단위로 평균 변화율을 계산하는 함수
    def compute_avg_rate(click_coords, click_markers, ax, canvas):
        if len(click_coords) == 2:
            # 선택된 점들의 정보 가져오기
            point1 = click_coords[0]
            point2 = click_coords[1]
            x1 = point1['x_value']
            y1_original = point1['y_original']
            x2 = point2['x_value']
            y2_original = point2['y_original']
            i = point1['i']  # 데이터셋 인덱스

            # delta_y 계산
            delta_y_units = y2_original - y1_original

            # delta_t 계산 (x 축 단위)
            delta_t_units = x2 - x1  # x 축의 단위에 따라 다름

            if delta_t_units != 0:
                avg_rate = delta_y_units / delta_t_units  # 평균 변화율 (단위: y단위/x단위)
                unit = test_unit_names[i]
                messagebox.showinfo("평균 변화율", f"두 점 사이의 평균 변화율: {avg_rate:.6f} {unit}/μs")
            else:
                messagebox.showerror("오류", "두 점의 x 좌표가 같습니다.")

            # 마커 제거
            for marker in click_markers:
                marker.remove()
            click_markers.clear()
            click_coords.clear()
            canvas.draw()


    def on_click(event, plotted_data, click_coords, click_markers, ax, canvas):
        if event.inaxes != ax or not event.dblclick:
            return

        x_mouse = event.xdata
        y_mouse = event.ydata

        vertical_offset = 1.5  # y축 오프셋
        i = int(y_mouse / vertical_offset)

        if i < 0 or i >= len(test_datas):
            return

        # 해당 데이터셋의 정보 가져오기
        data_dict = next((d for d in plotted_data if d['i'] == i), None)
        if data_dict is None:
            return

        data_min = data_dict['data_min']
        data_max = data_dict['data_max']

        # y_scaled 계산
        y_scaled = y_mouse - vertical_offset * i

        # y_scaled가 0~1 범위를 벗어날 수 있으므로 클리핑
        y_scaled = np.clip(y_scaled, 0, 1)

        # 원래 y 값 복원
        y_original = y_scaled * (data_max - data_min) + data_min

        # 클릭한 위치의 정보를 저장
        click_coords.append({
            'x_value': x_mouse,
            'y_original': y_original,
            'i': i
        })

        # 마커 그리기
        marker, = ax.plot(x_mouse, y_mouse,
                        marker='s', markersize=10, markeredgecolor='black', markerfacecolor='none',
                        scalex=False, scaley=False)
        canvas.draw()
        click_markers.append(marker)

        if len(click_coords) == 2:
            compute_avg_rate(click_coords, click_markers, ax, canvas)




    # 클릭 이벤트 연결
    click_coords_main = []
    click_markers_main = []
    canvas_main.mpl_connect('button_press_event', lambda event: on_click(event, plotted_data_main, click_coords_main, click_markers_main, ax_main, canvas_main))
    
    click_coords1 = []
    click_markers1 = []
    canvas1.mpl_connect('button_press_event', lambda event: on_click(event, plotted_data_window1, click_coords1, click_markers1, ax1, canvas1))
    
    click_coords2 = []
    click_markers2 = []
    canvas2.mpl_connect('button_press_event', lambda event: on_click(event, plotted_data_window2, click_coords2, click_markers2, ax2, canvas2))

    # 마우스 모션 이벤트 연결
    canvas_main.mpl_connect('motion_notify_event', lambda event: on_motion(event, plotted_data_main, ax_main, canvas_main))
    canvas1.mpl_connect('motion_notify_event', lambda event: on_motion(event, plotted_data_window1, ax1, canvas1))
    canvas2.mpl_connect('motion_notify_event', lambda event: on_motion(event, plotted_data_window2, ax2, canvas2))

def on_motion(event, plotted_data, ax, canvas):
    if event.inaxes != ax:
        if hasattr(on_motion, 'text') and on_motion.text:
            on_motion.text.remove()
            on_motion.text = None
            canvas.draw_idle()
        return

    y_mouse = event.ydata

    vertical_offset = 1.5  # y축 오프셋

    # 데이터셋 인덱스 계산
    i = int(y_mouse / vertical_offset)

    # 인덱스 범위 체크
    if i < 0 or i >= len(test_datas):
        if hasattr(on_motion, 'text') and on_motion.text:
            on_motion.text.remove()
            on_motion.text = None
            canvas.draw_idle()
        return

    # 해당 데이터셋의 최소값과 최대값 가져오기
    data_dict = next((d for d in plotted_data if d['i'] == i), None)
    if data_dict is None:
        if hasattr(on_motion, 'text') and on_motion.text:
            on_motion.text.remove()
            on_motion.text = None
            canvas.draw_idle()
        return

    data_min = data_dict['data_min']
    data_max = data_dict['data_max']

    # y_mouse를 사용하여 y_scaled 계산
    y_scaled = y_mouse - vertical_offset * i

    # y_scaled가 0~1 범위를 벗어날 수 있으므로 클리핑
    y_scaled = np.clip(y_scaled, 0, 1)

    # 원래 y 값 복원
    y_original = y_scaled * (data_max - data_min) + data_min

    unit = test_unit_names[i]
    print(unit)

    if hasattr(on_motion, 'text') and on_motion.text:
        on_motion.text.remove()

    on_motion.text = ax.text(event.xdata, event.ydata, f'y = {y_original:.4f} {unit}',
                             fontsize=10, bbox=dict(facecolor='white', alpha=0.5))

    canvas.draw_idle()


def save_plot():
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    if save_path:
        plt.savefig(save_path)
        messagebox.showinfo("Success", f"Plot saved as {save_path}")

def reset():
    global file_paths, entry_widgets, browse_buttons, test_datas, test_datas_scaled, test_names, test_unit_names

    # Clear all global variables except plt_name
    file_paths.clear()
    entry_widgets.clear()
    browse_buttons.clear()
    test_datas.clear()
    test_datas_scaled.clear()
    test_names.clear()
    test_unit_names.clear()

    # Clear the canvas by destroying the previous plot
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    print("Reset complete!")

def set_graph_title():
    global plt_name
    plt_name = simpledialog.askstring("Graph Title", "그래프의 제목을 입력하세요:", parent=root)
    if not plt_name:
        messagebox.showerror("Error", "그래프 제목을 입력해야 합니다.")

def update_canvas_size(event=None):
    # Update canvas size based on the current window size
    canvas_width = int(root.winfo_width() * 0.9)  # 90% of window width
    canvas_height = int(root.winfo_height() * 0.9)  # 90% of window height
    canvas_frame.config(width=canvas_width, height=canvas_height)

root = tk.Tk()
root.title("SPEA Viewer")

# Maximize the window (but keep window control buttons)
root.state('zoomed')
#root.wm_attributes('-toolwindow', True)
root.iconbitmap('')

# Set up the canvas frame with larger dimensions and place it in the center
canvas_frame = tk.Frame(root)
canvas_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=int(root.winfo_screenwidth() * 0.9), height=int(root.winfo_screenheight() * 0.9))

# Bind the window resizing event to dynamically adjust the canvas size
root.bind('<Configure>', update_canvas_size)

# Adding buttons to the root window
start_button = tk.Button(root, text="Add Test", command=ask_file_count)
start_button.place(x=10, y=20)

plot_button = tk.Button(root, text="Draw Plot", command=draw_ddp_plot)
plot_button.place(x=95, y=20)

save_button = tk.Button(root, text="Save Plot", command=save_plot)
save_button.place(x=190, y=20)

reset_button = tk.Button(root, text="Reset", command=reset)
reset_button.place(x=290, y=20)

title_button = tk.Button(root, text="Set Plot Title", command=set_graph_title)
title_button.place(x=360, y=20)

# Start the Tkinter main loop
root.mainloop() 

# 이 소스코드에서 window1 과 window2 에 plot 을 할때 plot 되는 y data 최대값의 90% 되는 지점과 최대값의 10% 되는 지점을 각각 찾아서 plot 에서 조그마한 동그라미 마커를 남겨줘. 그리고 그렇게 구한 두 지점의 평균 변화율을 계산해서 plot 별로 옆에 값을 단위와 함께 표시해줘.
# 이때 가장 주의해야 할 점은 바로 plot 되는 y data 에 스케일이 되어 있다는거야. 내가 원하는건 두 지점의 평균 변화율을 구할 떄 스케일 되기 이전 값으로 평균 변화율을 구하는 것이야. x 는 스케일 되어있지 않아. 오직 y만 스케일 되어있고 스케일 된 값을 복원하는 로직 우선 이해하도록해.
# 두번째로 주의할 점은 plot 할때 for 문을 돌면서 data들을 여러개 다루는데 이때 모든 data에 대해서 최대값의 90% 되는 데이터와 최대값의 10%가 되는 데이터를 개별적으로 구해야한다는거야. 코드상으로는 for i ~~~ for j~~~ 의 2중 for 문인데 여기서 모든 j 번째 data에 대해서 90% 10% 를 구해서 평균 변화율을 계산하고 이를 plot 에 값과 단위로 나타내야한다는 것이야. 
#  코드를 작성해줘.
