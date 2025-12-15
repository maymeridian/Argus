# Argus

**Automated Image Renaming & Sorting System for Memorabilia Archives.**

Argus is a specialized desktop application designed to organize large collections of digital assets (specifically movie props and Certificates of Authenticity). It utilizes local AI-powered OCR (Optical Character Recognition) to scan images, extract SKUs and item descriptions, and automatically rename and sort files into a structured directory tree.

Built with **Python**, **CustomTkinter**, and **ONNX Runtime**, Argus features a fully portable GPU acceleration engine that runs on NVIDIA hardware without requiring the user to install the CUDA Toolkit.

---

## 🚀 Key Features

* **AI-Powered Scanning:** Uses `RapidOCR` and `ONNX Runtime` to read text from images in milliseconds.
* **Intelligent Grouping:** Automatically detects "Certificate of Authenticity" (COA) documents and groups them with their associated prop images.
* **Consensus Normalization:** Analyzing multiple images to fix typos and standardize item descriptions automatically.
* **Smart Renaming:** Renames files to a standard format: `SKU-Description-Sequence.jpg`.
* **Anchor Sorting:** Creates folders based on Show Titles or SKU prefixes and moves files automatically.
* **Portable GPU Engine:** Custom dependency injection allows the app to run with full CUDA acceleration on any PC with NVIDIA drivers—no complex installation required.
* **Modern GUI:** Clean, dark-themed interface built with CustomTkinter.

---

## 📦 Installation & Usage

### For End Users
Argus is distributed as a portable standalone application.

1.  **Download** the latest release (ZIP archive).
2.  **Extract** the folder to your preferred location.
3.  **Run `Argus.exe`**.
    * *Requirement:* A PC with an NVIDIA Graphics Card and standard Game Ready / Studio Drivers installed.

### How to Use
1.  **Select Photos:** Click "SORT PHOTOS" and select the images you wish to process.
2.  **Processing:** Argus will scan, analyze, and group the images. Progress is shown in the console.
3.  **Result:** Files are copied to the `Output` folder (configurable in Settings), renamed and organized by folder.

---

## 🛠️ Development Setup

If you want to run Argus from source or build it yourself, follow these steps.

### 1. Prerequisites
* Python 3.12+
* NVIDIA GPU (Recommended)

### 2. Dependencies
Install the required Python packages:
```bash
pip install customtkinter rapidocr_onnxruntime onnxruntime-gpu
```
### 3. The "Libraries" Folder (**Crucial**)

Argus uses a local `libraries` folder to inject GPU DLLs at runtime. This allows the app to be portable.

You must create a folder named `libraries` in the project root and populate it with the following NVIDIA binaries (extracted from CUDA 12.4 and cuDNN 9.x):
```text
cublas64_12.dll
cublasLt64_12.dll
cudart64_12.dll
cufft64_11.dll
curand64_10.dll
cusolver64_11.dll
nvrtc64_12.dll
nvrtc-builtins64_124.dll
cudnn*.dll  (All cuDNN 9.x binaries)
```

## 🏗️ Building the Executable

This project includes a build script that uses **PyInstaller** to package the application, assets, and GPU libraries into a single folder.

1.  Ensure you have the `icon.ico` file in the root directory.
2.  Run the build script:

    ```bat
    build.bat
    ```

3.  The final output will be located in `dist/Argus`.

**Build Script Logic:**
The `build.bat` script automatically:
* Cleans previous build artifacts.
* Bundles the `libraries` folder.
* Collects CustomTkinter and RapidOCR themes.
* Sets the executable icon and Window taskbar ID.

---

## ⚙️ Configuration

Settings are persisted in `settings.json`. You can modify these via the GUI "Settings" menu:

* **Output Folder:** Destination for sorted files.
* **GPU Acceleration:** Toggle between CUDA (Fast) and CPU (Compatibility) modes.
* **Discard COA:** Option to rename but exclude the actual Certificate image from the final folder.
* **Detection Lists:** Customize "Strong" and "Weak" keywords used to identify Certificates.

---

## 📝 License

Proprietary / Internal Tool.
*Author: maymeridian*
