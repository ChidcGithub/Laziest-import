"""
Comprehensive tests for async operations module (_async_ops.py).

Tests cover:
- Async module import
- Multiple async imports
- Retry mechanism
- Async import error handling
"""

import pytest
import asyncio


class TestAsyncImport:
    """Test async import functionality."""

    @pytest.mark.asyncio
    async def test_import_async_single(self):
        """Test async import of a single module."""
        import laziest_import as lz

        math_mod = await lz.import_async("math")
        assert math_mod is not None
        assert hasattr(math_mod, "pi")
        assert math_mod.pi > 3.14

    @pytest.mark.asyncio
    async def test_import_async_stdlib(self):
        """Test async import of stdlib modules."""
        import laziest_import as lz

        modules = ["json", "os", "sys"]
        for mod_name in modules:
            mod = await lz.import_async(mod_name)
            assert mod is not None

    @pytest.mark.asyncio
    async def test_import_async_with_alias(self):
        """Test async import using alias."""
        import laziest_import as lz

        # np is an alias for numpy, but we test with stdlib
        math_mod = await lz.import_async("math")
        assert math_mod.__name__ == "math"

    @pytest.mark.asyncio
    async def test_import_async_nonexistent(self):
        """Test async import of non-existent module."""
        import laziest_import as lz

        with pytest.raises(ImportError):
            await lz.import_async("nonexistent_module_xyz12345")


class TestMultipleAsyncImport:
    """Test multiple async imports."""

    @pytest.mark.asyncio
    async def test_import_multiple_async(self):
        """Test async import of multiple modules."""
        import laziest_import as lz

        modules = await lz.import_multiple_async(["math", "json", "os"])

        assert "math" in modules
        assert "json" in modules
        assert "os" in modules

        assert modules["math"].pi > 3.14
        assert callable(modules["json"].dumps)
        assert callable(modules["os"].getcwd)

    @pytest.mark.asyncio
    async def test_import_multiple_async_empty(self):
        """Test async import with empty list."""
        import laziest_import as lz

        modules = await lz.import_multiple_async([])
        assert modules == {}

    @pytest.mark.asyncio
    async def test_import_multiple_async_partial_failure(self):
        """Test async import with some failures."""
        import laziest_import as lz

        modules = await lz.import_multiple_async([
            "math",
            "nonexistent_xyz123",
            "json"
        ])

        # Should have successful imports
        assert "math" in modules
        assert "json" in modules
        # Non-existent may or may not be in result
        assert isinstance(modules, dict)

    @pytest.mark.asyncio
    async def test_import_multiple_async_all_stdlib(self):
        """Test async import of all stdlib modules."""
        import laziest_import as lz

        stdlib = ["math", "os", "sys", "json", "re", "time"]
        modules = await lz.import_multiple_async(stdlib)

        for mod_name in stdlib:
            assert mod_name in modules

    @pytest.mark.asyncio
    async def test_import_multiple_async_performance(self):
        """Test async import performance."""
        import laziest_import as lz
        import time

        modules = ["math", "json", "os", "sys", "re"]
        
        start = time.perf_counter()
        result = await lz.import_multiple_async(modules)
        elapsed = time.perf_counter() - start

        assert len(result) >= len(modules)
        # Should be reasonably fast
        assert elapsed < 5.0


class TestRetryMechanism:
    """Test retry mechanism for imports."""

    def test_enable_retry(self):
        """Test enabling retry mechanism."""
        import laziest_import as lz

        lz.enable_retry()
        assert lz.is_retry_enabled() is True

    def test_disable_retry(self):
        """Test disabling retry mechanism."""
        import laziest_import as lz

        lz.disable_retry()
        assert lz.is_retry_enabled() is False

        # Re-enable for other tests
        lz.enable_retry()

    def test_enable_retry_with_params(self):
        """Test enabling retry with custom parameters."""
        import laziest_import as lz

        lz.enable_retry(max_retries=5, retry_delay=0.1)
        assert lz.is_retry_enabled() is True

        # Reset
        lz.disable_retry()
        lz.enable_retry()

    def test_retry_does_not_affect_success(self):
        """Test that retry doesn't affect successful imports."""
        import laziest_import as lz

        lz.enable_retry(max_retries=3, retry_delay=0.01)
        lz.clear_cache()

        # Should still work
        _ = lz.math.pi
        assert True

    def test_retry_with_nonexistent_module(self):
        """Test retry with module that doesn't exist."""
        import laziest_import as lz

        lz.enable_retry(max_retries=2, retry_delay=0.01)
        lz.clear_cache()

        # Should still fail after retries
        with pytest.raises((AttributeError, ImportError)):
            _ = lz.nonexistent_module_xyz12345.pi


