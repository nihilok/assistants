from pathlib import Path


class FilesystemError(Exception):
    pass

class FilesystemService:

    @staticmethod
    def read_file(path: Path | str) -> str:
        if not isinstance(path, Path):
            path = Path(path)

        if not path.exists():
            raise FilesystemError(f"File {path} does not exist.")

        with open(path, "r") as f:
            return f.read()


    @staticmethod
    def auto_complete_path(partial_path: str) -> str:
        import os
        # Remember if input was relative
        is_relative = not Path(partial_path).is_absolute()
        # Expand ~ and environment variables
        expanded = Path(partial_path).expanduser()
        expanded = Path(str(expanded))  # ensure Path after expanduser

        # If the path is a directory and exists, return as-is (with trailing sep)
        if expanded.exists() and expanded.is_dir():
            result = expanded
            add_sep = True
        else:
            parent = expanded.parent
            prefix = expanded.name
            if not parent.exists() or not parent.is_dir():
                return partial_path
            matches = [p.name for p in parent.iterdir() if p.name.startswith(prefix)]
            if not matches:
                return partial_path
            if len(matches) == 1:
                result = parent / matches[0]
            else:
                def common_prefix(strs):
                    if not strs:
                        return ''
                    s1 = min(strs)
                    s2 = max(strs)
                    for i, c in enumerate(s1):
                        if i >= len(s2) or c != s2[i]:
                            return s1[:i]
                    return s1
                lcp = common_prefix(matches)
                if lcp:
                    result = parent / lcp
                else:
                    return partial_path
            add_sep = result.exists() and result.is_dir()
        # Return in the same form as input (relative or absolute), add trailing sep if dir
        if is_relative:
            try:
                out_path = str(result.relative_to(Path.cwd()))
            except ValueError:
                out_path = str(result)
        else:
            out_path = str(result)
        if add_sep and not out_path.endswith(os.sep):
            out_path += os.sep
        return out_path

    @staticmethod
    def is_fs_ref(word: str) -> bool:
        return word.startswith("@")