from pathlib import Path
from .cleaner import clean_image
def remove_gps(src:Path,dst:Path): return clean_image(src,dst,gps_only=True)
