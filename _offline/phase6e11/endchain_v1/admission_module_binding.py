"""Read-only origin proof for explicit project module objects, not sys.modules.

Main calls verify(gate, [this_module, *actual_modules]) before dispatch and saves
the returned JSON-safe receipt. Pass imported project helpers explicitly too;
this does not prove in-memory code integrity or discover every dependency.
"""
import hashlib
import json
import os
import pathlib
import re
import types


class ModuleBindingError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(value):
    if not isinstance(value, (str, os.PathLike)) or not str(value):
        raise ModuleBindingError('module_binding_path_missing')
    path = pathlib.Path(value)
    if not path.is_absolute() or '..' in path.parts:
        raise ModuleBindingError('module_binding_path_not_absolute')
    # Check ancestors before resolving: resolve alone hides symlink escapes.
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ModuleBindingError('module_binding_symlink')
    return path.resolve(strict=True)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModuleBindingError('module_binding_duplicate_manifest_key')
        result[key] = value
    return result


def verify(gate, selected_modules):
    """Return a receipt or raise before dispatch; no fallback roots or writes."""
    try:
        checkout = checked_path(os.environ.get('GITHUB_WORKSPACE'))
        candidate = checked_path(gate.sources)
        if not checkout.is_dir() or not candidate.is_dir():
            raise ModuleBindingError('module_binding_root_not_directory')
        manifest = checked_path(pathlib.Path(gate.out) / 'candidate.json').read_bytes()
        sources = json.loads(manifest, object_pairs_hook=unique_object)['sources']
        if not isinstance(sources, dict):
            raise ModuleBindingError('module_binding_manifest_sources')
        modules = list(selected_modules)
        if not modules:
            raise ModuleBindingError('module_binding_empty_selection')
        records = []
        for module in modules:
            if not isinstance(module, types.ModuleType):
                raise ModuleBindingError('module_binding_module_object_required')
            if not isinstance(module.__name__, str):
                raise ModuleBindingError('module_binding_module_name')
            actual = checked_path(getattr(module, '__file__', None))
            if actual.suffix != '.py' or not actual.is_file():
                raise ModuleBindingError('module_binding_python_source_required')
            # Candidate wins when its directory is inside the checkout.
            if actual.is_relative_to(candidate):
                root, origin = candidate, 'candidate'
            elif actual.is_relative_to(checkout):
                root, origin = checkout, 'checkout'
            else:
                raise ModuleBindingError('module_binding_external_origin')
            relative = actual.relative_to(root).as_posix()
            expected = sources.get(relative)
            if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
                raise ModuleBindingError('module_binding_source_not_registered')
            pinned = checked_path(candidate / relative)
            if not pinned.is_relative_to(candidate) or not pinned.is_file():
                raise ModuleBindingError('module_binding_candidate_escape')
            candidate_bytes = pinned.read_bytes()
            if sha(candidate_bytes) != expected:
                raise ModuleBindingError('module_binding_candidate_hash')
            actual_bytes = actual.read_bytes()
            canonicalization = 'byte-exact'
            if origin == 'checkout':
                canonicalization = 'CRLF-to-LF-only'
                same = actual_bytes.replace(b'\r\n', b'\n') == candidate_bytes.replace(b'\r\n', b'\n')
            else:
                same = actual_bytes == candidate_bytes
            if not same:
                raise ModuleBindingError('module_binding_loaded_source_changed')
            records.append({'module': module.__name__, 'relative_path': relative,
                'origin_root': origin, 'actual_sha256': sha(actual_bytes),
                'candidate_sha256': expected, 'canonicalization': canonicalization})
        return {'status': 'SELECTED_MODULE_SOURCE_BINDING_PASS', 'modules': records,
            'selected_module_count': len(records), 'candidate_manifest_sha256': sha(manifest),
            'dependency_scope': 'explicit_selected_modules_only', 'hosted_admitted': False}
    except ModuleBindingError:
        raise
    except (OSError, TypeError, KeyError, AttributeError, ValueError):
        raise ModuleBindingError('module_binding_input_or_io') from None
