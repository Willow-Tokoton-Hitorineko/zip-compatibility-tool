"""Offline demonstration using a temporary synthetic archive."""
import json
import tempfile
import zipfile
from pathlib import Path
from repair_zip import repair

with tempfile.TemporaryDirectory() as directory:
    source=Path(directory)/'synthetic.zip'
    with zipfile.ZipFile(source,'w') as archive:
        archive.writestr('中文/示例.txt','Synthetic content only.')
        archive.writestr('__MACOSX/._example.txt',b'metadata')
    result=repair(source)
    result['output']=Path(result['output']).name
    # Escaped JSON is lossless and works even on legacy Windows console encodings.
    print(json.dumps(result,ensure_ascii=True,indent=2))
