"""Scoped exact-byte project imports for an independent installed-code collector.

Use for the entire inspection, not only module construction. Not a sandbox for
malicious approved source or a proof of external interpreter/extension binaries.
The caller must bootstrap this module from its independently pinned raw bytes.
"""
import _imp
import builtins
import hashlib
import importlib
import importlib.machinery
import importlib.util
import pathlib
import re
import sys
import sysconfig
import threading
import types

PREFIX = "_offline/phase6e11/endchain_v1/"
_ACTIVE = None
_ABSENT = object()
_STDLIB = tuple({pathlib.Path(sysconfig.get_path(key)).resolve()
                 for key in ("stdlib", "platstdlib")} | {pathlib.Path(sys.base_prefix).resolve() / "DLLs"})


class TrustedImportError(ValueError):
    pass


def _name(value):
    return type(value) is str and re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", value, re.ASCII)


def _plain(path):
    return all(not p.is_symlink() and not getattr(p, "is_junction", lambda: False)()
               for p in (path, *path.parents))


class TrustedImports:
    """One single-threaded collector scope. Never replace an existing module."""

    def __init__(self, root, sources):
        root = pathlib.Path(root).absolute()
        if not _plain(root) or not root.is_dir():
            raise TrustedImportError("trusted_root_origin")
        if type(sources) is not dict or not 0 < len(sources) <= 4096:
            raise TrustedImportError("trusted_sources")
        self.root = root.resolve(strict=True)
        self.sources = dict(sources)
        self.index = {}
        folded = set()
        for path, digest in self.sources.items():
            if (type(path) is not str or not re.fullmatch(r"[A-Za-z0-9_./-]+", path)
                    or any(p in ("", ".", "..") for p in path.split("/"))
                    or any(re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
                           or p.endswith(".") for p in path.split("/"))
                    or path.casefold() in folded
                    or type(digest) is not str or not re.fullmatch("[a-f0-9]{64}", digest)):
                raise TrustedImportError("trusted_source_entry")
            folded.add(path.casefold())
            if path.startswith(PREFIX) and path.endswith(".py"):
                tail = path[len(PREFIX):-3]
                package = tail.endswith("/__init__")
                name = (tail[:-9] if package else tail).replace("/", ".")
                if not _name(name) or name in self.index:
                    raise TrustedImportError("trusted_module_alias")
                self.index[name] = (path, package)
        self.owned = {}
        self.loading = set()
        self.owner = None
        self.failed = False
        self.closed = False

    def deny(self, reason):
        self.failed = True
        raise TrustedImportError(reason)

    def live(self):
        if (_ACTIVE is not self or self.closed or self.failed
                or threading.get_ident() != self.owner or threading.active_count() != 1):
            self.deny("trusted_session_inactive_or_concurrent")

    def raw(self, relative):
        self.live()
        if relative not in self.sources:
            self.deny("trusted_source_missing")
        path = self.root / relative
        try:
            if not _plain(path) or not path.resolve(strict=True).is_relative_to(self.root):
                self.deny("trusted_source_origin")
            if not path.is_file() or path.stat().st_size > 8_000_000:
                self.deny("trusted_source_size")
            raw = path.read_bytes()
        except OSError:
            self.deny("trusted_source_io")
        if len(raw) > 8_000_000 or hashlib.sha256(raw).hexdigest() != self.sources[relative]:
            self.deny("trusted_source_hash")
        return raw

    def project(self, name):
        if not _name(name):
            self.deny("trusted_module_name")
        top = name.split(".")[0]
        tree = self.root / PREFIX
        return (name in self.index or any(n.split(".")[0] == top for n in self.index)
                or (tree / top).exists() or (tree / (top + ".py")).exists())

    def check(self, name):
        self.live()
        if name not in self.index:
            self.deny("trusted_project_module_unlisted:" + name)
        relative, package = self.index[name]
        raw = self.raw(relative)
        cached = sys.modules.get(name, _ABSENT)
        if cached is not _ABSENT:
            if cached is not self.owned.get(name):
                self.deny("trusted_preexisting_module:" + name)
            spec = getattr(cached, "__spec__", None)
            if (getattr(cached, "__loader__", None) is not self or spec is None
                    or spec.loader is not self or spec.name != name
                    or getattr(cached, "__file__", None) != str(self.root / relative)
                    or spec.origin != str(self.root / relative)
                    or getattr(cached, "__trusted_imports__", None) is not self):
                self.deny("trusted_cached_identity:" + name)
            if package and cached.__path__ != [str((self.root / relative).parent)]:
                self.deny("trusted_package_path:" + name)
        elif name in self.owned:
            self.deny("trusted_owned_module_removed:" + name)
        return raw

    def guard(self, name):
        if self.project(name):
            parts = name.split(".")
            for i in range(1, len(parts) + 1):
                self.check(".".join(parts[:i]))
        else:
            if name.split(".")[0] not in sys.stdlib_module_names:
                self.deny("trusted_external_dependency_unbound:" + name)
            cached = sys.modules.get(name, _ABSENT)
            if cached is not _ABSENT:
                self.external_spec(name, getattr(cached, "__spec__", None))

    def external_spec(self, name, spec):
        if spec is None or spec.name != name:
            self.deny("trusted_external_spec:" + name)
        if spec.origin in ("built-in", "frozen"):
            return
        if not isinstance(spec.origin, str):
            self.deny("trusted_external_origin:" + name)
        path = pathlib.Path(spec.origin).resolve()
        if (path.is_relative_to(self.root) or not any(path.is_relative_to(p) for p in _STDLIB)
                or any(p in ("site-packages", "dist-packages") for p in path.parts)):
            self.deny("trusted_external_origin:" + name)

    def absolute(self, name, globals, level):
        if level:
            package = (globals or {}).get("__package__")
            if not package:
                self.deny("trusted_relative_import")
            return importlib.util.resolve_name("." * level + name, package)
        return name

    def guard_fromlist(self, absolute, fromlist):
        if fromlist and self.project(absolute):
            parent = sys.modules.get(absolute)
            if "*" in fromlist and parent is not None:
                fromlist = getattr(parent, "__all__", tuple(vars(parent)))
            for item in fromlist:
                if item == "*":
                    continue
                child = absolute + "." + item
                value = getattr(parent, item, None) if parent is not None else None
                if child in self.index or isinstance(value, types.ModuleType):
                    self.guard(child)
                    if isinstance(value, types.ModuleType) and value is not self.owned.get(child):
                        self.deny("trusted_parent_attribute:" + child)

    def imported(self, name, globals=None, locals=None, fromlist=(), level=0):
        self.live()
        absolute = self.absolute(name, globals, level)
        self.guard(absolute)
        self.guard_fromlist(absolute, fromlist)
        result = self.original_import(name, globals, locals, fromlist, level)
        self.guard(absolute)
        self.guard_fromlist(absolute, fromlist)
        return result

    def dynamic(self, name, package=None):
        self.live()
        absolute = importlib.util.resolve_name(name, package) if name.startswith(".") else name
        self.guard(absolute)
        result = self.original_dynamic(absolute)
        self.guard(absolute)
        return result

    def file_spec(self, name, location=None, *args, **kwargs):
        # Legacy ad-hoc file loaders have no transitive/cached-code contract.
        # Do not silently permit them, even for a source-listed project file.
        self.live()
        self.deny("trusted_file_loader_unsupported:" + str(name))

    def find_spec(self, fullname, path=None, target=None):
        self.live()
        if not self.project(fullname):
            self.guard(fullname)
            for finder in (importlib.machinery.BuiltinImporter, importlib.machinery.FrozenImporter,
                           importlib.machinery.PathFinder):
                spec = finder.find_spec(fullname, path)
                if spec is not None:
                    self.external_spec(fullname, spec)
                    return spec
            self.deny("trusted_external_missing:" + fullname)
        raw = self.check(fullname)
        relative, package = self.index[fullname]
        if target is not None:
            self.deny("trusted_reload_unsupported")
        spec = importlib.machinery.ModuleSpec(fullname, self,
            origin=str(self.root / relative), is_package=package)
        spec.has_location = True
        if package:
            spec.submodule_search_locations = [str((self.root / relative).parent)]
        # Hash and compile the same captured buffer, never a loader's .pyc.
        spec.loader_state = raw
        return spec

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        self.live()
        name = module.__spec__.name
        relative, _ = self.index[name]
        raw = module.__spec__.loader_state
        if (type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != self.sources[relative]
                or name in self.owned or sys.modules.get(name) is not module):
            self.deny("trusted_execution_identity")
        self.owned[name] = module
        self.loading.add(name)
        module.__trusted_imports__ = self
        module.__builtins__ = {**vars(builtins), "__import__": self.imported}
        try:
            exec(compile(raw, str(self.root / relative), "exec", dont_inherit=True), module.__dict__)
            self.check(name)
        except BaseException:
            self.failed = True
            raise
        finally:
            self.loading.discard(name)

    def module(self, name):
        self.live()
        if not self.project(name):
            self.deny("trusted_not_project:" + str(name))
        return self.dynamic(name)

    def bound_module(self, name, root, sources):
        self.live()
        if pathlib.Path(root).resolve(strict=True) != self.root or sources != self.sources:
            self.deny("trusted_context_binding")
        return self.module(name)

    def __enter__(self):
        global _ACTIVE
        if _ACTIVE is not None or self.closed or self.owner is not None or threading.active_count() != 1:
            raise TrustedImportError("trusted_session_busy_or_concurrent")
        if type(sys.meta_path) is not list or not isinstance(builtins.__import__, types.BuiltinFunctionType):
            raise TrustedImportError("trusted_preexisting_import_hook")
        _imp.acquire_lock()
        self.owner = threading.get_ident()
        self.original_import = builtins.__import__
        self.original_dynamic = importlib.import_module
        self.original_file_spec = importlib.util.spec_from_file_location
        self.original_meta = tuple(sys.meta_path)
        try:
            _ACTIVE = self
            builtins.__import__ = self.imported
            importlib.import_module = self.dynamic
            importlib.util.spec_from_file_location = self.file_spec
            sys.meta_path.insert(0, self)
        except BaseException:
            builtins.__import__ = self.original_import
            importlib.import_module = self.original_dynamic
            importlib.util.spec_from_file_location = self.original_file_spec
            sys.meta_path[:] = self.original_meta
            self.closed = True
            _ACTIVE = None
            _imp.release_lock()
            raise
        return self

    def __exit__(self, kind, value, trace):
        global _ACTIVE
        problem = None
        try:
            if kind is None:
                try:
                    self.live()
                    for name in self.owned:
                        self.check(name)
                    if (builtins.__import__ != self.imported or importlib.import_module != self.dynamic
                            or importlib.util.spec_from_file_location != self.file_spec
                            or tuple(sys.meta_path) != (self, *self.original_meta)):
                        self.deny("trusted_import_hooks_changed")
                except BaseException as error:
                    problem = error
        finally:
            builtins.__import__ = self.original_import
            importlib.import_module = self.original_dynamic
            importlib.util.spec_from_file_location = self.original_file_spec
            sys.meta_path[:] = self.original_meta
            # Never remove/replace unrelated preexisting module objects.
            for name, module in reversed(list(self.owned.items())):
                if sys.modules.get(name) is module:
                    del sys.modules[name]
                parent_name, _, child = name.rpartition(".")
                parent = self.owned.get(parent_name)
                if parent is not None and getattr(parent, child, None) is module:
                    delattr(parent, child)
            self.closed = True
            _ACTIVE = None
            _imp.release_lock()
        if problem is not None:
            raise problem
        return False
