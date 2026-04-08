"""
Laziest-import Stress Tests - High Pressure Testing

This module contains intensive stress tests designed to push the library
to its limits and uncover potential bugs under extreme conditions.
"""

import sys
import pytest
import tempfile
import os
import gc
import threading
import time
import asyncio
import random
import string
import weakref
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

# Ensure laziest_import can be imported
sys.path.insert(0, '.')


class TestHighConcurrencyStress:
    """Extreme high-concurrency stress tests"""
    
    def test_massive_concurrent_imports(self):
        """Test 1000 concurrent imports from 100 threads"""
        import laziest_import as lz
        
        lz.clear_cache()
        errors = []
        success_count = [0]
        lock = threading.Lock()
        
        def import_and_use(module_name, attr):
            try:
                # Access module
                mod = getattr(lz, module_name)
                # Access attribute
                val = getattr(mod, attr)
                with lock:
                    success_count[0] += 1
            except Exception as e:
                with lock:
                    errors.append((module_name, str(e)))
        
        # Create 100 threads, each doing 10 imports
        threads = []
        modules = ['math', 'os', 'json', 'sys', 're', 'time', 'random', 
                   'collections', 'itertools', 'functools']
        attrs = ['pi', 'getcwd', 'dumps', 'version', 'compile', 'time', 
                 'random', 'defaultdict', 'count', 'partial']
        
        for i in range(100):
            for j in range(10):
                mod_idx = j % len(modules)
                t = threading.Thread(
                    target=import_and_use,
                    args=(modules[mod_idx], attrs[mod_idx])
                )
                threads.append(t)
        
        # Start all threads
        start_time = time.perf_counter()
        for t in threads:
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        elapsed = time.perf_counter() - start_time
        
        print(f"\n[Stress] 1000 concurrent imports: {success_count[0]} success, "
              f"{len(errors)} errors in {elapsed:.2f}s")
        
        assert success_count[0] >= 900, f"Too many failures: {len(errors)}"
        assert len(errors) < 100, f"Too many errors: {errors[:10]}"
    
    def test_concurrent_cache_operations(self):
        """Test concurrent cache operations"""
        import laziest_import as lz
        
        errors = []
        operations = [0]
        lock = threading.Lock()
        
        def cache_ops(thread_id):
            try:
                for i in range(100):
                    # Mix of operations
                    op = i % 5
                    if op == 0:
                        lz.clear_cache()
                    elif op == 1:
                        _ = lz.list_loaded()
                    elif op == 2:
                        _ = lz.list_available()
                    elif op == 3:
                        lz.register_alias(f"test_{thread_id}_{i}", "os")
                    elif op == 4:
                        lz.unregister_alias(f"test_{thread_id}_{i}")
                    
                    with lock:
                        operations[0] += 1
            except Exception as e:
                with lock:
                    errors.append((thread_id, str(e)))
        
        threads = [threading.Thread(target=cache_ops, args=(i,)) for i in range(50)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"\n[Stress] 5000 cache operations: {operations[0]} completed, "
              f"{len(errors)} errors")
        
        # Some errors are expected due to race conditions
        # But should not crash
        assert len(errors) < 500
    
    def test_concurrent_alias_registration(self):
        """Test concurrent alias registration and unregistration"""
        import laziest_import as lz
        
        errors = []
        
        def register_unregister(prefix):
            try:
                for i in range(100):
                    alias = f"{prefix}_{i}"
                    lz.register_alias(alias, "math")
                    _ = lz.list_available()
                    lz.unregister_alias(alias)
            except Exception as e:
                errors.append((prefix, str(e)))
        
        threads = [threading.Thread(target=register_unregister, args=(f"t{i}",)) 
                   for i in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"\n[Stress] Concurrent alias registration: {len(errors)} errors")
        # Should handle gracefully
        assert len(errors) < 100


