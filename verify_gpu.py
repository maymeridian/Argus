"""
verify_gpu.py

Author: maymeridian
Description: Validates the presence of local NVIDIA library dependencies and 
             confirms that the ONNX Runtime (ORT) can access the CUDA execution provider.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Configure professional logging instead of simple print statements
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def inject_local_libraries(folder_name: str = "libraries") -> bool:
    """
    Attempts to add a local directory to the Windows DLL search path.
    
    Args:
        folder_name (str): The name of the subfolder containing DLLs.
        
    Returns:
        bool: True if the folder was found and added, False otherwise.
    """
    if sys.platform != "win32":
        # DLL injection is specific to Windows
        return True

    base_path = Path(__file__).resolve().parent
    libs_path = base_path / folder_name

    logger.info(f"Looking for local libraries at: {libs_path}")

    if not libs_path.exists():
        logger.warning(f"Library folder '{folder_name}' not found. Relying on system-wide PATH.")
        return False

    try:
        # Python 3.8+ on Windows ignores PATH for DLL resolution; this explicit call is required.
        os.add_dll_directory(str(libs_path))
        logger.info(f"Successfully injected '{folder_name}' into DLL search path.")
        return True
    except OSError as e:
        logger.error(f"Failed to inject DLL directory: {e}")
        return False

def check_onnx_runtime() -> None:
    """Imports ONNX Runtime and checks for CUDA availability."""
    try:
        import onnxruntime as ort
    except ImportError:
        logger.critical("ONNX Runtime is not installed. Please run: pip install onnxruntime-gpu")
        return

    logger.info("--- Runtime Configuration ---")
    logger.info(f"ORT Version: {ort.__version__}")
    
    # get_device() often defaults to CPU until a session is run, checking providers is more reliable
    providers: List[str] = ort.get_available_providers()
    logger.info(f"Available Providers: {providers}")

    validate_cuda_support(providers)

def validate_cuda_support(providers: List[str]) -> None:
    """
    Analyzes the available providers to determine GPU status.
    
    Args:
        providers (List[str]): List of execution providers returned by ORT.
    """
    if 'CUDAExecutionProvider' in providers:
        print("\n" + "="*40)
        print("✅ SUCCESS: CUDA (GPU) is detected and available!")
        print("="*40 + "\n")
    else:
        print("\n" + "="*40)
        print("❌ FAILURE: Only CPU is available.")
        print("Possible causes:")
        print("1. Missing 'onnxruntime-gpu' package (check pip list).")
        print("2. Missing NVIDIA Drivers or CUDA Toolkit.")
        print("3. Missing DLL files in the 'libraries' folder.")
        print("="*40 + "\n")

def main():
    """Main execution entry point."""
    logger.info("Starting GPU Verification...")
    
    # 1. Inject DLLs
    inject_local_libraries("libraries")
    
    # 2. Check Runtime
    check_onnx_runtime()

if __name__ == "__main__":
    main()