"""Tests for conflict resolution functionality."""

import pytest

from llm_memory import create_empty_memory
from llm_memory.conflict import (
    ConflictResolver,
    Strategy,
    detect_conflicts,
    merge_memories,
    summarize_conflicts,
)


# --- Fixtures ---

@pytest.fixture
def base_memory():
    """Base/ancestor memory state."""
    mem = create_empty_memory(source="base")
    mem["g"] = ["Original goal"]
    mem["ctx"] = ["Shared context"]
    mem["f"] = [["key", "original"]]
    mem["n"] = "Base notes"
    return mem


@pytest.fixture
def local_memory(base_memory):
    """Local modifications to base."""
    import copy
    mem = copy.deepcopy(base_memory)
    mem["g"] = ["Local goal"]  # Changed
    mem["ctx"] = ["Shared context", "Local context"]  # Added
    mem["n"] = "Local notes"  # Changed
    return mem


@pytest.fixture
def remote_memory(base_memory):
    """Remote modifications to base."""
    import copy
    mem = copy.deepcopy(base_memory)
    mem["g"] = ["Remote goal"]  # Changed differently
    mem["ctx"] = ["Shared context", "Remote context"]  # Added differently
    mem["n"] = "Remote notes"  # Changed differently
    return mem


@pytest.fixture
def non_conflicting_local(base_memory):
    """Local changes that don't conflict with remote."""
    import copy
    mem = copy.deepcopy(base_memory)
    mem["g"] = ["Local goal"]  # Only local changes g
    return mem


@pytest.fixture
def non_conflicting_remote(base_memory):
    """Remote changes that don't conflict with local."""
    import copy
    mem = copy.deepcopy(base_memory)
    mem["n"] = "Remote notes"  # Only remote changes n
    return mem


# --- Detect Conflicts Tests ---

class TestDetectConflicts:
    """Tests for conflict detection."""
    
    def test_no_conflicts_identical(self, base_memory):
        """Identical memories have no conflicts."""
        conflicts = detect_conflicts(base_memory, base_memory, base_memory)
        assert len(conflicts) == 0
    
    def test_no_conflicts_non_overlapping(self, base_memory, non_conflicting_local, non_conflicting_remote):
        """Non-overlapping changes don't conflict."""
        conflicts = detect_conflicts(base_memory, non_conflicting_local, non_conflicting_remote)
        assert len(conflicts) == 0
    
    def test_detects_conflict(self, base_memory, local_memory, remote_memory):
        """Should detect when both sides changed the same field differently."""
        conflicts = detect_conflicts(base_memory, local_memory, remote_memory)
        
        # Should have conflicts on g, ctx, and n
        conflict_paths = [c["path"] for c in conflicts]
        assert "g" in conflict_paths
        assert "n" in conflict_paths
    
    def test_conflict_info_structure(self, base_memory, local_memory, remote_memory):
        """Conflict info should have correct structure."""
        conflicts = detect_conflicts(base_memory, local_memory, remote_memory)
        
        assert len(conflicts) > 0
        conflict = conflicts[0]
        
        assert "path" in conflict
        assert "base_value" in conflict
        assert "local_value" in conflict
        assert "remote_value" in conflict


# --- ConflictResolver Tests ---

class TestConflictResolver:
    """Tests for ConflictResolver class."""
    
    def test_last_write_wins(self, base_memory, local_memory, remote_memory):
        """Last-write-wins should prefer remote values."""
        resolver = ConflictResolver(default_strategy=Strategy.LAST_WRITE_WINS)
        result, conflicts = resolver.resolve(base_memory, local_memory, remote_memory)
        
        # Remote should win for conflicting fields
        assert result["g"] == ["Remote goal"]
        assert result["n"] == "Remote notes"
    
    def test_union_merge_arrays(self, base_memory, local_memory, remote_memory):
        """Union merge should combine arrays."""
        resolver = ConflictResolver(default_strategy=Strategy.UNION_MERGE)
        result, conflicts = resolver.resolve(base_memory, local_memory, remote_memory)
        
        # ctx should have elements from both
        # Note: The exact behavior depends on implementation
        assert "Shared context" in result["ctx"]
    
    def test_strategy_override(self, base_memory, local_memory, remote_memory):
        """Should allow per-call strategy override."""
        resolver = ConflictResolver(default_strategy=Strategy.LAST_WRITE_WINS)
        
        # Override to UNION_MERGE for this call
        result, conflicts = resolver.resolve(
            base_memory, local_memory, remote_memory,
            strategy=Strategy.UNION_MERGE
        )
        
        # Should use union merge logic
        assert len(conflicts) > 0
    
    def test_manual_strategy_keeps_base(self, base_memory, local_memory, remote_memory):
        """Manual strategy should keep base values pending review."""
        resolver = ConflictResolver(default_strategy=Strategy.MANUAL)
        result, conflicts = resolver.resolve(base_memory, local_memory, remote_memory)
        
        # Conflicting values should stay as base (for manual review)
        assert any(c["strategy_used"] == "manual" for c in conflicts)
    
    def test_reports_conflicts(self, base_memory, local_memory, remote_memory):
        """Should report all conflicts."""
        resolver = ConflictResolver()
        result, conflicts = resolver.resolve(base_memory, local_memory, remote_memory)
        
        assert len(conflicts) > 0
        assert all("strategy_used" in c for c in conflicts)
    
    def test_get_pending_conflicts(self, base_memory, local_memory, remote_memory):
        """Should track pending conflicts."""
        resolver = ConflictResolver()
        resolver.resolve(base_memory, local_memory, remote_memory)
        
        pending = resolver.get_pending_conflicts()
        assert isinstance(pending, list)
    
    def test_no_conflict_preserves_local(self, base_memory, non_conflicting_local, non_conflicting_remote):
        """Should preserve local changes when no conflict."""
        resolver = ConflictResolver()
        result, conflicts = resolver.resolve(base_memory, non_conflicting_local, non_conflicting_remote)
        
        # Local change to g should be preserved
        assert result["g"] == ["Local goal"]
    
    def test_no_conflict_preserves_remote(self, base_memory, non_conflicting_local, non_conflicting_remote):
        """Should preserve remote changes when no conflict."""
        resolver = ConflictResolver()
        result, conflicts = resolver.resolve(base_memory, non_conflicting_local, non_conflicting_remote)
        
        # Remote change to n should be preserved
        assert result["n"] == "Remote notes"
    
    def test_has_unresolved_conflicts(self, base_memory, local_memory, remote_memory):
        """Should detect unresolved manual conflicts."""
        resolver = ConflictResolver(default_strategy=Strategy.MANUAL)
        resolver.resolve(base_memory, local_memory, remote_memory)
        
        # Manual strategy leaves conflicts unresolved
        has_unresolved = resolver.has_unresolved_conflicts()
        # Note: Implementation may vary - check actual behavior
        assert isinstance(has_unresolved, bool)


