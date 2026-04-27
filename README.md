# NexusTag

**NexusTag** is a desktop image annotation tool with AI-assisted object detection. Manually draw bounding boxes, assign class labels, run YOLO-based detection automatically, and export annotations in multiple industry-standard formats.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt5](https://img.shields.io/badge/UI-PyQt5-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Features

- **Manual annotation** — Draw bounding boxes with mouse drag (W to enter draw mode)
- **AI detection** — Load a YOLO model and run detection on single images or the entire dataset
- **Undo** — Ctrl+Z undoes the last shape addition or deletion
- **Multiple export formats** — YOLO, Pascal VOC (XML), CreateML (JSON)
- **Class management** — Load/create `classes.txt`, add new classes on the fly
- **Auto-save** — Optionally save annotations automatically when navigating between images
- **Image verification** — Mark images as verified with a visual indicator
- **Zoom & pan** — Scroll wheel or Z/X keys; Center button to reset view

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Git

---

### Windows

**1. Clone the repository**
```bat
git clone https://github.com/Abdullahkanaan/NexusTag.git
cd NexusTag
```

**2. Create a virtual environment**
```bat
python -m venv nexustag_venv
nexustag_venv\Scripts\activate
```

**3. Install dependencies**
```bat
pip install -r requirements.txt
```

> If you get a Qt plugin conflict with OpenCV, install the headless version instead:
> ```bat
> pip uninstall opencv-python -y
> pip install opencv-python-headless
> ```

**4. Run the application**
```bat
python main.py
```

---

### Linux

**1. Install system dependencies**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

**2. Clone the repository**
```bash
git clone https://github.com/Abdullahkanaan/NexusTag.git
cd NexusTag
```

**3. Create a virtual environment**
```bash
python3 -m venv nexustag_venv
source nexustag_venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```

> OpenCV and PyQt5 can conflict on Linux. Install the headless version to avoid issues:
> ```bash
> pip uninstall opencv-python -y
> pip install opencv-python-headless
> ```

**5. Run the application**
```bash
python3 main.py
```

---

### macOS

**1. Install Homebrew and Python** (skip if already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python git
```

**2. Clone the repository**
```bash
git clone https://github.com/Abdullahkanaan/NexusTag.git
cd NexusTag
```

**3. Create a virtual environment**
```bash
python3 -m venv nexustag_venv
source nexustag_venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```

> On macOS, prefer the headless OpenCV to avoid Qt conflicts:
> ```bash
> pip uninstall opencv-python -y
> pip install opencv-python-headless
> ```

**5. Run the application**
```bash
python3 main.py
```

---

## Workflow

### 1. Load Images

**File → Open Images Folder** — Select a folder containing your images (JPG, PNG, BMP, GIF supported).

A `labels/` folder is automatically created next to your images folder for storing annotation files.

### 2. Load or Create Classes

In the **Classes** panel, click **Open Current Dataset classes.txt**. If no file exists, you will be prompted to create one.

Click **Add New Class** to add classes one at a time. Enable **Use Default Class** to automatically assign a class to every new bounding box you draw.

### 3. Annotate Images

1. Press **W** to enter draw mode (cursor becomes a crosshair)
2. Click and drag to draw a bounding box
3. Press **W** again to exit draw mode
4. Select a box and press **E** to assign or change its class
5. Press **S** to save annotations for the current image

Use **Ctrl+Z** to undo the last box drawn or deleted.

### 4. AI-Assisted Detection

1. In the **AI Mode** panel, select the model family (YOLO)
2. Click **Upload Model** and choose your `.pt` model file — a `yolov8n.pt` is included
3. Optionally click **Upload Model YAML** to load class names from a YAML config
4. Select which class to detect and which label to assign
5. Choose **Single Frame** or **All Images** and click **Run Detection**
6. Press **R** to run detection on the current image directly

### 5. Export Annotations

**File → Export Annotations** — Choose a format and output directory:

| Format | Output | Coordinates |
|--------|--------|-------------|
| YOLO | `.txt` per image | Normalized (x_center, y_center, width, height) |
| Pascal VOC | `.xml` per image | Absolute pixel coordinates |
| CreateML | `.json` per image | Percentage of image dimensions |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `W` | Toggle draw mode |
| `S` | Save current annotations |
| `D` | Next image |
| `A` | Previous image |
| `Z` | Zoom in |
| `X` | Zoom out |
| `Q` | Delete selected box(es) |
| `E` | Set class for selected box |
| `R` | Run AI detection on current image |
| `Space` | Toggle image verification |
| `Shift` | Select all boxes |
| `C` (hold) | Hover to select boxes |
| `V` (hold) | Hover to deselect boxes |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Shift+D` | Delete current image (with confirmation) |
| `Esc` | Show/hide shortcuts reference |

---

## Project Structure

```
NexusTag/
├── main.py                        # Entry point
├── nexustag.py                    # Main window (MVC coordinator)
├── app_ui.py                      # Qt UI layout
├── requirements.txt               # Python dependencies
├── run.sh                         # Quick launch script (Linux/macOS)
├── yolov8n.pt                     # Pre-downloaded YOLO nano model
├── controllers/
│   ├── ai_controller.py           # AI detection logic
│   ├── file_controller.py         # File I/O and export
│   ├── ui_controller.py           # Navigation, zoom, visual settings
│   └── class_controller.py        # Class management
├── models/
│   ├── canvas.py                  # Drawing canvas widget
│   ├── dataset.py                 # Image and annotation data management
│   ├── shape.py                   # Bounding box representation
│   └── annotation.py              # Annotation state
├── utils/
│   ├── ai_detector.py             # YOLO inference wrapper
│   ├── exporters.py               # Annotation format exporters
│   └── shortcuts.py               # Keyboard shortcut handler
└── dialogs/
    ├── export_dialog.py           # Export format selection dialog
    └── shortcuts_info_dialog.py   # Shortcuts reference dialog
```

---

## Annotation File Format

NexusTag saves annotations in **YOLO format** by default:

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates are normalized to `[0, 1]` relative to image dimensions. One `.txt` file is created per image in the `labels/` folder.

---

## Troubleshooting

**Qt platform plugin error on Linux**
```
Could not load the Qt platform plugin "xcb"
```
Fix: Replace `opencv-python` with `opencv-python-headless`:
```bash
pip uninstall opencv-python -y
pip install opencv-python-headless
```

**`python` command not found on Linux/macOS**

Use `python3` instead of `python`, or create an alias:
```bash
alias python=python3
```

**Virtual environment not activating on Windows (execution policy error)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## License

This project is licensed under the MIT License.
