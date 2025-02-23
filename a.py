import os
import sys
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as ticker
from PIL import Image, ImageTk
from matplotlib.font_manager import FontProperties

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
    file_path = filedialog.askopenfilename(
        title=f"Select TXT file {index + 1}", 
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

        datas = [minmax(read_waveform(path.get())) for path in file_paths]
        test_datas.append(datas)

        datas_qutor = get_qutor(read_waveform(file_paths[0].get()))
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

def draw_plot():
    # Clear the canvas by destroying the previous plot
    for widget in canvas_frame.winfo_children():
        widget.destroy()
    
    test_cnt = len(test_datas)
    fig, ax = plt.subplots(figsize=(10, 5))
    

    def find_max_average_rate_change(vector):
        '''
        입력 벡터의 최대값 이전까지 평균 변화율 그리고 가장 큰 구간을 리턴
        '''
        # 최대값의 인덱스를 찾음
        max_index = np.argmax(vector) - 500 # Hyper para
        
        # 가장 큰 평균 변화율을 저장할 변수와 해당 구간 초기화
        max_avg_rate_change = None
        max_interval = (None, None)
        
    # 모든 가능한 구간에 대해 평균 변화율 계산
        for start in range(max_index):
            for end in range(start + 1, max_index + 1):
                if end - start == 0: # 0으로 나누는 경우 예외 처리
                    continue
                avg_rate_change = abs((vector[end] - vector[start]) / (end - start))
                if max_avg_rate_change is None or avg_rate_change > max_avg_rate_change:
                    max_avg_rate_change = avg_rate_change
                    max_interval = (start, end)
        
        return max_avg_rate_change, max_interval


    for i, datas in enumerate(test_datas):
        for j, data in enumerate(datas):
            max_avg_rate_change, (p1, _) = find_max_average_rate_change(data)

            # 데이터를 p1부터 그리기
            x_data = np.arange(p1, len(data))  # x 데이터 생성 (p1부터 데이터 끝까지의 인덱스)
            plot_data = data[p1:] + 1.5 * i  # 데이터를 p1부터 슬라이싱하고 y 위치 조정

            color = ['r', 'g', 'b', 'violet'][j] if j < 4 else 'violet'
            ax.plot(x_data, plot_data, color=color)  # 슬라이싱된 데이터와 새로운 x 데이터로 플롯

        ax.annotate(f'{test_names[i]} {test_datas_qutor[i]} {test_unit_names[i]}/div', [1500, 0.5 + 1.5 * i], fontsize=15)


    # for i, datas in enumerate(test_datas):



    #     for j, data in enumerate(datas):
    #         max_avg_rate_change ,(p1,_)  = find_max_average_rate_change(data)
    #         p2 = np.argmax(data)


    #         color = ['r', 'g', 'b', 'violet'][j] if j < 4 else 'violet'
    #         ax.plot(data + 1.5 * i, color=color)
    #     ax.annotate(f'{test_names[i]} {test_datas_qutor[i]} {test_unit_names[i]}/div', [1500, 0.5+1.5 * i], fontsize=15)

    # x축과 y축의 tick 수 줄이기
    ax.xaxis.set_major_locator(ticker.MultipleLocator(3000))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax.yaxis.set_major_formatter(ticker.NullFormatter())

    font_path = resource_path("TimesNewerRoman-Italic.otf")
    font_prop = FontProperties(fname=font_path, size=25)

    ax.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
    ax.set_title(plt_name, fontproperties =font_prop , loc='left')

    # Load the image using PIL
    img_path = resource_path("spea.png")
    my_img = Image.open(img_path)

    # 이미지를 numpy 배열로 변환하여 matplotlib에서 표시
    my_img_np = np.array(my_img)

    # 이미지 그리기 (축의 우상단에 배치)
    # 위치와 크기를 동적으로 결정 (예시: 오른쪽 상단에 고정)
    x_pos = 0.80  # 상대적인 x 위치 (0 ~ 1 사이 값)
    y_pos = 0.87  # 상대적인 y 위치 (0 ~ 1 사이 값)
    width_ratio = 0.10  # 상대적인 너비
    height_ratio = 0.10  # 상대적인 높이

    # 축을 다시 추가
    ax_inset = fig.add_axes([x_pos, y_pos, width_ratio, height_ratio], anchor='NE')
    ax_inset.imshow(my_img_np)
    ax_inset.axis('off')  # 축을 숨김

    # Create canvas and add to window
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    # Add the toolbar for zoom/pan functionality
    toolbar_frame = tk.Frame(canvas_frame)
    toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()

def save_plot():
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    if save_path:
        plt.savefig(save_path)
        messagebox.showinfo("Success", f"Plot saved as {save_path}")

def reset():
    global file_paths, entry_widgets, browse_buttons, test_datas, test_names, test_unit_names

    # Clear all global variables except plt_name
    file_paths.clear()
    entry_widgets.clear()
    browse_buttons.clear()
    test_datas.clear()
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
root.title("SPEA Waviwer")

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

plot_button = tk.Button(root, text="Draw Plot", command=draw_plot)
plot_button.place(x=95, y=20)

save_button = tk.Button(root, text="Save Plot", command=save_plot)
save_button.place(x=190, y=20)

reset_button = tk.Button(root, text="Reset", command=reset)
reset_button.place(x=290, y=20)

title_button = tk.Button(root, text="Set Plot Title", command=set_graph_title)
title_button.place(x=360, y=20)

# Start the Tkinter main loop
root.mainloop()