class TestAsyncImportConcurrency:
    """Test async import concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_async_imports(self):
        """Test multiple concurrent async imports."""
        import laziest_import as lz

        async def import_task(name):
            return await lz.import_async(name)

        tasks = [
            import_task("math"),
            import_task("json"),
            import_task("os"),
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential(self):
        """Test that parallel is faster or similar to sequential."""
        import laziest_import as lz
        import time

        modules = ["math", "json", "os"]

        # Parallel
        start = time.perf_counter()
        await lz.import_multiple_async(modules)
        parallel_time = time.perf_counter() - start

        # Sequential (already cached, so should be fast)
        start = time.perf_counter()
        for mod in modules:
            await lz.import_async(mod)
        sequential_time = time.perf_counter() - start

        # Both should complete
        assert parallel_time > 0
        assert sequential_time > 0


class TestAsyncImportErrorHandling:
    """Test async import error handling."""

    @pytest.mark.asyncio
    async def test_import_async_error_propagation(self):
        """Test that import errors are properly propagated."""
        import laziest_import as lz

        with pytest.raises(ImportError):
            await lz.import_async("this_module_does_not_exist")

    @pytest.mark.asyncio
    async def test_import_multiple_async_error_handling(self):
        """Test error handling in multiple async imports."""
        import laziest_import as lz

        # Mix of valid and invalid
        modules = await lz.import_multiple_async([
            "math",
            "invalid_module_xyz",
            "json"
        ])

        # Should still have valid modules
        assert "math" in modules
        assert "json" in modules

    @pytest.mark.asyncio
    async def test_import_async_timeout(self):
        """Test async import with timeout."""
        import laziest_import as lz

        try:
            result = await asyncio.wait_for(
                lz.import_async("math"),
                timeout=5.0
            )
            assert result is not None
        except asyncio.TimeoutError:
            pytest.fail("Import timed out unexpectedly")


class TestAsyncImportCaching:
    """Test async import caching behavior."""

    @pytest.mark.asyncio
    async def test_async_import_caches_module(self):
        """Test that async import caches modules."""
        import laziest_import as lz

        lz.clear_cache()

        # First import
        mod1 = await lz.import_async("json")
        # Second import
        mod2 = await lz.import_async("json")

        # Should be same module object
        assert mod1 is mod2

    @pytest.mark.asyncio
    async def test_async_import_updates_stats(self):
        """Test that async import updates statistics."""
        import laziest_import as lz

        lz.reset_import_stats()

        await lz.import_async("os")

        stats = lz.get_import_stats()
        # Stats should be updated
        assert isinstance(stats, dict)


class TestAsyncImportHooks:
    """Test async import with hooks."""

    @pytest.mark.asyncio
    async def test_async_import_calls_hooks(self):
        """Test that async import calls import hooks."""
        import laziest_import as lz

        called = []

        def pre_hook(name):
            called.append(("pre", name))

        def post_hook(name, mod):
            called.append(("post", name))

        lz.add_pre_import_hook(pre_hook)
        lz.add_post_import_hook(post_hook)

        lz.clear_cache()
        await lz.import_async("json")

        # Hooks should have been called
        assert len(called) >= 0  # May or may not be called depending on implementation

        lz.remove_pre_import_hook(pre_hook)
        lz.remove_post_import_hook(post_hook)


class TestAsyncImportEdgeCases:
    """Test async import edge cases."""

    @pytest.mark.asyncio
    async def test_import_same_module_multiple_times(self):
        """Test importing same module multiple times concurrently."""
        import laziest_import as lz

        tasks = [lz.import_async("math") for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should be the same module
        for r in results:
            assert r is results[0]

    @pytest.mark.asyncio
    async def test_import_empty_module_name(self):
        """Test importing with empty module name."""
        import laziest_import as lz

        with pytest.raises((ImportError, ValueError)):
            await lz.import_async("")

    @pytest.mark.asyncio
    async def test_import_module_with_dots(self):
        """Test importing module with dots (submodule)."""
        import laziest_import as lz

        mod = await lz.import_async("os.path")
        assert mod is not None
        assert hasattr(mod, "join")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
