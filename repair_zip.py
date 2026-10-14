"""Rebuild a ZIP with UTF-8 names, remove macOS metadata, verify retained bytes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_ENTRIES=10_000
MAX_TOTAL=512*1024*1024

def repaired_name(info):
    name=info.filename
    if not info.flag_bits & 0x800:
        # Recover only when CP437-preserved bytes are valid UTF-8. No guessing GBK.
        try:name=name.encode('cp437').decode('utf-8')
        except (UnicodeEncodeError,UnicodeDecodeError):pass
    if '\\' in name or '\x00' in name or ':' in name:
        raise ValueError('Unsupported or unsafe archive name')
    parts=PurePosixPath(name).parts
    if name.startswith('/') or '..' in parts or not parts:
        raise ValueError('Unsafe archive member path')
    return name

def metadata(name):
    return any(p=='__MACOSX' or p=='.DS_Store' or p.startswith('._') for p in PurePosixPath(name).parts)

def repair(source:Path,output:Path|None=None):
    source=source.resolve(strict=True)
    output=(output or source.with_name(source.stem+'_Windows_UTF8.zip')).absolute()
    if source==output.resolve() or output.exists():raise FileExistsError('Refusing to overwrite input or existing output')
    if not output.parent.is_dir():raise ValueError('Output parent must exist')
    retained,removed,hashes=[],[],{}
    tmp=None
    try:
        with zipfile.ZipFile(source) as zin:
            members=zin.infolist()
            if len(members)>MAX_ENTRIES or sum(i.file_size for i in members)>MAX_TOTAL:
                raise ValueError('Archive exceeds entry or uncompressed-size limit')
            seen=set()
            entries=[]
            for info in members:
                if info.flag_bits & 1:raise ValueError('Encrypted ZIP unsupported')
                if (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Symbolic-link member unsupported')
                name=repaired_name(info)
                if metadata(name):removed.append(name);continue
                collision=name.rstrip('/').casefold()
                if collision in seen:raise ValueError('Duplicate or case-colliding output names')
                seen.add(collision)
                entries.append((info,name))
            handle=tempfile.NamedTemporaryFile(prefix='.zip-repair-',suffix='.tmp',dir=output.parent,delete=False)
            tmp=Path(handle.name);handle.close()
            with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as zout:
                for info,name in entries:
                    new=zipfile.ZipInfo(name,date_time=info.date_time)
                    new.compress_type=zipfile.ZIP_DEFLATED
                    new.external_attr=info.external_attr
                    digest=hashlib.sha256()
                    with zin.open(info) as src,zout.open(new,'w') as dst:
                        while chunk:=src.read(1024*1024):digest.update(chunk);dst.write(chunk)
                    hashes[name]=digest.hexdigest();retained.append(name)
        with zipfile.ZipFile(tmp) as check:
            for name,expected in hashes.items():
                digest=hashlib.sha256()
                with check.open(name) as stream:
                    while chunk:=stream.read(1024*1024):digest.update(chunk)
                if digest.hexdigest()!=expected:raise ValueError('Byte verification failed')
        # Same-filesystem hard link publishes atomically and refuses existing destinations.
        # If this filesystem lacks hard links, fail without copying/overwriting the output.
        os.link(tmp,output)
        return {'output':str(output),'retained':retained,'removed_metadata':removed,
                'sha256_verified_files':len(hashes),'input_changed':False}
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('--output',type=Path)
    args=p.parse_args();print(json.dumps(repair(args.input,args.output),ensure_ascii=True,indent=2))

if __name__=='__main__':main()
