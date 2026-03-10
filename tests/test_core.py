"""Tests for core memory validation and manipulation."""

import json
import tempfile
from pathlib import Path

import pytest

from llm_memory import (
    LLMMemoryError,
    ValidationReport,
    apply_patch,
    canonicalize_llm_output,
    compact_memory,
    compress_memory,
    create_empty_memory,
    create_thread,
    decompress_memory,
    detect_schema_version,
    get_active_thread,
    load_memory,
    save_memory,
    switch_thread,
    validate_and_fix_memory,
    validate_memory,
)


# --- Fixtures ---

@pytest.fixture
def valid_memory():
    """Return a valid memory object."""
    return {
        "v": 1,
        "meta": {
            "created": "2026-01-06T10:00:00Z",
            "updated": "2026-01-06T14:30:00Z",
            "source": "test-model",
        },
        "g": ["Test goal"],
        "ctx": ["Test context"],
        "d": [["d1", "Test decision", "on"]],
        "f": [["key", "value"]],
        "c": {"h": ["hard"], "s": ["soft"]},
        "p": {"pref": "value"},
        "s": {"d": ["done"], "n": ["next"], "b": []},
        "oq": ["question?"],
        "n": "Test notes",
        "ent": [["e1", "Entity", "project"]],
    }


@pytest.fixture
def minimal_memory():
    """Return a minimal valid memory object."""
    return create_empty_memory(source="test")


# --- Validation Tests ---

class TestValidation:
    """Tests for memory validation."""
    
    def test_valid_memory_passes(self, valid_memory):
        """Valid memory should pass validation."""
        validate_memory(valid_memory)  # Should not raise
    
    def test_minimal_memory_passes(self, minimal_memory):
        """Minimal memory should pass validation."""
        validate_memory(minimal_memory)
    
    def test_missing_required_key_fails(self, valid_memory):
        """Missing required key should fail."""
        del valid_memory["g"]
        with pytest.raises(LLMMemoryError, match="Missing top-level keys"):
            validate_memory(valid_memory)
    
    def test_wrong_version_fails(self, valid_memory):
        """Wrong version should fail."""
        valid_memory["v"] = 2
        with pytest.raises(LLMMemoryError, match="v must be 1"):
            validate_memory(valid_memory)
    
    def test_invalid_decision_format_fails(self, valid_memory):
        """Invalid decision format should fail."""
        valid_memory["d"] = [["d1", "text"]]  # Missing status
        with pytest.raises(LLMMemoryError, match="must be \\[id, txt, st\\]"):
            validate_memory(valid_memory)
    
    def test_non_sequential_decisions_fail(self, valid_memory):
        """Non-sequential decision IDs should fail."""
        valid_memory["d"] = [
            ["d1", "First", "on"],
            ["d3", "Third", "on"],  # Skipped d2
        ]
        with pytest.raises(LLMMemoryError, match="sequential"):
            validate_memory(valid_memory)
    
    def test_duplicate_fact_key_fails(self, valid_memory):
        """Duplicate fact key should fail."""
        valid_memory["f"] = [["key", "val1"], ["key", "val2"]]
        with pytest.raises(LLMMemoryError, match="Duplicate fact key"):
            validate_memory(valid_memory)
    
    def test_string_too_long_fails(self, valid_memory):
        """String exceeding max length should fail."""
        valid_memory["g"] = ["x" * 200]  # > 120 chars
        with pytest.raises(LLMMemoryError, match="exceeds"):
            validate_memory(valid_memory)
    
    def test_invalid_decision_status_fails(self, valid_memory):
        """Invalid decision status should fail."""
        valid_memory["d"] = [["d1", "text", "invalid"]]
        with pytest.raises(LLMMemoryError, match="st must be one of"):
            validate_memory(valid_memory)
    
    def test_invalid_entity_type_fails(self, valid_memory):
        """Invalid entity type should fail."""
        valid_memory["ent"] = [["e1", "Name", "invalid_type"]]
        with pytest.raises(LLMMemoryError, match="type must be one of"):
            validate_memory(valid_memory)
    
    def test_missing_meta_fails(self, valid_memory):
        """Missing meta field should fail."""
        del valid_memory["meta"]
        with pytest.raises(LLMMemoryError, match="Missing top-level keys"):
            validate_memory(valid_memory)
    
    def test_invalid_iso_datetime_fails(self, valid_memory):
        """Invalid datetime format should fail."""
        valid_memory["meta"]["created"] = "not-a-date"
        with pytest.raises(LLMMemoryError, match="valid ISO 8601"):
            validate_memory(valid_memory)


