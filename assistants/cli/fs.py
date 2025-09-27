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
        # Expand ~ and environment variables
        expanded = Path(partial_path).expanduser()
        expanded = Path(str(expanded))  # ensure Path after expanduser

        # If the path is a directory and exists, return as-is
        if expanded.exists() and expanded.is_dir():
            return str(expanded)

        parent = expanded.parent
        prefix = expanded.name
        if not parent.exists() or not parent.is_dir():
            return partial_path

        matches = [p.name for p in parent.iterdir() if p.name.startswith(prefix)]
        if not matches:
            return partial_path
        if len(matches) == 1:
            return str(parent / matches[0])
        # Find longest common prefix
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
        return str(parent / lcp) if lcp else partial_path

    @staticmethod
    def is_fs_ref(word: str) -> bool:
        return word.startswith("@")