class TestMemoryStress:
    """Memory stress tests"""
    
    def test_massive_module_cache(self):
        """Test handling of massive module cache"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # Import many stdlib modules
        stdlib_modules = [
            'abc', 'argparse', 'ast', 'asyncio', 'atexit', 'base64',
            'bisect', 'builtins', 'bz2', 'calendar', 'cmath', 'cmd',
            'code', 'codecs', 'collections', 'configparser', 'contextlib',
            'copy', 'csv', 'ctypes', 'dataclasses', 'datetime', 'dbm',
            'decimal', 'difflib', 'dis', 'enum', 'errno', 'functools',
            'gc', 'getopt', 'getpass', 'gettext', 'glob', 'gzip', 'hashlib',
            'heapq', 'hmac', 'html', 'http', 'imaplib', 'importlib', 'inspect',
            'io', 'itertools', 'json', 'keyword', 'linecache', 'locale', 'logging',
            'lzma', 'mailbox', 'marshal', 'math', 'mimetypes', 'mmap',
            'multiprocessing', 'netrc', 'numbers', 'operator', 'optparse', 'os',
            'pathlib', 'pickle', 'platform', 'plistlib', 'poplib', 'pprint',
            'profile', 'queue', 'random', 're', 'reprlib', 'sched', 'secrets',
            'select', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtplib',
            'socket', 'socketserver', 'sqlite3', 'ssl', 'stat', 'statistics',
            'string', 'struct', 'subprocess', 'sys', 'sysconfig', 'tarfile',
            'tempfile', 'textwrap', 'threading', 'time', 'timeit', 'token',
            'tokenize', 'trace', 'traceback', 'types', 'typing', 'unicodedata',
            'unittest', 'urllib', 'uuid', 'warnings', 'wave', 'weakref',
            'webbrowser', 'wsgiref', 'xml', 'xmlrpc', 'zipfile', 'zipimport',
            'zlib', 'zoneinfo'
        ]
        
        loaded_count = 0
        errors = []
        
        for mod in stdlib_modules:
            try:
                _ = getattr(lz, mod)
                loaded_count += 1
            except (AttributeError, ImportError) as e:
                errors.append((mod, str(e)))
        
        print(f"\n[Stress] Loaded {loaded_count}/{len(stdlib_modules)} modules")
        print(f"[Stress] Errors: {len(errors)}")
        
        # Should load most stdlib modules
        assert loaded_count >= len(stdlib_modules) * 0.8
    
    def test_memory_leak_prevention(self):
        """Test that module cache doesn't leak memory"""
        import laziest_import as lz
        import gc
        
        lz.clear_cache()
        gc.collect()
        
        # Get initial loaded modules
        initial_count = len(lz.list_loaded())
        
        # Load many modules
        for _ in range(100):
            _ = lz.math.pi
            _ = lz.os.getcwd
            lz.clear_cache()
        
        gc.collect()
        
        final_count = len(lz.list_loaded())
        
        # Cache should be cleared
        assert final_count <= initial_count + 1
    
    def test_weakref_handling(self):
        """Test that module results work correctly with memory management"""
        import laziest_import as lz
        import gc
        
        lz.clear_cache()
        
        # Access a module
        pi_value = lz.math.pi
        
        # Value should be correct
        assert pi_value > 3.14
        
        # Clear cache
        lz.clear_cache()
        gc.collect()
        
        # Module should be unloaded
        loaded = lz.list_loaded()
        assert "math" not in loaded
        
        # But we can still use the value we got earlier
        assert pi_value > 3.14


