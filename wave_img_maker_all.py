import sys
import os
import time
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt

def load_txt_file(txt_path):
    '''
    Read text file which is given and return float vector data(=list)
    '''
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

def get_img_name(dir_path:str,is_high_side:bool):
    '''
    Parsing dir_name for get img file name.
    dir_name should be absolute path with containing _ 
    
     C:\!FAIL_WFM\HK3_ACH_rev000\TEST_LOT_ID_378000E130PS2C0012_AB2507030012_20250305_155743\AC_L7_600V_408A_+15.0V_-05.0V_000.50ohm_000.50ohm_000.00ohm

    -> 378000E130PS2C0012_AC_SW_High_Side.jpg
    '''
    test_item = {
        ('HK3','400A',0.5,0.5) : 'SW',
        ('HK3','408A',0.5,0.5) : 'SW',
        ('HK3','780A',0.5,6) : 'RBSOA1',
        ('HK3','1000A',0.5,6) : 'RBSOA2',

        ('HK3A','400A',0.5,0.5) : 'SW',
        ('HK3A','408A',0.5,0.5) : 'SW',
        ('HK3A','780A',0.5,6) : 'RBSOA1',
        ('HK3A','1000A',0.5,6) : 'RBSOA2',

        ('HK5','200A',0.5,0.5) : 'SW',
        ('HK5','390A',0.5,6) : 'RBSOA1',
        ('HK5','500A',0.5,6) : 'RBSOA2',
    }
    
    dirs=dir_path.split('\\')
    # ['C:', '!FAIL_WFM', 'HK3_ACH_rev000', 'TEST_LOT_ID_378000E130PS2C0012_AB2507030012_20250305_155743', 'AC_L7_600V_408A_+15.0V_-05.0V_000.50ohm_000.50ohm_000.00ohm']
    bacord = dirs[3].split('_')[3]
    print(bacord)

    # Find HK
    tmp = dirs[4].split('_')
    k = (dirs[2].split('_')[0],
        tmp[3],float(tmp[6].removesuffix('ohm')),
        float(tmp[7].removesuffix('ohm')) 
    )
    print(k)

    if '_SC' in dir_path: 
        test_type = 'SC' 
    else :
        test_type =test_item[k]

    if is_high_side:
        return f'{bacord}_AC_{test_type}_High_Side.jpg'
    return f'{bacord}_AC_{test_type}_Low_Side.jpg'
    

def plot_and_save_offset(data_dict, output_path, title, line_color='red'):
    """
    Ploting wave data and save it to output_path.

    data_dict: { "IGBT1_HS_VGE": [...], "IGBT1_HS_VCE": [...], ... }
    output_path: jpg file path , Usally same as input data path.
    title: Title of graph, Usally same as input data's floder.
    line_color: HS for red , LS for blue.
    """

    scale_map = {
        'VGE': (10.0, 'V'),    # 10 V / div
        'VCE': (200.0, 'V'),   # 200 V / div
        'ICE': (200.0, 'A'),   # 200 A / div
        'POW1': (100000.0 ,'kW') #(100.0, 'kW'), # 100 kW / div
    }

    plt.figure(figsize=(16, 8))
    plt.title(title)

    labels = list(data_dict.keys())

    # Offset if Large Current , shoud be get bigger.
    offset_distance = 8.0  
    offsets = [i * offset_distance for i in range(len(labels))]
    y_lim_top = 0.0

    line_objs = [] # for plt.legnd.

    for idx, label in enumerate(labels):
        raw_data = data_dict[label][1:]  # The first value is Length of txt file.
        if not raw_data :
            print(f"[Warning] No '{label}' data in {output_path} Folder.")
            continue
        # scaling data by provided division.
        scale_factor = 1.0
        unit_per_div = '?'
        for key in scale_map:
            if key in label.upper():
                scale_factor = 1.0 / scale_map[key][0]  # 예: 1/10.0
                unit_per_div = f"{scale_map[key][0]} {scale_map[key][1]}"
                break
        scaled_data = [val * scale_factor for val in raw_data]

        # Set offset
        offset_val = offsets[idx]
        offset_data = [val + offset_val for val in scaled_data]

        x_vals = [i / 1000.0 for i in range(len(offset_data))]

        short_name = label[-4:].removeprefix('_').upper()  # "VGE", "VCE" ...
        legend_str = f"{short_name} (1 div = {unit_per_div})"
        if short_name == 'POW1': legend_str = f"{short_name} (1 div = {scale_map[short_name][0]/1000.0} {scale_map[short_name][1]})"

        line_obj, = plt.plot(x_vals, offset_data, color=line_color, linewidth=1.0,
                             label=legend_str)
        line_objs.append(line_obj)


        plt.text(
            0, offset_val,
            short_name + '   ',
            va='center',
            ha='right',
            fontsize=9,
            color='k'
        )

        local_max = max(offset_data) if offset_data else 0
        if local_max > y_lim_top:
            y_lim_top = local_max

    # Setting X range.
    max_len = max((len(data_dict[lbl]) for lbl in labels), default=1)
    x_max_us = (max_len - 1) / 1000.0 if max_len > 1 else 1.0
    plt.xlim(0, x_max_us)

    # Setting Y range and tick , 1. div = 1 grid.
    plt.ylim(-2, y_lim_top + 1.0)
    y_ticks = np.arange(-2, y_lim_top + 2.0, 1.0)  # 1
    plt.yticks(y_ticks)
    plt.tick_params(axis='y', labelleft=False)  # Hide y label.

    # Set Grid, Ticks for x axis 5 makes clean plot.
    ax = plt.gca()
    major_step = 5.0
    minor_step = 1.0
    ax.xaxis.set_major_locator(MultipleLocator(major_step))
    ax.xaxis.set_minor_locator(MultipleLocator(minor_step))

    # label format : 0 us, 5 us, ...
    ax.xaxis.set_major_formatter(lambda val, pos: f"{int(val)} us")

    # Grid: major/minor both True.
    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)
    ax.grid(True, which='minor', axis='both', linestyle='--', linewidth=0.3)

    if line_objs:
        plt.legend(handles=line_objs, loc='lower right', fontsize=9,handlelength=0, handletextpad=0,) #bbox_to_anchor=(1.1, 1.05)

    # Save
    plt.savefig(output_path)
    plt.close()
    print(f"[INFO] Saved Plot : {output_path}")


