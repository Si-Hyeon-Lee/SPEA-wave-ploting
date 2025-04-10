# Semiconductor Defect Waveform Plotter

> **Purpose** : Automatically detect, parse, and visualize electrical waveforms (VGE, VCE, ICE, POW) recorded during power‐semiconductor testing when a device is classified as **FAIL**.

---

## 📚 Project Overview

In a high‑volume wafer or packaged‑device test line, every failed DUT (Device Under Test) produces raw text files that contain time‑series measurements such as gate‑emitter voltage (VGE), collector‑emitter voltage (VCE), collector current (ICE), and instantaneous power (POW). These measurements are stored inside a dedicated failure repository (e.g. `C:\!FAIL_WFM`).

This project **continuously watches** that repository, **discovers** newly created DUT folders, **extracts** the numeric vectors, and **renders** publication‑quality waveform images—one for the high‑side switch and one for the low‑side switch—so that process engineers and researchers can quickly inspect abnormal behaviour.

Although the code targets an industrial environment, it is intentionally lightweight and self‑contained so that university laboratories can reproduce the workflow on a standard Windows PC.

---

## 🖼️ Result Image example.
WIP

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Real‑time monitoring** | Uses `watchdog.Observer` to detect freshly created test folders without polling. |
| **Recursive discovery** | Performs a depth‑first search to locate any directory that contains the expected `*.txt` waveform files. |
| **Automated plot naming** | Derives a descriptive JPEG filename (`<BARCODE>_AC_<TEST>_<High or Low>_Side.jpg`) from the directory hierarchy. |
| **Dynamic offset plotting** | When the folder name includes `_SC` (short‑circuit test), each waveform is vertically shifted just enough to avoid overlap, maximising readability. |
| **Flexible scaling** | Physical units per division (e.g. 10 V/div, 200 A/div) are automatically annotated in the legend. |
| **Zero external dependencies** | Requires only `numpy`, `matplotlib`, and `watchdog`. No proprietary libraries or test‑station software. |

---

## 🔍 How It Works (Detailed Flow)

1. **Folder Detection** – `Observer` triggers `NewDirectoryHandler.on_created` whenever a new directory appears.
2. **Debounce** – The handler waits 3 seconds to ensure all text files are fully written.
3. **DFS Search** – `process_directory()` recursively scans sub‑folders until it finds a set of waveform files.
4. **Data Loading** – `load_txt_file()` converts each line to `float`, ignoring malformed rows.
5. **Plot Naming** – `get_img_name()` parses the directory structure, looks up the test type, and returns a barcode‑based JPEG filename.
6. **Plotting** – `plot_and_save_offset()`
   - Normalises each channel according to `scale_map`.
   - Applies either **fixed** (8 div) or **dynamic** offsets.
   - Adds legends and unit annotations.
   - Saves JPEG image at the source folder.
     
---


## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 📢 Acknowledgements

- The data used in the semiconductor test cannot be provided due to SPEA's security.
- Open‑source libraries: **NumPy**, **Matplotlib**, **Watchdog**.