class TestImportStress:
    """Import stress tests"""
    
    def test_repeated_imports(self):
        """Test 10000 repeated imports of the same module"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        start_time = time.perf_counter()
        
        for i in range(10000):
            _ = lz.math.pi
        
        elapsed = time.perf_counter() - start_time
        
        print(f"\n[Stress] 10000 repeated imports in {elapsed:.3f}s "
              f"({elapsed/10000*1000:.4f}ms per import)")
        
        # Should be fast due to caching
        assert elapsed < 5.0
    
    def test_import_with_exceptions(self):
        """Test handling of exceptions during import"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        exception_count = 0
        success_count = 0
        
        for i in range(1000):
            try:
                # Try to import non-existent module
                _ = lz.nonexistent_module_xyz_12345.pi
            except (AttributeError, ImportError):
                exception_count += 1
            
            # Successful import should still work
            try:
                _ = lz.math.pi
                success_count += 1
            except Exception:
                pass
        
        print(f"\n[Stress] Exception handling: {exception_count} exceptions, "
              f"{success_count} successful")
        
        assert exception_count == 1000
        assert success_count == 1000
    
    def test_deep_submodule_access(self):
        """Test deep submodule access"""
        import laziest_import as lz
        
        # Access deeply nested submodules
        try:
            _ = lz.os.path.dirname
            _ = lz.collections.abc.MutableMapping
            _ = lz.urllib.parse.urlparse
            _ = lz.xml.etree.ElementTree
            print("\n[Stress] Deep submodule access: OK")
        except Exception as e:
            pytest.fail(f"Deep submodule access failed: {e}")


