"""
Tests for shorthand/abbreviated alias resolution via from laziest_import import *.

Ensures that common short aliases (np, pd, plt, etc.) resolve correctly
as bare names after a wildcard import.
"""

import sys
import pytest


class TestStdlibShorthandAliases:
    """Test short aliases for stdlib modules."""

    def test_os_available_as_bare_name(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        os_mod = namespace["os"]
        assert callable(os_mod.getcwd)
        assert os_mod.__name__ == "os"

    def test_math_available_as_bare_name(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        math = namespace["math"]
        assert math.pi > 3.14
        assert math.sqrt(16) == 4.0

    def test_json_available_as_bare_name(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        json = namespace["json"]
        assert json.dumps({"a": 1}) == '{"a": 1}'

    def test_sys_available_as_bare_name(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "sys" in namespace
        assert namespace["sys"].version == sys.version

    def test_datetime_aliases_dt(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "datetime" in namespace
        dt = namespace["datetime"]
        assert callable(dt.datetime.now)

    def test_tempfile_aliases_temp(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "tempfile" in namespace
        temp = namespace["tempfile"]
        assert callable(temp.NamedTemporaryFile)

    def test_collections_aliases_coll(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "collections" in namespace
        coll = namespace["collections"]
        assert hasattr(coll, "Counter")

    def test_logging_aliases_log(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "logging" in namespace
        log = namespace["logging"]
        assert callable(log.getLogger)

    def test_random_aliases_rand(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "random" in namespace
        rand = namespace["random"]
        assert callable(rand.randint)

    def test_multiprocessing_aliases_mp(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "multiprocessing" in namespace
        mp = namespace["multiprocessing"]
        assert hasattr(mp, "Pool")


class TestCommonThirdPartyShorthand:
    """Test common third-party library short aliases (np, pd, plt, etc.).

    These tests use try/except since the actual libraries may not be
    installed in all environments.
    """

    def test_np_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        np_mod = namespace["np"]
        try:
            result = np_mod.array([1, 2, 3])
            assert result.tolist() == [1, 2, 3]
        except ImportError:
            pytest.skip("numpy not installed")

    def test_pd_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        pd_mod = namespace["pd"]
        try:
            df = pd_mod.DataFrame({"a": [1]})
            assert df is not None
        except ImportError:
            pytest.skip("pandas not installed")

    def test_plt_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        plt_mod = namespace["plt"]
        try:
            import matplotlib

            assert plt_mod.__name__ == "matplotlib.pyplot"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("matplotlib not installed")

    def test_tf_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "tf" in namespace
        try:
            tf = namespace["tf"]
            assert hasattr(tf, "constant")
        except (ImportError, ModuleNotFoundError):
            pytest.skip("tensorflow not installed")

    def test_sns_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        sns_mod = namespace["sns"]
        try:
            import seaborn

            assert sns_mod.__name__ == "seaborn"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("seaborn not installed")

    def test_go_alias_plotly(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "go" in namespace
        try:
            go_mod = namespace["go"]
            import zoneinfo

            assert go_mod.__name__ == "plotly.graph_objects"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("plotly not installed")

    def test_cv_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        cv_mod = namespace["cv"]
        try:
            import cv2

            assert cv_mod.__name__ == "cv2"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("opencv-python not installed")

    def test_sklearn_aliases(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        for alias in (
            "svm",
            "tree",
            "neighbors",
            "preprocessing",
            "model_selection",
            "pipeline",
            "naive_bayes",
            "cluster",
            "decomposition",
            "ensemble",
            "feature_extraction",
            "metrics",
        ):
            assert alias in namespace, f"alias '{alias}' should be in __all__"

    def test_sklearn_submodules(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        try:
            import sklearn

            tree = namespace.get("tree")
            if tree is not None:
                assert hasattr(tree, "DecisionTreeClassifier")
        except ImportError:
            pytest.skip("sklearn not installed")

    def test_mpl_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "mpl" in namespace
        mpl_mod = namespace["mpl"]
        try:
            assert mpl_mod.__name__ == "matplotlib"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("matplotlib not installed")

    def test_st_alias(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "st" in namespace
        try:
            st_mod = namespace["st"]
            assert st_mod.__name__ == "streamlit"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("streamlit not installed")


class TestLazyLoadingViaBareName:
    """Test that bare-name access triggers lazy loading correctly."""

    def test_bare_name_lazy_loading(self):
        from laziest_import import lz

        lz.cache.clear()
        namespace = {}
        exec("from laziest_import import *", namespace)
        loaded = lz.module.list_loaded()
        assert "math" not in loaded
        _ = namespace["math"].pi
        loaded = lz.module.list_loaded()
        assert "math" in loaded

    def test_bare_name_is_lazy_module(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        from laziest_import._proxy import LazyModule

        assert isinstance(namespace["math"], LazyModule)

    def test_bare_name_dir_includes_aliases(self):
        namespace = {}
        exec(
            """
from laziest_import import *
names = dir()
""",
            namespace,
        )
        all_names = namespace["names"]
        assert "np" in all_names
        assert "pd" in all_names
        assert "plt" in all_names


class TestShorthandAliasEdgeCases:
    """Test edge cases for shorthand alias resolution."""

    def test_all_alias_maps_to_submodule(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        alt_mod = namespace["alt"]
        try:
            import altair

            assert alt_mod.__name__ == "altair"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("altair not installed")

    def test_same_alias_as_module_name(self):
        namespace = {}
        exec("from laziest_import import *", namespace)
        assert "numpy" in namespace
        assert "np" in namespace

    def test_list_loaded_via_bare_name(self):
        from laziest_import import lz

        lz.cache.clear()
        namespace = {}
        exec(
            """
from laziest_import import *
_ = math.pi
_ = os.getcwd()
""",
            namespace,
        )
        loaded = lz.module.list_loaded()
        assert "math" in loaded
        assert "os" in loaded

    def test_multiple_bare_names_interop(self):
        pytest.importorskip("numpy")
        namespace = {}
        exec(
            """
from laziest_import import *
raw = np.array([1, 2, 3])
result = json.dumps({'array': [int(x) for x in raw]})
""",
            namespace,
        )
        import json as std_json

        expected = std_json.dumps({"array": [1, 2, 3]})
        assert namespace["result"] == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
