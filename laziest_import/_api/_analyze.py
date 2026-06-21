from typing import Any, Optional


class AnalyzeNamespace:
    def file(self, file_path: str) -> Any:
        from .._analysis._preanalyze import DependencyPreAnalyzer

        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_file(file_path)

    def code(self, source: str, file_path: str = "<string>") -> Any:
        from .._analysis._preanalyze import DependencyPreAnalyzer

        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_source(source, file_path)

    def dir(
        self,
        dir_path: str,
        recursive: bool = True,
        exclude: Optional[set[str]] = None,
    ) -> list[Any]:
        from .._analysis._preanalyze import DependencyPreAnalyzer

        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_directory(dir_path, recursive, exclude)

    def dep_tree(
        self,
        dir_path: str = ".",
        max_depth: int = 3,
    ) -> Any:
        from .._analysis._dependency import dependency_tree

        return dependency_tree(dir_path, max_depth=max_depth)

    def __repr__(self) -> str:
        return "<AnalyzeNamespace>"


class ProfileNamespace:
    def start(self) -> None:
        from .._analysis._profiler import start_profiling

        start_profiling()

    def stop(self) -> None:
        from .._analysis._profiler import stop_profiling

        stop_profiling()

    def report(self, print_report: bool = False) -> Any:
        from .._analysis._profiler import get_profile_report, print_profile_report

        if print_report:
            print_profile_report()
        return get_profile_report()

    def print_report(self) -> None:
        from .._analysis._profiler import print_profile_report

        print_profile_report()

    @property
    def is_active(self) -> bool:
        from .._analysis._profiler import _profiler

        return _profiler.is_active()

    def __repr__(self) -> str:
        return f"<ProfileNamespace: active={self.is_active}>"
