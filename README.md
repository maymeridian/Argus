# Argus

**Automated Asset Management & OCR Sorting System**

Argus is a specialized desktop application engineered for the automated organization of large-scale memorabilia archives. It leverages a local, AI-powered Optical Character Recognition (OCR) pipeline to analyze digital assets, extract text (SKUs and item descriptions), and systematically restructure file directories.

Built on **Python 3.12**, **CustomTkinter**, and **ONNX Runtime**, Argus utilizes a custom dependency injection architecture to deliver a fully portable GPU-accelerated environment. This eliminates the need for system-wide CUDA Toolkit installations, allowing for high-performance inference on any NVIDIA-equipped workstation.

---

## Core Capabilities

* **High-Performance OCR:** Implements `RapidOCR` via `ONNX Runtime` for millisecond-latency text extraction.
* **Semantic Grouping:** Automatically identifies "Certificate of Authenticity" (COA) documentation and associates it with corresponding artifact images.
* **Consensus Normalization:** Algorithms analyze multiple data points within a group to error-correct typos and standardize descriptions across the dataset.
* **Automated Taxonomy:** Renames files according to a strict schema (`SKU-Description-Sequence.jpg`) and sorts them into Anchor Folders based on SKU prefixes.
* **Portable GPU Engine:** Proprietary DLL injection logic enables full CUDA acceleration without requiring administrative installation of the CUDA Toolkit.
* **Modern Interface:** A responsive, dark-themed GUI designed for efficiency and ease of use.

---

## Installation

Argus is distributed as a standalone, portable executable. No installation wizard is required.

### Prerequisites
* **OS:** Windows 10/11 (64-bit)
* **Hardware:** NVIDIA Graphics Card (Maxwell architecture or newer recommended)
* **Drivers:** Standard NVIDIA Game Ready or Studio Drivers

### Quick Start
1.  **Download** the latest release artifact (ZIP).
2.  **Extract** the archive to a local directory (e.g., `D:\Tools\Argus`).
3.  **Execute** `Argus.exe`.

---

## Usage Guide

1.  **Initialization:** Launch the application. The console will verify the initialization of the ONNX inference engine.
2.  **Ingestion:** Click **"SORT PHOTOS"** and select the directory or specific images for processing.
3.  **Processing:** The system will scan, group, and normalize metadata in real-time. Logs are displayed in the application console.
4.  **Output:** Processed files are moved to the configured `Output` directory, organized by show title or SKU group.

---

## Development Documentation

### Environment Setup
1.  Ensure **Python 3.12+** is installed.
2.  Install dependencies via pip:
    ```bash
    pip install -r requirements.txt
    ```

### GPU Dependency Injection (Crucial)
Argus uses a local `libraries` folder to inject GPU DLLs at runtime. This allows the app to be portable.

You must create a folder named `libraries` in the project root and populate it with the following NVIDIA binaries:

| Component | Required Binaries |
| :--- | :--- |
| **Math Utils** | `cublas64_12.dll`, `cublasLt64_12.dll` |
| **Runtime** | `cudart64_12.dll` |
| **FFT & Rand** | `cufft64_11.dll`, `curand64_10.dll` |
| **Compiler** | `nvrtc64_120_0.dll` |
| **Deep Neural** | `cudnn64_9.dll`, `cudnn_adv64_9.dll`, `cudnn_cnn64_9.dll`, `cudnn_ops64_9.dll`, `cudnn_graph64_9.dll`, `cudnn_heuristic64_9.dll`, `cudnn_engines_precompiled64_9.dll`, `cudnn_engines_runtime_compiled64_9.dll` |

*> Note: The `libraries/` folder is excluded from version control via `.gitignore`.*

---

## Build Pipeline

This repository includes a `build.bat` script utilizing **PyInstaller** to compile the application into a single-folder distribution.

### Build Instructions
1.  Verify `icon.ico` is present in the project root.
2.  Execute the build script:
    ```cmd
    build.bat
    ```
3.  The compiled artifact will be generated in `dist/Argus`.

**Script Actions:**
* Sanitizes previous build artifacts (`build/`, `dist/`).
* Bundles the `libraries/` directory and `settings.json`.
* Hooks CustomTkinter and RapidOCR resources.
* Embeds the application icon and assigns the Windows AppUserModelID.

---

## ⚙️ Configuration

Runtime behavior is controlled via `settings.json` or the in-app **Settings** menu.

* **Output Path:** target directory for organized assets.
* **Compute Backend:** Switch between `CUDA` (GPU) and `CPU` modes.
* **Asset Filtering:** Toggle exclusion of raw COA images from the final output.
* **Heuristics:** Customizable "Strong" and "Weak" keyword lists for document classification.

---

## License

**Proprietary Software.**
Internal Tooling. All rights reserved.
*Author: maymeridian*