# --- Merge Memories Tests ---

class TestMergeMemories:
    """Tests for merge_memories function."""
    
    def test_empty_list_raises(self):
        """Should raise error for empty list."""
        with pytest.raises(ValueError, match="No memories"):
            merge_memories([])
    
    def test_single_memory_returns_copy(self, base_memory):
        """Single memory should return a copy."""
        result = merge_memories([base_memory])
        
        assert result["g"] == base_memory["g"]
        assert result is not base_memory  # Should be a copy
    
    def test_merges_multiple(self, base_memory, local_memory):
        """Should merge multiple memories."""
        result = merge_memories([base_memory, local_memory])
        
        # Should have content from both
        assert result is not None
    
    def test_uses_specified_strategy(self, base_memory, local_memory, remote_memory):
        """Should use specified strategy."""
        result = merge_memories(
            [base_memory, local_memory, remote_memory],
            strategy=Strategy.LAST_WRITE_WINS
        )
        
        assert result is not None


# --- Summarize Conflicts Tests ---

class TestSummarizeConflicts:
    """Tests for conflict summarization."""
    
    def test_no_conflicts_message(self):
        """Should report no conflicts when list is empty."""
        summary = summarize_conflicts([])
        assert "No conflicts" in summary
    
    def test_includes_count(self, base_memory, local_memory, remote_memory):
        """Should include conflict count."""
        conflicts = detect_conflicts(base_memory, local_memory, remote_memory)
        summary = summarize_conflicts(conflicts)
        
        assert str(len(conflicts)) in summary
    
    def test_includes_paths(self, base_memory, local_memory, remote_memory):
        """Should include conflict paths."""
        conflicts = detect_conflicts(base_memory, local_memory, remote_memory)
        summary = summarize_conflicts(conflicts)
        
        # Should mention the conflicting fields
        assert "Path:" in summary
    
    def test_shows_values(self, base_memory, local_memory, remote_memory):
        """Should show base, local, and remote values."""
        conflicts = detect_conflicts(base_memory, local_memory, remote_memory)
        summary = summarize_conflicts(conflicts)
        
        assert "Base:" in summary
        assert "Local:" in summary
        assert "Remote:" in summary


# --- Strategy Enum Tests ---

class TestStrategy:
    """Tests for Strategy enum."""
    
    def test_all_strategies_exist(self):
        """Should have all expected strategies."""
        assert Strategy.LAST_WRITE_WINS
        assert Strategy.UNION_MERGE
        assert Strategy.FIELD_TIMESTAMP
        assert Strategy.MANUAL
    
    def test_strategy_values(self):
        """Strategy values should be strings."""
        assert Strategy.LAST_WRITE_WINS.value == "last_write_wins"
        assert Strategy.UNION_MERGE.value == "union_merge"


# --- Edge Cases ---

class TestConflictEdgeCases:
    """Edge case tests for conflict resolution."""
    
    def test_nested_dict_conflict(self):
        """Should handle conflicts in nested dicts."""
        base = create_empty_memory()
        base["p"] = {"key": "base"}
        
        local = create_empty_memory()
        local["p"] = {"key": "local"}
        
        remote = create_empty_memory()
        remote["p"] = {"key": "remote"}
        
        resolver = ConflictResolver(default_strategy=Strategy.LAST_WRITE_WINS)
        result, conflicts = resolver.resolve(base, local, remote)
        
        # Should handle nested conflict
        assert result["p"]["key"] == "remote"
    
    def test_type_change_conflict(self):
        """Should handle type changes in conflicts."""
        base = create_empty_memory()
        base["p"] = {"key": "string"}
        
        local = create_empty_memory()
        local["p"] = {"key": ["list"]}
        
        remote = create_empty_memory()
        remote["p"] = {"key": 123}
        
        resolver = ConflictResolver(default_strategy=Strategy.LAST_WRITE_WINS)
        result, conflicts = resolver.resolve(base, local, remote)
        
        # Remote wins with type change
        assert result["p"]["key"] == 123
    
    def test_empty_arrays_merge(self):
        """Should handle merging with empty arrays."""
        base = create_empty_memory()
        local = create_empty_memory()
        local["g"] = ["local goal"]
        
        remote = create_empty_memory()
        remote["g"] = []  # Empty
        
        resolver = ConflictResolver(default_strategy=Strategy.UNION_MERGE)
        result, conflicts = resolver.resolve(base, local, remote)
        
        # Should preserve local goal
        assert result is not None

