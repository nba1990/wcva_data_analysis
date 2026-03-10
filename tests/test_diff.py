"""Tests for memory diff and history tracking."""

import pytest

from llm_memory import create_empty_memory
from llm_memory.diff import (
    MemoryHistory,
    diff_memories,
    diff_to_patch,
    summarize_diff,
)


# --- Fixtures ---

@pytest.fixture
def base_memory():
    """Create a base memory for testing."""
    mem = create_empty_memory(source="test")
    mem["g"] = ["Goal 1", "Goal 2"]
    mem["ctx"] = ["Context 1"]
    mem["d"] = [["d1", "Decision 1", "on"]]
    mem["f"] = [["key1", "value1"]]
    mem["n"] = "Base notes"
    return mem


@pytest.fixture
def modified_memory(base_memory):
    """Create a modified version of base memory."""
    import copy
    mem = copy.deepcopy(base_memory)
    mem["g"] = ["Goal 1", "Goal 3"]  # Changed Goal 2 -> Goal 3
    mem["ctx"] = ["Context 1", "Context 2"]  # Added Context 2
    mem["d"] = [["d1", "Decision 1", "off"]]  # Changed status
    mem["f"] = [["key1", "value1"], ["key2", "value2"]]  # Added fact
    mem["n"] = "Modified notes"
    return mem


# --- Diff Tests ---

class TestDiffMemories:
    """Tests for diff_memories function."""
    
    def test_no_changes(self, base_memory):
        """Identical memories should have no changes."""
        diff = diff_memories(base_memory, base_memory)
        assert diff["changes"] == []
    
    def test_detects_scalar_change(self, base_memory):
        """Should detect changes to scalar values."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["n"] = "Changed notes"
        
        diff = diff_memories(base_memory, modified)
        assert len(diff["changes"]) == 1
        assert diff["changes"][0]["path"] == "/n"
        assert diff["changes"][0]["op"] == "change"
        assert diff["changes"][0]["old_value"] == "Base notes"
        assert diff["changes"][0]["new_value"] == "Changed notes"
    
    def test_detects_array_addition(self, base_memory):
        """Should detect additions to arrays."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["g"].append("Goal 3")
        
        diff = diff_memories(base_memory, modified)
        assert len(diff["changes"]) == 1
        assert diff["changes"][0]["op"] == "add"
        assert "Goal 3" in str(diff["changes"][0]["new_value"])
    
    def test_detects_array_removal(self, base_memory):
        """Should detect removals from arrays."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["g"].pop()  # Remove last goal
        
        diff = diff_memories(base_memory, modified)
        assert len(diff["changes"]) == 1
        assert diff["changes"][0]["op"] == "remove"
    
    def test_detects_dict_key_addition(self, base_memory):
        """Should detect new keys in dictionaries."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["p"]["new_pref"] = "new_value"
        
        diff = diff_memories(base_memory, modified)
        assert any(c["path"] == "/p/new_pref" for c in diff["changes"])
    
    def test_exclude_meta_by_default(self, base_memory):
        """Should exclude meta changes by default."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["meta"]["source"] = "different-source"
        modified["meta"]["turns"] = 100
        
        diff = diff_memories(base_memory, modified, include_meta=False)
        # Should have no changes since only meta was modified
        assert len(diff["changes"]) == 0
    
    def test_include_meta_when_requested(self, base_memory):
        """Should include meta changes when requested."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["meta"]["source"] = "different-source"
        
        diff = diff_memories(base_memory, modified, include_meta=True)
        assert any("/meta" in c["path"] for c in diff["changes"])
    
    def test_multiple_changes(self, base_memory, modified_memory):
        """Should detect multiple changes."""
        diff = diff_memories(base_memory, modified_memory)
        assert len(diff["changes"]) > 1
    
    def test_diff_has_timestamps(self, base_memory, modified_memory):
        """Diff should include timestamp info."""
        diff = diff_memories(base_memory, modified_memory)
        assert "timestamp" in diff
        assert "source_version" in diff
        assert "target_version" in diff


class TestDiffToPatch:
    """Tests for converting diff to JSON Patch."""
    
    def test_add_operation(self, base_memory):
        """Add changes should become add patches."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["p"]["new_key"] = "new_value"
        
        diff = diff_memories(base_memory, modified)
        patch = diff_to_patch(diff)
        
        add_ops = [p for p in patch if p["op"] == "add"]
        assert len(add_ops) >= 1
    
    def test_change_becomes_replace(self, base_memory):
        """Change operations should become replace patches."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["n"] = "New notes"
        
        diff = diff_memories(base_memory, modified)
        patch = diff_to_patch(diff)
        
        replace_ops = [p for p in patch if p["op"] == "replace"]
        assert len(replace_ops) == 1
        assert replace_ops[0]["path"] == "/n"
    
    def test_empty_diff_empty_patch(self, base_memory):
        """Empty diff should produce empty patch."""
        diff = diff_memories(base_memory, base_memory)
        patch = diff_to_patch(diff)
        assert patch == []


