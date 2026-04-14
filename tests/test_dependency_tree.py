"""
Comprehensive tests for dependency_tree functionality.

Tests cover:
- DependencyNode dataclass
- DependencyTree dataclass
- dependency_tree() function
- print_dependency_tree() function
"""

import pytest
import laziest_import as lz


class TestDependencyNode:
    """Test DependencyNode dataclass."""

    def test_node_creation(self):
        """Test creating a DependencyNode."""
        from laziest_import._analysis._dependency import DependencyNode

        node = DependencyNode(module_name="test_module")
        assert node.module_name == "test_module"
        assert node.children == []
        assert node.is_stdlib is False
        assert node.is_third_party is False

    def test_node_with_children(self):
        """Test node with children."""
        from laziest_import._analysis._dependency import DependencyNode

        child = DependencyNode(module_name="child_module")
        parent = DependencyNode(module_name="parent_module", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].module_name == "child_module"

    def test_node_flags(self):
        """Test node flags."""
        from laziest_import._analysis._dependency import DependencyNode

        node = DependencyNode(
            module_name="numpy",
            is_stdlib=False,
            is_third_party=True,
            version="1.24.0"
        )
        assert node.is_stdlib is False
        assert node.is_third_party is True
        assert node.version == "1.24.0"

    def test_node_to_dict(self):
        """Test node serialization."""
        from laziest_import._analysis._dependency import DependencyNode

        node = DependencyNode(module_name="test", is_stdlib=True)
        d = node.to_dict()
        assert d["module_name"] == "test"
        assert d["is_stdlib"] is True


class TestDependencyTree:
    """Test DependencyTree dataclass."""

    def test_tree_creation(self):
        """Test creating a DependencyTree."""
        from laziest_import._analysis._dependency import DependencyTree, DependencyNode

        root = DependencyNode(module_name="root")
        tree = DependencyTree(root_module="root", tree=root)
        assert tree.root_module == "root"
        assert tree.tree.module_name == "root"

    def test_tree_to_dict(self):
        """Test tree serialization to dict."""
        from laziest_import._analysis._dependency import DependencyTree, DependencyNode

        child = DependencyNode(module_name="child")
        root = DependencyNode(module_name="root", children=[child])
        tree = DependencyTree(root_module="root", tree=root, total_modules=2)
        
        d = tree.to_dict()
        assert isinstance(d, dict)
        assert d["root_module"] == "root"

    def test_tree_stats(self):
        """Test tree statistics."""
        from laziest_import._analysis._dependency import DependencyTree

        tree = DependencyTree(
            root_module="test",
            total_modules=10,
            stdlib_count=5,
            third_party_count=3,
            local_count=2
        )
        assert tree.total_modules == 10
        assert tree.stdlib_count == 5
        assert tree.third_party_count == 3


class TestDependencyTreeFunction:
    """Test dependency_tree() function."""

    def test_basic_dependency_tree(self):
        """Test basic dependency tree analysis."""
        tree = lz.dependency_tree("json", max_depth=1)
        assert tree is not None
        assert tree.root_module == "json"

    def test_dependency_tree_max_depth(self):
        """Test max_depth parameter."""
        tree1 = lz.dependency_tree("json", max_depth=1)
        tree2 = lz.dependency_tree("json", max_depth=2)
        
        # Both should work
        assert tree1.root_module == "json"
        assert tree2.root_module == "json"

    def test_dependency_tree_stdlib(self):
        """Test analyzing stdlib module."""
        tree = lz.dependency_tree("os", max_depth=2, include_stdlib=True)
        assert tree.root_module == "os"
        if tree.tree:
            assert tree.tree.is_stdlib is True

    def test_dependency_tree_exclude_stdlib(self):
        """Test excluding stdlib modules."""
        tree = lz.dependency_tree("json", max_depth=2, include_stdlib=False)
        # Should still return a tree, just without stdlib children
        assert tree is not None

    def test_dependency_tree_invalid_module(self):
        """Test with non-existent module."""
        tree = lz.dependency_tree("nonexistent_module_xyz", max_depth=1)
        # Should return tree with unavailable module
        assert tree.root_module == "nonexistent_module_xyz"

    def test_dependency_tree_include_options(self):
        """Test include options."""
        # Test with different combinations
        tree = lz.dependency_tree(
            "json",
            max_depth=1,
            include_stdlib=True,
            include_third_party=True,
            include_local=True
        )
        assert tree is not None


class TestPrintDependencyTree:
    """Test print_dependency_tree() function."""

    def test_print_basic_tree(self, capsys):
        """Test printing a basic tree."""
        tree = lz.dependency_tree("json", max_depth=1)
        lz.print_dependency_tree(tree)
        captured = capsys.readouterr()
        assert "json" in captured.out

    def test_print_tree_with_depth(self, capsys):
        """Test printing tree with depth."""
        tree = lz.dependency_tree("os", max_depth=2)
        lz.print_dependency_tree(tree)
        captured = capsys.readouterr()
        assert "os" in captured.out


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_analyzer_creation(self):
        """Test creating DependencyAnalyzer."""
        from laziest_import._analysis._dependency import DependencyAnalyzer

        analyzer = DependencyAnalyzer()
        assert analyzer is not None

    def test_analyzer_analyze(self):
        """Test analyzer analyze method."""
        from laziest_import._analysis._dependency import DependencyAnalyzer

        analyzer = DependencyAnalyzer()
        tree = analyzer.analyze("json")
        assert tree.root_module == "json"

    def test_analyzer_with_options(self):
        """Test analyzer with options."""
        from laziest_import._analysis._dependency import DependencyAnalyzer

        analyzer = DependencyAnalyzer(
            max_depth=2,
            include_stdlib=False,
            include_third_party=True
        )
        tree = analyzer.analyze("json")
        assert tree is not None


class TestDependencyTreeEdgeCases:
    """Test edge cases for dependency tree."""

    def test_zero_max_depth(self):
        """Test with max_depth=0."""
        tree = lz.dependency_tree("json", max_depth=0)
        # Should return tree with just root
        assert tree.total_modules >= 1

    def test_large_max_depth(self):
        """Test with large max_depth."""
        tree = lz.dependency_tree("json", max_depth=10)
        assert tree is not None

    def test_circular_dependency_handling(self):
        """Test handling of circular dependencies."""
        # Most stdlib modules don't have circular deps, but test the handling
        tree = lz.dependency_tree("collections", max_depth=3)
        assert tree is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])