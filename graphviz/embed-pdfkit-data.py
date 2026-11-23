"""Inline the runtime assets used by the pinned PDFKit bundle."""

import base64
import json
import re
import sys
from pathlib import Path


def embed(bundle: Path, data: Path) -> None:
    source = bundle.read_text(encoding="utf-8")
    metrics = re.compile(
        r'fs2\.readFileSync\(__dirname \+ "/data/([\w-]+\.afm)", "utf8"\)'
    )
    source, count = metrics.subn(
        lambda match: json.dumps((data / match[1]).read_text(encoding="utf-8")),
        source,
    )
    if count != 14:
        raise ValueError(f"Expected 14 PDFKit font metric reads, found {count}")

    profile = "sRGB_IEC61966_2_1.icc"
    profile_read = 'fs2.readFileSync(`${__dirname}/data/' + profile + '`)'
    if source.count(profile_read) != 1:
        raise ValueError("Expected one PDFKit color profile read")
    profile_bytes = base64.b64encode((data / profile).read_bytes()).decode("ascii")
    source = source.replace(profile_read, f'Buffer.from("{profile_bytes}", "base64")')
    source, count = re.subn(
        r'^var __dirname = "[^"]*/node_modules/pdfkit/js";\n',
        "",
        source,
        flags=re.MULTILINE,
    )
    if count != 1 or "__dirname" in source:
        raise ValueError("Unexpected PDFKit bundle path references")
    bundle.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    embed(Path(sys.argv[1]), Path(sys.argv[2]))
