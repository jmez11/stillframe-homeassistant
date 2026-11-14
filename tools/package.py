"""Build the manual-install bundle without credentials or development caches."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
component = root / "custom_components" / "stillframe"
version = json.loads((component / "manifest.json").read_text())["version"]
output = root / "dist" / f"stillframe-homeassistant-{version}.zip"
output.parent.mkdir(exist_ok=True)
files = [p for p in component.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
files += [root / "README.md", root / "hacs.json"]
files += list((root / "docs").glob("*.md"))
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(root).as_posix())
print(output)
