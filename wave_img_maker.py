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
    '''
    test_item = {
        ('HK3','400A','000.50','000.50') : 'SW',
        ('HK3','408A','000.50','000.50') : 'SW',
        ('HK3','780A','000.50','006.00') : 'RBSOA1',
        ('HK3','1000A','000.50','006.00') : 'RBSOA2',

        ('HK3A','400A','000.50','000.50') : 'SW',
        ('HK3A','408A','000.50','000.50') : 'SW',
        ('HK3A','780A','000.50','006.00') : 'RBSOA1',
        ('HK3A','1000A','000.50','006.00') : 'RBSOA2',

        ('HK5','200A','000.50','000.50') : 'SW',
        ('HK5','390A','000.50','006.00') : 'RBSOA1',
        ('HK5','500A','000.50','006.00') : 'RBSOA2',
    }
    
    dirs=dir_path.split('\\')
    bacord = dirs[4].split('_')[3]
    '''
    C:\  0
        !FAIL_WFM\ 1
            AC_HK3A_OSAT_V00\ 2 
                20250318_143933\ 3 
                    TEST_LOT_ID_378001X000JR590181_20250318_143933\  4 
                        AC_L7_600V_400A_+15.0V_-05.0V_000.50ohm_000.50ohm_000.00ohm 5

    C:\ 0
        !FAIL_WFM\ 1
            AC_HK3A_OSAT_V00\ 2
                20250318_143933\ 3 
                    TEST_LOT_ID_378001X000JR590181_20250318_143933\ 4
                        AC_L7_600V_400A_+15.0V_-05.0V_000.50ohm_000.50ohm_000.00ohm 5
    '''
    tmp = dirs[5].split('_')
    k = (
        dirs[2].split('_')[1].strip(),
        tmp[3].strip(),
        tmp[6].removesuffix('ohm').strip(),
        tmp[7].removesuffix('ohm').strip()
    )
    
    if '_SC' in dir_path: 
        test_type = 'SC' 
    # elif k in test_item :
    #     print(f'Found key : {k}')
    #     test_type = test_item[k]
    else:
        test_type = test_item.get(k, "UNKNOWN_TEST")
        if test_type == "UNKNOWN_TEST":
            print(f'[Error] : No test item in dictionary \n Test_item key = {k} \n')
    if is_high_side:
        return f'{bacord}_AC_{test_type}_High_Side.jpg'
    return f'{bacord}_AC_{test_type}_Low_Side.jpg'
    
def plot_and_save_offset(data_dict, output_path, title, line_color='red', is_sc=False):
    """
    Plot wave data and save to output_path with dynamic offset if 'is_sc' is True.
    data_dict: { "IGBT1_HS_VGE": [...], "IGBT1_HS_VCE": [...], ... }
    output_path: jpg file path, usually same as input data path.
    title: Title of the graph, usually same as input data's folder.
    line_color: HS -> 'red', LS -> 'blue'
    is_sc: True if folder name contains '_SC'. Then waveforms are dynamically offset 
           to avoid overlap.
    """

    scale_map = {
        'VGE': (10.0, 'V'),        # 10 V / div
        'VCE': (200.0, 'V'),       # 200 V / div
        'ICE': (200.0, 'A'),       # 200 A / div
        'POW1': (100000.0, 'kW')   # 100 kW / div (100000 = 100k in raw scale)
    }

    plt.figure(figsize=(16, 8))
    plt.title(title)

    labels = list(data_dict.keys())
    
    # [1] Determine the plotting range based on whether it's SC or not
    N_list = []
    for lbl in labels:
        N_list.append(len(data_dict[lbl]) - 1)  # Each array's first element is length info
    max_len = max(N_list) if N_list else 0

    if is_sc and max_len > 4:
        start_i = int(max_len * 0.40)
        end_i = int(max_len * 0.70)
    else:
        start_i = 0
        end_i = max_len

    # Prepare offset logic
    # If '_SC' in directory => dynamic offset, else => fixed offset (8.0 increments)
    fixed_offset_distance = 8.0
    current_top = 0.0  # Tracks top of previously plotted waveform when using dynamic offsets

    y_lim_top = 0.0
    line_objs = []

    for idx, label in enumerate(labels):
        raw_data = data_dict[label][1:]  # Drop first value
        if not raw_data:
            print(f"[Warning] No '{label}' data in {output_path} folder.")
            continue

        partial_data = raw_data[start_i:end_i]

        # (2) Determine scale factor based on label
        scale_factor = 1.0
        unit_per_div = '?'
        for key in scale_map:
            if key in label.upper():
                scale_factor = 1.0 / scale_map[key][0]
                unit_per_div = f"{scale_map[key][0]} {scale_map[key][1]}"
                break

        scaled_data = [val * scale_factor for val in partial_data]

        # (3) Calculate dynamic or fixed offset
        if is_sc:
            # For SC directories, dynamically compute offset to avoid overlap
            local_min = min(scaled_data) if scaled_data else 0
            local_max = max(scaled_data) if scaled_data else 0
            # Shift so that local_min is slightly above current_top
            offset_val = current_top - local_min + 1.0  # +1.0 margin
            offset_data = [val + offset_val for val in scaled_data]
            # Update current_top for the next waveform
            current_top = offset_val + local_max
        else:
            # Original fixed offset approach
            offset_val = idx * fixed_offset_distance
            offset_data = [val + offset_val for val in scaled_data]

        # (4) X-axis from start_i to end_i in 1 kHz steps
        x_vals = [i / 1000.0 for i in range(start_i, end_i)]

        short_name = label[-4:].removeprefix('_').upper()
        if short_name == 'POW1':
            legend_str = f"{short_name} (1 div = {scale_map['POW1'][0]/1000.0} {scale_map['POW1'][1]})"
        else:
            legend_str = f"{short_name} (1 div = {unit_per_div})"

        line_obj, = plt.plot(x_vals, offset_data, color=line_color,
                             linewidth=1.0, label=legend_str)
        line_objs.append(line_obj)

        # Label text near the start of each waveform
        plt.text(
            x_vals[0],
            offset_data[0],
            short_name + '   ',
            va='center',
            ha='right',
            fontsize=9,
            color='k'
        )

        local_data_max = max(offset_data) if offset_data else 0
        if local_data_max > y_lim_top:
            y_lim_top = local_data_max

    # (5) X-axis limits
    plt.xlim(start_i / 1000.0, end_i / 1000.0)

    # (6) Y-axis range
    # Include some margin on the top for labels
    plt.ylim(-2, y_lim_top + 1.0)
    y_ticks = np.arange(-2, y_lim_top + 2.0, 1.0)
    plt.yticks(y_ticks)
    plt.tick_params(axis='y', labelleft=False)

    # (7) X-axis tick settings
    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(5.0))   # major = 5
    ax.xaxis.set_minor_locator(MultipleLocator(1.0))   # minor = 1

    ax.xaxis.set_major_formatter(lambda val, pos: f"{int(val)} us")

    ax.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5)
    ax.grid(True, which='minor', axis='both', linestyle='--', linewidth=0.3)

    if line_objs:
        plt.legend(handles=line_objs, loc='lower right', fontsize=9,
                   handlelength=0, handletextpad=0)

    plt.savefig(output_path)
    plt.close()
    print(f"[INFO] Saved Plot : {output_path}")

def process_directory(dir_path):
    '''
    DFS search. if dir_path contains txt file then start plotting.
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
    
    # _SC 포함 여부 판별
    is_sc = ('_SC' in dir_path)

    # High Side
    h_files = ["IGBT1_HS_VGE.txt", "IGBT1_HS_VCE.txt", "IGBT1_HS_ICE.txt","IGBT1_HS_POW1.txt"]
    h_files.reverse()
    data_dict_h = {}
    for hf in h_files:
        full_path = os.path.join(dir_path, hf)
        label = hf.replace(".txt", "")
        data_dict_h[label] = load_txt_file(full_path)

    output_h = os.path.join(dir_path, get_img_name(dir_path=dir_path, is_high_side=True))
    plot_and_save_offset(
        data_dict_h, 
        output_h, 
        title=f"{plt_name}_High_Side", 
        line_color='red',
        is_sc=is_sc
    )

    # Low Side
    l_files = ["IGBT2_LS_VGE.txt", "IGBT2_LS_VCE.txt", "IGBT2_LS_ICE.txt","IGBT2_LS_POW1.txt"]
    l_files.reverse()
    data_dict_l = {}
    for lf in l_files:
        full_path = os.path.join(dir_path, lf)
        label = lf.replace(".txt", "")
        data_dict_l[label] = load_txt_file(full_path)

    output_l = os.path.join(dir_path, get_img_name(dir_path=dir_path, is_high_side=False))
    plot_and_save_offset(
        data_dict_l, 
        output_l, 
        title=f"{plt_name}_Low_Side", 
        line_color='blue',
        is_sc=is_sc
    )

class NewDirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            new_dir_path = event.src_path
            print(f"[INFO] New Folder Detected : {new_dir_path} .")
            time.sleep(3)
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

if __name__ == "__main__":
    main()

