import sys
import os

# Get current notebook directory
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
current_dir = "/Workspace" + os.path.dirname(notebook_path)

# Add to sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Added to path: {current_dir}")