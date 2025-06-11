import sys
from pathlib import Path

# Ensure the 'src' folder is on sys.path so imports like "from matai…" resolve
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