def process_directory(dir_path):
    '''
    DFS serach. if dir_path contains txt file then start ploting.
    '''
    print(f"[*] process_directory: {dir_path}")
    sub_items = os.listdir(dir_path)
    txt_files = [f for f in sub_items if f.endswith('.txt')]
    if not txt_files:
        for item in sub_items:
            sub_path = os.path.join(dir_path, item)
            if os.path.isdir(sub_path):
                process_directory(sub_path)
        return
    
    # FOUND TXT
    dir_name = os.path.basename(dir_path)

    plt_name = dir_name[:dir_name.find("A_")+1] if "A_" in dir_name else dir_name
    
    # High Side
    h_files = ["IGBT1_HS_VGE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_ICE.txt","IGBT1_HS_POW1.txt"]
    h_files.reverse()
    data_dict_h = {}
    for hf in h_files:
        full_path = os.path.join(dir_path, hf)
        label = hf.replace(".txt", "")
        data_dict_h[label] = load_txt_file(full_path)
    #output_h = os.path.join(dir_path, f"{plt_name}_High_Side.jpg")
    output_h = os.path.join(dir_path,get_img_name(dir_path=dir_path,is_high_side=True))
    plot_and_save_offset(data_dict_h, output_h, title=f"{plt_name}_High_Side", line_color='red')

    # Low Side
    l_files = ["IGBT2_LS_VGE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_ICE.txt","IGBT2_LS_POW1.txt"]
    l_files.reverse()
    data_dict_l = {}
    for lf in l_files:
        full_path = os.path.join(dir_path, lf)
        label = lf.replace(".txt", "")
        data_dict_l[label] = load_txt_file(full_path)
    #output_l = os.path.join(dir_path, f"{plt_name}_Low_Side.jpg")
    output_l = os.path.join(dir_path,get_img_name(dir_path=dir_path,is_high_side=False))
    # 나중에 title 명도 output 이랑 동일하게 원하면 걍 title 만 output_h or l 로 할 것.
    plot_and_save_offset(data_dict_l, output_l, title=f"{plt_name}_Low_Side", line_color='blue')

# WathDogHandler for File Creation Event handle.
class NewDirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            new_dir_path = event.src_path
            print(f"[INFO] New Folder Detected : {new_dir_path} .")
            time.sleep(5)
            process_directory(new_dir_path)

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

# FOR debug.
# sys.stderr = StreamToLogger("wave_img_maker_stderr.log")
if __name__ == "__main__":
    main()