class TestSummarizeDiff:
    """Tests for diff summarization."""
    
    def test_no_changes_summary(self, base_memory):
        """Should report no changes for identical memories."""
        diff = diff_memories(base_memory, base_memory)
        summary = summarize_diff(diff)
        assert "No changes" in summary
    
    def test_summary_includes_counts(self, base_memory, modified_memory):
        """Summary should include change counts."""
        diff = diff_memories(base_memory, modified_memory)
        summary = summarize_diff(diff)
        assert "Total changes:" in summary
    
    def test_summary_groups_by_operation(self, base_memory):
        """Summary should group changes by operation type."""
        import copy
        modified = copy.deepcopy(base_memory)
        modified["n"] = "Changed"  # change
        modified["p"]["new"] = "val"  # add
        
        diff = diff_memories(base_memory, modified)
        summary = summarize_diff(diff)
        # Should mention different operation types
        assert "Changed" in summary or "Added" in summary


# --- History Tests ---

class TestMemoryHistory:
    """Tests for MemoryHistory class."""
    
    def test_add_snapshot(self, base_memory):
        """Should add snapshots to history."""
        history = MemoryHistory()
        history.add_snapshot(base_memory, source="test")
        
        assert len(history._snapshots) == 1
        assert history._snapshots[0]["source"] == "test"
    
    def test_get_latest(self, base_memory, modified_memory):
        """Should return the most recent memory."""
        history = MemoryHistory()
        history.add_snapshot(base_memory, source="first")
        history.add_snapshot(modified_memory, source="second")
        
        latest = history.get_latest()
        assert latest["n"] == modified_memory["n"]
    
    def test_get_snapshot_by_index(self, base_memory, modified_memory):
        """Should retrieve specific snapshot by index."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        first = history.get_snapshot(0)
        assert first["memory"]["n"] == base_memory["n"]
        
        last = history.get_snapshot(-1)
        assert last["memory"]["n"] == modified_memory["n"]
    
    def test_generates_diffs(self, base_memory, modified_memory):
        """Should generate diffs between snapshots."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        assert len(history._diffs) == 1
        assert history._diffs[0]["changes"]  # Should have changes
    
    def test_get_diff(self, base_memory, modified_memory):
        """Should retrieve specific diff."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        diff = history.get_diff(0)
        assert diff is not None
        assert "changes" in diff
    
    def test_rollback(self, base_memory, modified_memory):
        """Should rollback to previous state."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        rolled_back = history.rollback(steps=1)
        assert rolled_back["n"] == base_memory["n"]
    
    def test_rollback_too_far_returns_none(self, base_memory):
        """Should return None if rollback goes too far."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        
        result = history.rollback(steps=10)
        assert result is None
    
    def test_clear(self, base_memory, modified_memory):
        """Should clear all history."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        history.clear()
        assert len(history._snapshots) == 0
        assert len(history._diffs) == 0
    
    def test_max_snapshots(self, base_memory):
        """Should respect max_snapshots limit."""
        history = MemoryHistory(max_snapshots=3)
        
        for i in range(5):
            import copy
            mem = copy.deepcopy(base_memory)
            mem["n"] = f"Snapshot {i}"
            history.add_snapshot(mem)
        
        assert len(history._snapshots) == 3
        # Should keep the most recent
        assert history._snapshots[-1]["memory"]["n"] == "Snapshot 4"
    
    def test_get_change_summary(self, base_memory, modified_memory):
        """Should generate a readable change summary."""
        history = MemoryHistory()
        history.add_snapshot(base_memory, source="initial")
        history.add_snapshot(modified_memory, source="update")
        
        summary = history.get_change_summary()
        assert "Memory History" in summary
        assert "snapshots" in summary
    
    def test_to_dict_and_from_dict(self, base_memory, modified_memory):
        """Should serialize and deserialize correctly."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        data = history.to_dict()
        restored = MemoryHistory.from_dict(data)
        
        assert len(restored._snapshots) == 2
        assert len(restored._diffs) == 1
    
    def test_save_and_load(self, base_memory, modified_memory, tmp_path):
        """Should save to and load from file."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        path = tmp_path / "history.json"
        history.save(str(path))
        
        loaded = MemoryHistory.load(str(path))
        assert len(loaded._snapshots) == 2


class TestGetAllDiffs:
    """Tests for get_all_diffs method."""
    
    def test_returns_all_diffs(self, base_memory, modified_memory):
        """Should return all stored diffs."""
        history = MemoryHistory()
        history.add_snapshot(base_memory)
        history.add_snapshot(modified_memory)
        
        import copy
        third = copy.deepcopy(modified_memory)
        third["n"] = "Third version"
        history.add_snapshot(third)
        
        diffs = history.get_all_diffs()
        assert len(diffs) == 2

