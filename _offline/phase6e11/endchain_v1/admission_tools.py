"""Pinned public build tools for disposable CI, never Supabase credentials."""
import hashlib
import io
import os
import pathlib
import tarfile
import urllib.request
import zipfile

BUN = ('https://github.com/oven-sh/bun/releases/download/bun-v1.4.1/bun-linux-x64.zip',
       '74c1c3bee7cd998500c8f969cd8972355ac6a07207e94a39eece1999b56ffabf', 36659492)
PNPM = ('https://github.com/pnpm/pnpm/releases/download/v12.3.0/pnpm-linux-x64.tar.gz',
        '64dc4ce87f81ea614a4e4fecd5e6f81d8ef91fae37434602e6a5aebf6dd22939', 19674963)
UPSTREAM = '21db855916f2c2b12f61cde923a27094b8528b23'


def fetch(pin):
    url, digest, size = pin
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(size+1)
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('admission_tool_digest')
    return data


def extract_pnpm(data, target):
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        by_name={m.name:m for m in members}
        seen = set()
        if len(members)>2000 or sum(m.size for m in members)>100000000:
            raise ValueError('admission_tool_archive_size')
        for member in members:
            path = pathlib.PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or '\\' in member.name
                    or member.name.casefold() in seen or not(member.isfile() or member.isdir() or member.islnk())):
                raise ValueError('admission_tool_archive_path')
            if member.islnk() and (member.linkname not in by_name or not by_name[member.linkname].isfile()):
                raise ValueError('admission_tool_archive_link')
            seen.add(member.name.casefold())
        expanded=sum(by_name[m.linkname].size if m.islnk() else m.size for m in members)
        if expanded>100000000:raise ValueError('admission_tool_archive_size')
        archive.extractall(target, members=[m for m in members if not m.islnk()], filter='data')
        # Preserve the pinned package's internal duplicates as regular files,
        # never filesystem links to a caller-selected destination.
        for member in members:
            if member.islnk():
                original=by_name[member.linkname]
                data=archive.extractfile(original).read(original.size+1)
                if len(data)!=original.size:raise ValueError('admission_tool_archive_short')
                destination=target/member.name
                destination.parent.mkdir(parents=True,exist_ok=True)
                with destination.open('xb') as stream:stream.write(data)
    executable = target/'pnpm'
    if not executable.is_file() or executable.is_symlink(): raise ValueError('admission_pnpm_missing')
    executable.chmod(0o755)
    return executable


def install(gate):
    if (os.environ.get('GITHUB_REPOSITORY') != 'Yourizorge/fitmetzorge-staging'
            or os.environ.get('GITHUB_REF') != 'refs/heads/main'
            or os.environ.get('GITHUB_RUN_ATTEMPT') != '1'):
        raise ValueError('admission_tools_disposable_only')
    folder = gate.work/'admission-build-tools'
    folder.mkdir(exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(fetch(BUN))) as archive:
        info = archive.getinfo('bun-linux-x64/bun')
        if info.file_size>120000000: raise ValueError('admission_bun_size')
        binary = archive.read(info)
    bun = folder/'bun'
    with bun.open('xb') as stream: stream.write(binary)
    bun.chmod(0o755)
    pnpm_folder = folder/'pnpm-tool'; pnpm_folder.mkdir()
    pnpm = extract_pnpm(fetch(PNPM), pnpm_folder)
    for executable, expected in ((bun,'1.4.1'), (pnpm,'12.3.0')):
        result = gate.command('admission-tool-version', [str(executable),'--version'],timeout=10)
        if result.stdout.strip()!=expected: raise ValueError('admission_tool_version')
    upstream = gate.work/'admission-cli-upstream'
    gate.command('admission-upstream', ['git','clone','--depth','1','--branch','v2.117.0',
        'https://github.com/supabase/cli.git',str(upstream)],timeout=90)
    result = gate.command('admission-upstream-pin',['git','-C',str(upstream),'rev-parse','HEAD'])
    if result.stdout.strip()!=UPSTREAM: raise ValueError('admission_upstream_pin')
    os.environ['PATH']=str(folder)+os.pathsep+str(pnpm_folder)+os.pathsep+os.environ['PATH']
    component = gate.sources/'_offline/phase6e11/endchain_v1/cli_predispatch'
    gate.command('admission-upstream-deps',[str(pnpm),'--dir',str(upstream),'install',
        '--filter','supabase...','--frozen-lockfile','--ignore-scripts',
        '--os','linux','--cpu','x64','--libc','glibc'],timeout=180)
    gate.command('admission-cli-patch',['python3','-B',str(component/'prepare.py'),
        '--upstream',str(upstream)],timeout=30)
    for path in (upstream/'apps/cli/cli_predispatch',component):
        gate.command('admission-hook-deps',[str(pnpm),'--dir',str(path),'install',
            '--frozen-lockfile','--ignore-scripts'],timeout=90)
    gate.command('admission-hook-tests',['node','--test',str(component/'test_hook.cjs'),
        str(component/'test_policy.cjs')],timeout=60)
    old_pythonpath=os.environ.get('PYTHONPATH')
    os.environ['PYTHONPATH']=str(gate.sources/'_offline/phase6e_server_v1')+(
        os.pathsep+old_pythonpath if old_pythonpath else '')
    try:
        gate.command('admission-cli-python',['python3','-B','-m','unittest','discover','-s',
            str(component),'-p','test_*.py'],timeout=60)
    finally:
        if old_pythonpath is None:os.environ.pop('PYTHONPATH',None)
        else:os.environ['PYTHONPATH']=old_pythonpath
    gate.command('admission-cli-smoke',['python3','-B',str(component/'smoke.py'),
        '--upstream',str(upstream),'--bun',str(bun),'--receipt',str(gate.out/'cli-predispatch-help.json')],timeout=30)
    os.environ['FMZ_CLI_PREDISPATCH_UPSTREAM']=str(upstream)
    os.environ['FMZ_BUN']=str(bun)
    gate.save('admission-build-tools.json', {'bun_sha256':BUN[1], 'pnpm_sha256':PNPM[1],
        'bun':'1.4.1','pnpm':'12.3.0','upstream':UPSTREAM,'hosted_calls':0,
        'release_binary_equivalence_claimed':False})
