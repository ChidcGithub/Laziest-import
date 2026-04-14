"""
Comprehensive tests for benchmark functionality.

Tests cover:
- BenchmarkResult dataclass
- BenchmarkReport dataclass
- benchmark() function
- benchmark_imports() function
- print_benchmark_report() function
"""

import pytest
import time
import laziest_import as lz


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_result_creation(self):
        """Test creating a BenchmarkResult."""
        from laziest_import._analysis._benchmark import BenchmarkResult

        result = BenchmarkResult(
            name="test",
            iterations=10,
            total_time=0.1,
            avg_time=0.01,
            min_time=0.008,
            max_time=0.015,
            std_dev=0.002
        )
        assert result.name == "test"
        assert result.iterations == 10
        assert result.avg_time == 0.01


class TestBenchmarkReport:
    """Test BenchmarkReport dataclass."""

    def test_report_creation(self):
        """Test creating a BenchmarkReport."""
        from laziest_import._analysis._benchmark import BenchmarkReport

        report = BenchmarkReport()
        assert report.results == []

    def test_report_with_results(self):
        """Test report with results."""
        from laziest_import._analysis._benchmark import BenchmarkReport, BenchmarkResult

        result = BenchmarkResult(
            name="test", iterations=10, total_time=0.1,
            avg_time=0.01, min_time=0.008, max_time=0.015, std_dev=0.002
        )
        report = BenchmarkReport(results=[result])
        assert len(report.results) == 1

    def test_report_to_dict(self):
        """Test report serialization."""
        from laziest_import._analysis._benchmark import BenchmarkReport, BenchmarkResult

        result = BenchmarkResult(
            name="test", iterations=10, total_time=0.1,
            avg_time=0.01, min_time=0.008, max_time=0.015, std_dev=0.002
        )
        report = BenchmarkReport(results=[result])
        d = report.to_dict()
        assert "results" in d
        assert len(d["results"]) == 1


class TestBenchmarkFunction:
    """Test benchmark() function."""

    def test_basic_benchmark(self):
        """Test basic function benchmarking."""
        def simple_func():
            return sum(range(100))

        result = lz.benchmark(simple_func, iterations=5)
        assert result is not None
        assert result.name == "simple_func"
        assert result.iterations == 5
        assert result.avg_time > 0

    def test_benchmark_with_name(self):
        """Test benchmarking with custom name."""
        def test_func():
            return 42

        result = lz.benchmark(test_func, name="custom_name", iterations=3)
        assert result.name == "custom_name"

    def test_benchmark_iterations(self):
        """Test different iteration counts."""
        def func():
            return 1

        result5 = lz.benchmark(func, iterations=5)
        result10 = lz.benchmark(func, iterations=10)

        assert result5.iterations == 5
        assert result10.iterations == 10

    def test_benchmark_warmup(self):
        """Test benchmark with warmup."""
        def func():
            return sum(range(1000))

        result = lz.benchmark(func, iterations=5, warmup=2)
        assert result is not None
        assert result.avg_time > 0

    def test_benchmark_lambda(self):
        """Test benchmarking lambda function."""
        result = lz.benchmark(lambda: sum(range(100)), name="lambda_test", iterations=5)
        assert result.name == "lambda_test"


class TestBenchmarkImports:
    """Test benchmark_imports() function."""

    def test_benchmark_single_import(self):
        """Test benchmarking single module import."""
        report = lz.benchmark_imports(["json"], iterations=3)
        assert report is not None
        assert len(report.results) >= 1

    def test_benchmark_multiple_imports(self):
        """Test benchmarking multiple module imports."""
        report = lz.benchmark_imports(["json", "os", "math"], iterations=2)
        assert report is not None

    def test_benchmark_imports_with_options(self):
        """Test benchmark_imports with options."""
        report = lz.benchmark_imports(
            ["json"],
            iterations=3,
            compare_lazy=True
        )
        assert report is not None

    def test_benchmark_imports_empty_list(self):
        """Test with empty module list."""
        report = lz.benchmark_imports([], iterations=3)
        assert report is not None


class TestPrintBenchmarkReport:
    """Test print_benchmark_report() function."""

    def test_print_basic_report(self, capsys):
        """Test printing basic report."""
        def func():
            return sum(range(100))

        result = lz.benchmark(func, iterations=5)
        from laziest_import._analysis._benchmark import BenchmarkReport
        report = BenchmarkReport(results=[result])
        lz.print_benchmark_report(report)
        captured = capsys.readouterr()
        assert "Benchmark" in captured.out


class TestBenchmarkRunner:
    """Test BenchmarkRunner class."""

    def test_runner_creation(self):
        """Test creating BenchmarkRunner."""
        from laziest_import._analysis._benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        assert runner is not None

    def test_runner_benchmark_function(self):
        """Test runner benchmark_function method."""
        from laziest_import._analysis._benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        result = runner.benchmark_function(
            "test",
            lambda: sum(range(100)),
            5
        )
        assert result.name == "test"
        assert result.avg_time > 0

    def test_runner_with_options(self):
        """Test runner with options."""
        from laziest_import._analysis._benchmark import BenchmarkRunner

        runner = BenchmarkRunner(
            warmup_iterations=2,
            default_iterations=5,
            use_gc=False
        )
        result = runner.benchmark_function("test", lambda: 1, 3)
        assert result is not None


class TestBenchmarkEdgeCases:
    """Test edge cases for benchmarking."""

    def test_benchmark_fast_function(self):
        """Test benchmarking very fast function."""
        def instant():
            return 1

        result = lz.benchmark(instant, iterations=10)
        assert result.avg_time >= 0  # May be very small

    def test_benchmark_slow_function(self):
        """Test benchmarking slow function."""
        def slow():
            time.sleep(0.01)
            return True

        result = lz.benchmark(slow, iterations=2, warmup=1)
        assert result.avg_time >= 0.01  # At least sleep time

    def test_benchmark_function_with_args(self):
        """Test function with arguments."""
        def add(a, b):
            return a + b

        # Wrap in lambda for benchmarking
        result = lz.benchmark(lambda: add(1, 2), name="add", iterations=5)
        assert result is not None

    def test_benchmark_single_iteration(self):
        """Test with single iteration."""
        def func():
            return 42

        result = lz.benchmark(func, iterations=1)
        assert result.iterations == 1


class TestBenchmarkStatistics:
    """Test benchmark statistical calculations."""

    def test_result_statistics(self):
        """Test that result has all statistics."""
        def func():
            return sum(range(1000))

        result = lz.benchmark(func, iterations=10)
        assert hasattr(result, "avg_time")
        assert hasattr(result, "min_time")
        assert hasattr(result, "max_time")
        assert hasattr(result, "std_dev")
        assert hasattr(result, "total_time")

    def test_min_less_than_max(self):
        """Test min_time <= avg_time <= max_time."""
        def func():
            return sum(range(100))

        result = lz.benchmark(func, iterations=10)
        assert result.min_time <= result.avg_time <= result.max_time

    def test_std_dev_non_negative(self):
        """Test std_dev is non-negative."""
        def func():
            return sum(range(100))

        result = lz.benchmark(func, iterations=10)
        assert result.std_dev >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])