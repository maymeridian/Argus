# **Argus**

Automatically rename prop photos based on their Certificate of Authenticity (COA) titles using AI-powered OCR.

*Named after Argus Panoptes, the all-seeing giant of Greek mythology.*

## Features

- 🤖 AI-powered OCR using olmOCR
- 📷 Automatic COA detection and matching
- 🏷️ Smart file renaming based on COA information
- 🖥️ Modern web-based GUI with drag-and-drop
- 🐋 Docker containerization for easy deployment

## Prerequisites

- **Docker Desktop** (with WSL2 enabled on Windows)
- **Python 3.11+**
- **NVIDIA GPU** with 15GB+ VRAM (for olmOCR)
- **NVIDIA Container Toolkit** (for GPU access in Docker)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd prop-renamer
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - Enable WSL2 backend (Windows only)
   - Install NVIDIA Container Toolkit for GPU support

4. **Build the Docker image**
   ```bash
   docker compose build
   ```

## Usage

### GUI Method (Recommended)

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Upload your images** by dragging and dropping them into the upload box

4. **Configure settings** in the sidebar (optional)

5. **Click "Process and Rename"** and wait for the processing to complete

6. **Download your renamed files** from the images folder

### Command Line Method

1. **Place your images** in the `images` folder

2. **Run the Docker container**
   ```bash
   docker compose up
   ```

3. **Check the `images` folder** for renamed files

## How It Works

1. Images are processed using olmOCR to extract text
2. COAs are identified by looking for specific keywords (e.g., "DOCUMENT CERTIFIES", "PRODUCTION OF")
3. Prop photos are grouped with their corresponding COA (COA always comes after its prop photos)
4. Files are renamed based on the item code and description from the COA
   - Format: `EXPANSE####-Description-1.jpg`, `EXPANSE####-Description-2.jpg`, `EXPANSE####-Description-coa.jpg`

## Project Structure

```
prop-renamer/
├── main.py             # Main processing script
├── application/        # Streamlit GUI application
│   ├── app.py          # Main Streamlit app
│   ├── ui_components.py
│   ├── processing.py
│   ├── file_operations.py
│   └── config.py
├── handler/            # Core processing modules
│   ├── reader.py       # OCR reading functionality
│   ├── matcher.py      # COA detection and matching
│   └── renamer.py      # File renaming logic
├── Dockerfile          # Docker image configuration
├── docker-compose.yml  # Docker compose setup
├── requirements.txt    # Python dependencies
├── images/             # Input/output folder for images
└── output/             # OCR results (JSONL format)
```

## Troubleshooting

- **GPU not detected**: Ensure NVIDIA Container Toolkit is installed and Docker has GPU access
- **Out of memory**: Reduce batch size or use a GPU with more VRAM
- **Files not renamed**: Check that COA images contain the expected text format
- **OCR not working**: Ensure Docker container has internet access to download the olmOCR model
- **Streamlit won't start**: Run `pip install -r requirements.txt` to install dependencies