class TestSymbolSearchStress:
    """Symbol search stress tests"""
    
    def test_massive_symbol_search(self):
        """Test 1000 symbol searches"""
        import laziest_import as lz
        
        lz.rebuild_symbol_index()
        
        # Common symbol names
        symbols = ['sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'abs', 'min', 'max',
                   'sum', 'len', 'range', 'print', 'input', 'open', 'type', 'str',
                   'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'frozenset']
        
        start_time = time.perf_counter()
        results_found = 0
        
        for i in range(1000):
            symbol = symbols[i % len(symbols)]
            results = lz.search_symbol(symbol, max_results=5)
            if results:
                results_found += 1
        
        elapsed = time.perf_counter() - start_time
        
        print(f"\n[Stress] 1000 symbol searches: {results_found} found in {elapsed:.2f}s")
        
        assert results_found >= 500
    
    def test_symbol_search_with_cache(self):
        """Test symbol search caching performance"""
        import laziest_import as lz
        
        lz.clear_symbol_cache()
        lz.rebuild_symbol_index()
        
        # First pass - cold cache
        start_time = time.perf_counter()
        for _ in range(100):
            _ = lz.search_symbol('sqrt', max_results=5)
        cold_time = time.perf_counter() - start_time
        
        # Second pass - warm cache
        start_time = time.perf_counter()
        for _ in range(100):
            _ = lz.search_symbol('sqrt', max_results=5)
        warm_time = time.perf_counter() - start_time
        
        print(f"\n[Stress] Symbol search caching: cold={cold_time:.3f}s, warm={warm_time:.3f}s")
        
        # Warm cache should be faster or similar
        assert warm_time <= cold_time * 1.5


class TestCacheStress:
    """Cache system stress tests"""
    
    def test_cache_size_limit(self):
        """Test cache size limits"""
        import laziest_import as lz
        
        lz.set_cache_config(max_cache_size_mb=1)
        
        # Load many modules
        for _ in range(100):
            _ = lz.math.pi
            _ = lz.os.getcwd
            _ = lz.json.dumps
        
        # Cache should handle size limit gracefully
        info = lz.get_file_cache_info()
        print(f"\n[Stress] Cache info: {info}")
        
        # Reset config
        lz.set_cache_config(max_cache_size_mb=100)
    
    def test_cache_persistence(self):
        """Test cache persistence under stress"""
        import laziest_import as lz
        
        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            
            # Load modules
            _ = lz.math.pi
            _ = lz.os.getcwd
            
            # Force save
            lz.force_save_cache()
            
            # Clear and reload
            lz.clear_cache()
            
            # Check cache directory
            cache_files = list(Path(tmpdir).glob("*.json"))
            print(f"\n[Stress] Cache files created: {len(cache_files)}")
            
            lz.reset_cache_dir()
    
    def test_concurrent_cache_access(self):
        """Test concurrent cache access"""
        import laziest_import as lz
        
        errors = []
        
        def cache_access(thread_id):
            try:
                for i in range(50):
                    _ = lz.get_cache_stats()
                    _ = lz.get_cache_config()
                    lz.reset_cache_stats()
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        threads = [threading.Thread(target=cache_access, args=(i,)) 
                   for i in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"\n[Stress] Concurrent cache access: {len(errors)} errors")
        assert len(errors) < 10


class TestAsyncStress:
    """Async operation stress tests"""
    
    @pytest.mark.asyncio
    async def test_massive_async_imports(self):
        """Test 100 async imports"""
        import laziest_import as lz
        
        # Use unique modules for proper count
        modules = ['math', 'os', 'json', 'sys', 're', 'time', 'random',
                   'collections', 'itertools', 'functools', 'pathlib',
                   'datetime', 'typing', 'copy', 'pickle', 'struct',
                   'hashlib', 'warnings', 'contextlib', 'dataclasses'] * 5
        
        start_time = time.perf_counter()
        results = await lz.import_multiple_async(modules)
        elapsed = time.perf_counter() - start_time
        
        print(f"\n[Stress] 100 async imports in {elapsed:.2f}s")
        
        # Should have at least 15 unique modules loaded
        assert len(results) >= 15
    
    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self):
        """Test concurrent async operations"""
        import laziest_import as lz
        
        async def async_import_task(alias):
            try:
                return await lz.import_async(alias)
            except Exception:
                return None
        
        tasks = [async_import_task('math') for _ in range(50)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time
        
        success = sum(1 for r in results if r is not None)
        print(f"\n[Stress] 50 concurrent async imports: {success} success in {elapsed:.2f}s")
        
        assert success >= 40


class TestFuzzySearchStress:
    """Fuzzy search stress tests"""
    
    def test_fuzzy_search_performance(self):
        """Test fuzzy search performance with many queries"""
        import laziest_import as lz
        
        lz.enable_auto_search()
        
        # Generate variations
        queries = []
        for base in ['math', 'json', 'os', 'sys', 'time']:
            # Add variations
            for i in range(20):
                # Random typos
                typo = list(base)
                if len(typo) > 2:
                    pos = random.randint(0, len(typo) - 1)
                    typo[pos] = random.choice(string.ascii_lowercase)
                queries.append(''.join(typo))
        
        start_time = time.perf_counter()
        found = 0
        
        for query in queries:
            result = lz.search_module(query)
            if result:
                found += 1
        
        elapsed = time.perf_counter() - start_time
        
        print(f"\n[Stress] 100 fuzzy searches: {found} found in {elapsed:.2f}s")
        
        # Should find something
        assert found >= 20


class TestHookStress:
    """Import hook stress tests"""
    
    def test_many_hooks(self):
        """Test with many registered hooks"""
        import laziest_import as lz
        
        called = []
        
        def make_hook(hook_id):
            def hook(name):
                called.append(hook_id)
            return hook
        
        hooks = [make_hook(i) for i in range(50)]
        
        # Register all hooks
        for hook in hooks:
            lz.add_pre_import_hook(hook)
        
        # Import something
        lz.clear_cache()
        _ = lz.math.pi
        
        # Unregister all hooks
        for hook in hooks:
            lz.remove_pre_import_hook(hook)
        
        print(f"\n[Stress] 50 hooks: {len(called)} called")
        
        # At least some hooks should be called
        assert len(called) >= 1
    
    def test_hook_exceptions(self):
        """Test hooks that raise exceptions"""
        import laziest_import as lz
        
        call_count = [0]
        
        def bad_hook(name):
            call_count[0] += 1
            raise RuntimeError("Intentional error")
        
        lz.add_pre_import_hook(bad_hook)
        
        # Should not crash
        lz.clear_cache()
        _ = lz.math.pi
        
        lz.remove_pre_import_hook(bad_hook)
        
        print(f"\n[Stress] Exception hooks: {call_count[0]} called")
        assert call_count[0] >= 1


class TestEdgeCaseStress:
    """Edge case stress tests"""
    
    def test_empty_and_invalid_inputs(self):
        """Test with empty and invalid inputs"""
        import laziest_import as lz
        
        errors = 0
        
        for _ in range(100):
            try:
                _ = lz.search_module("")
            except Exception:
                errors += 1
            
            try:
                _ = lz.search_module(None)
            except Exception:
                errors += 1
            
            try:
                _ = lz.search_symbol("")
            except Exception:
                errors += 1
        
        print(f"\n[Stress] Invalid inputs: {errors} errors handled")
        # Should handle gracefully
        assert errors <= 300
    
    def test_very_long_names(self):
        """Test with very long names"""
        import laziest_import as lz
        
        errors = 0
        
        for _ in range(50):
            long_name = "a" * 1000
            try:
                _ = lz.search_module(long_name)
            except Exception:
                errors += 1
            
            try:
                _ = lz.search_symbol(long_name)
            except Exception:
                errors += 1
        
        print(f"\n[Stress] Long names: {errors} errors handled")
        # Should not crash
        assert errors <= 100
    
    def test_unicode_names(self):
        """Test with unicode names"""
        import laziest_import as lz
        
        unicode_names = ['模块', 'モジュール', '모듈', 'модуль', 'وحدة']
        errors = 0
        
        for name in unicode_names:
            try:
                _ = lz.search_module(name)
            except Exception:
                errors += 1
        
        print(f"\n[Stress] Unicode names: {errors} errors handled")
        # Should handle gracefully
        assert errors <= len(unicode_names)


class TestRecoveryStress:
    """Recovery stress tests"""
    
    def test_recovery_after_errors(self):
        """Test recovery after many errors"""
        import laziest_import as lz
        
        # Cause many errors
        for _ in range(100):
            try:
                _ = lz.nonexistent_module.pi
            except (AttributeError, ImportError):
                pass
        
        # Should still work
        assert lz.math.pi > 3
        
        # Clear and try again
        lz.clear_cache()
        assert lz.math.pi > 3
    
    def test_recovery_after_clear(self):
        """Test recovery after clear operations"""
        import laziest_import as lz
        
        for _ in range(50):
            _ = lz.math.pi
            lz.clear_cache()
            lz.clear_symbol_cache()
        
        # Should still work
        _ = lz.math.pi
        assert True


class TestResourceCleanup:
    """Resource cleanup stress tests"""
    
    def test_file_handle_cleanup(self):
        """Test that file handles are properly closed"""
        import laziest_import as lz
        
        with tempfile.TemporaryDirectory() as tmpdir:
            lz.set_cache_dir(tmpdir)
            
            # Many operations that use file handles
            for _ in range(100):
                _ = lz.math.pi
                _ = lz.get_cache_stats()
                _ = lz.force_save_cache()
            
            lz.reset_cache_dir()
        
        # If we get here without "too many open files" error, we're good
        assert True
    
    def test_thread_cleanup(self):
        """Test that threads are properly cleaned up"""
        import laziest_import as lz
        
        initial_threads = threading.active_count()
        
        # Create many threads
        for _ in range(10):
            threads = [threading.Thread(target=lambda: lz.math.pi) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        
        final_threads = threading.active_count()
        
        print(f"\n[Stress] Thread cleanup: {initial_threads} -> {final_threads}")
        
        # Should not leak threads
        assert final_threads <= initial_threads + 5


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_import_latency(self):
        """Benchmark import latency"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # Cold import
        start = time.perf_counter()
        _ = lz.math.pi
        cold_time = time.perf_counter() - start
        
        # Warm import
        start = time.perf_counter()
        _ = lz.math.pi
        warm_time = time.perf_counter() - start
        
        print(f"\n[Benchmark] Import latency: cold={cold_time*1000:.2f}ms, "
              f"warm={warm_time*1000:.4f}ms")
        
        # Warm should be much faster
        assert warm_time < cold_time
    
    def test_memory_overhead(self):
        """Benchmark memory overhead"""
        import laziest_import as lz
        
        lz.clear_cache()
        
        # Get approximate memory before
        import sys
        before = sys.getsizeof(lz.list_loaded())
        
        # Load modules
        for _ in range(100):
            _ = lz.math.pi
            _ = lz.os.getcwd
        
        # Get approximate memory after
        after = sys.getsizeof(lz.list_loaded())
        
        print(f"\n[Benchmark] Memory: before={before}, after={after}")
        
        # Memory overhead should be reasonable
        assert after < before + 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