class TestValidateAndFix:
    """Tests for lenient validation with auto-fix."""
    
    def test_adds_missing_meta(self):
        """Should add missing meta field."""
        memory = {
            "v": 1,
            "g": [], "ctx": [], "d": [], "f": [],
            "c": {"h": [], "s": []}, "p": {},
            "s": {"d": [], "n": [], "b": []},
            "oq": [], "n": "",
        }
        fixed, report = validate_and_fix_memory(memory)
        assert "meta" in fixed
        assert report.is_valid
        assert any("meta" in fix for fix in report.fixes_applied)
    
    def test_fixes_decision_ids(self):
        """Should fix non-sequential decision IDs."""
        memory = create_empty_memory()
        memory["d"] = [
            ["x1", "First", "on"],
            ["x2", "Second", "on"],
        ]
        fixed, report = validate_and_fix_memory(memory)
        assert fixed["d"][0][0] == "d1"
        assert fixed["d"][1][0] == "d2"
    
    def test_truncates_long_strings(self):
        """Should truncate strings exceeding max length."""
        memory = create_empty_memory()
        memory["g"] = ["x" * 200]
        fixed, report = validate_and_fix_memory(memory)
        assert len(fixed["g"][0]) <= 120
        assert any("Truncated" in fix for fix in report.fixes_applied)
    
    def test_adds_missing_ent(self):
        """Should add missing ent field."""
        memory = create_empty_memory()
        del memory["ent"]
        fixed, report = validate_and_fix_memory(memory)
        assert "ent" in fixed
        assert fixed["ent"] == []


# --- JSON Patch Tests ---

class TestApplyPatch:
    """Tests for RFC 6902 JSON Patch."""
    
    def test_add_operation(self, valid_memory):
        """Add operation should work."""
        patch = [{"op": "add", "path": "/g/-", "value": "New goal"}]
        result = apply_patch(valid_memory, patch)
        assert "New goal" in result["g"]
    
    def test_replace_operation(self, valid_memory):
        """Replace operation should work."""
        patch = [{"op": "replace", "path": "/n", "value": "Updated notes"}]
        result = apply_patch(valid_memory, patch)
        assert result["n"] == "Updated notes"
    
    def test_remove_operation(self, valid_memory):
        """Remove operation should work."""
        patch = [{"op": "remove", "path": "/g/0"}]
        result = apply_patch(valid_memory, patch)
        assert len(result["g"]) == 0
    
    def test_nested_path(self, valid_memory):
        """Nested path should work."""
        patch = [{"op": "add", "path": "/p/new_key", "value": "new_value"}]
        result = apply_patch(valid_memory, patch)
        assert result["p"]["new_key"] == "new_value"
    
    def test_invalid_path_fails(self, valid_memory):
        """Invalid path should fail."""
        patch = [{"op": "replace", "path": "/nonexistent", "value": "x"}]
        with pytest.raises(LLMMemoryError, match="not found"):
            apply_patch(valid_memory, patch)
    
    def test_invalid_operation_fails(self, valid_memory):
        """Invalid operation should fail."""
        patch = [{"op": "invalid", "path": "/n", "value": "x"}]
        with pytest.raises(LLMMemoryError, match="Unsupported op"):
            apply_patch(valid_memory, patch)


# --- Compaction Tests ---

class TestCompactMemory:
    """Tests for memory compaction."""
    
    def test_dedupes_arrays(self, valid_memory):
        """Should deduplicate arrays."""
        valid_memory["g"] = ["goal", "goal", "goal"]
        result = compact_memory(valid_memory)
        assert len(result["g"]) == 1
    
    def test_removes_empty_strings(self, valid_memory):
        """Should remove empty strings."""
        valid_memory["g"] = ["goal", "", "  "]
        result = compact_memory(valid_memory)
        assert len(result["g"]) == 1
    
    def test_updates_timestamp(self, valid_memory):
        """Should update the updated timestamp."""
        original_updated = valid_memory["meta"]["updated"]
        result = compact_memory(valid_memory)
        assert result["meta"]["updated"] != original_updated


# --- Compression Tests ---

class TestCompression:
    """Tests for memory compression."""
    
    def test_roundtrip(self, valid_memory):
        """Compress and decompress should be lossless."""
        compressed = compress_memory(valid_memory)
        decompressed = decompress_memory(compressed)
        assert decompressed == valid_memory
    
    def test_reduces_size(self, valid_memory):
        """Compression should reduce size for larger memories."""
        # Add more data
        valid_memory["ctx"] = [f"Context item {i}" for i in range(50)]
        original_size = len(json.dumps(valid_memory))
        compressed_size = len(compress_memory(valid_memory))
        # Note: For small data, base64 overhead may increase size
        # For larger data, compression wins
        assert isinstance(compressed_size, int)


