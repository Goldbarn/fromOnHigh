import runpy
import os
import sys

# This script now serves as a clean entry point to the application.

# Add the 'src' directory to sys.path so its internal imports can be resolved
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# The path to the main script in the 'src' directory
main_path = os.path.join(src_path, 'main.py')

runpy.run_path(main_path, run_name='__main__')
