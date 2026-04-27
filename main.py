#!/usr/bin/env python3
"""
Nexus Tag: AI-Assisted Annotation Tool
Main application entry point.
"""

import sys
import os
import warnings

def setup_qt_environment():
    """Setup Qt environment variables before importing PyQt."""
    # Set Qt environment variables
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexustag_venv")
    if os.path.exists(venv_path):
        qt_plugin_path = os.path.join(venv_path, "lib/python3.10/site-packages/PyQt5/Qt5/plugins")
        if os.path.exists(qt_plugin_path):
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugin_path
    
    # Disable OpenCV's Qt usage to prevent conflicts
    os.environ["OPENCV_OPENCL_RUNTIME"] = ""
    
    # Suppress DeprecationWarning about sipPyTypeDict
    warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")

def main():
    """Main application entry point."""
    # Setup environment before importing Qt
    setup_qt_environment()
    
    from PyQt5.QtWidgets import QApplication

    # Import and start the application
    from nexustag import NexusTag

    app = QApplication(sys.argv)
    window = NexusTag()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