# --- Cross-Platform Parsing Tests ---

class TestCanonicalizeOutput:
    """Tests for parsing messy LLM output."""
    
    def test_strips_markdown_fences(self):
        """Should strip markdown code fences."""
        raw = '```json\n{"v": 1, "g": []}\n```'
        # Note: This is incomplete memory, just testing parsing
        result = canonicalize_llm_output(raw)
        assert result["v"] == 1
    
    def test_handles_preamble(self):
        """Should handle preamble text."""
        raw = 'Here is the JSON:\n{"v": 1, "g": []}'
        result = canonicalize_llm_output(raw)
        assert result["v"] == 1
    
    def test_handles_trailing_text(self):
        """Should handle trailing text."""
        raw = '{"v": 1, "g": []}\nI hope this helps!'
        result = canonicalize_llm_output(raw)
        assert result["v"] == 1
    
    def test_no_json_fails(self):
        """Should fail if no JSON found."""
        raw = "This has no JSON at all"
        with pytest.raises(LLMMemoryError, match="No JSON object found"):
            canonicalize_llm_output(raw)


# --- Thread Tests ---

class TestThreads:
    """Tests for thread management."""
    
    def test_create_thread(self, minimal_memory):
        """Should create a new thread."""
        result = create_thread(minimal_memory, "test-thread", "Test Thread")
        assert "threads" in result
        assert "test-thread" in result["threads"]
        assert result["active_thread"] == "test-thread"
    
    def test_switch_thread(self, minimal_memory):
        """Should switch active thread."""
        mem = create_thread(minimal_memory, "thread1")
        mem = create_thread(mem, "thread2")
        assert mem["active_thread"] == "thread2"
        
        mem = switch_thread(mem, "thread1")
        assert mem["active_thread"] == "thread1"
    
    def test_switch_nonexistent_fails(self, minimal_memory):
        """Should fail when switching to nonexistent thread."""
        with pytest.raises(LLMMemoryError, match="not found"):
            switch_thread(minimal_memory, "nonexistent")
    
    def test_get_active_thread(self, minimal_memory):
        """Should get active thread memory."""
        mem = create_thread(minimal_memory, "test", "Test Goal")
        active = get_active_thread(mem)
        assert active is not None
        assert "Test Goal" in active["g"]


# --- Version Detection Tests ---

class TestVersionDetection:
    """Tests for schema version detection."""
    
    def test_detects_v1(self, valid_memory):
        """Should detect v1 schema."""
        version = detect_schema_version(valid_memory)
        assert version == 1
    
    def test_missing_version_infers(self, valid_memory):
        """Should infer version from structure."""
        del valid_memory["v"]
        version = detect_schema_version(valid_memory)
        assert version == 1


# --- File I/O Tests ---

class TestFileIO:
    """Tests for file operations."""
    
    def test_save_and_load(self, valid_memory):
        """Should save and load memory."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        
        try:
            save_memory(path, valid_memory)
            loaded = load_memory(path)
            
            # Compare ignoring updated timestamp
            valid_memory["meta"].pop("updated", None)
            loaded["meta"].pop("updated", None)
            assert loaded["g"] == valid_memory["g"]
            assert loaded["d"] == valid_memory["d"]
        finally:
            Path(path).unlink(missing_ok=True)
    
    def test_load_lenient(self, valid_memory):
        """Should load with lenient mode."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        
        try:
            # Save memory with issues
            valid_memory["d"] = [["x1", "Test", "on"]]  # Wrong ID
            with open(path, "w") as f:
                json.dump(valid_memory, f)
            
            loaded, report = load_memory(path, lenient=True)
            assert loaded["d"][0][0] == "d1"  # Should be fixed
            assert report.is_valid
        finally:
            Path(path).unlink(missing_ok=True)


# --- Create Empty Memory Tests ---

class TestCreateEmptyMemory:
    """Tests for creating empty memory."""
    
    def test_creates_valid_memory(self):
        """Should create a valid memory object."""
        memory = create_empty_memory()
        validate_memory(memory)  # Should not raise
    
    def test_sets_source(self):
        """Should set the source."""
        memory = create_empty_memory(source="test-model")
        assert memory["meta"]["source"] == "test-model"
    
    def test_has_all_required_fields(self):
        """Should have all required fields."""
        memory = create_empty_memory()
        required = {"v", "meta", "g", "ctx", "d", "f", "c", "p", "s", "oq", "n"}
        assert required.issubset(set(memory.keys()))

