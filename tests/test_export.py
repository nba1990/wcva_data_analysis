"""Tests for memory export functionality."""

import pytest

from llm_memory import create_empty_memory
from llm_memory.export import (
    export_to_html,
    export_to_markdown,
    export_to_text,
)


# --- Fixtures ---

@pytest.fixture
def full_memory():
    """Create a fully populated memory for testing."""
    return {
        "v": 1,
        "meta": {
            "created": "2026-01-06T10:00:00Z",
            "updated": "2026-01-06T14:30:00Z",
            "source": "test-model",
            "turns": 42,
            "tokens_est": 500,
        },
        "g": ["Goal 1", "Goal 2"],
        "ctx": ["Context fact 1", "Context fact 2"],
        "d": [
            ["d1", "First decision", "on"],
            ["d2", "Second decision", "off"],
        ],
        "f": [
            ["key1", "value1"],
            ["key2", "value2"],
        ],
        "c": {
            "h": ["Hard constraint 1", "Hard constraint 2"],
            "s": ["Soft preference 1"],
        },
        "p": {"style": ["concise"]},
        "s": {
            "d": ["Done task 1"],
            "n": ["Next task 1", "Next task 2"],
            "b": ["Blocked task"],
        },
        "oq": ["Open question 1?"],
        "n": "Test notes here.",
        "ent": [
            ["e1", "Test Project", "project", {"status": "active"}],
            ["e2", "Test Person", "person"],
        ],
    }


@pytest.fixture
def memory_with_threads(full_memory):
    """Create memory with threads."""
    import copy
    mem = copy.deepcopy(full_memory)
    mem["threads"] = {
        "main": create_empty_memory(source="test"),
        "code": create_empty_memory(source="test"),
    }
    mem["threads"]["main"]["g"] = ["Main thread goal"]
    mem["threads"]["code"]["g"] = ["Code review"]
    mem["active_thread"] = "main"
    return mem


# --- Markdown Export Tests ---

class TestExportToMarkdown:
    """Tests for Markdown export."""
    
    def test_includes_title(self, full_memory):
        """Should include main title."""
        md = export_to_markdown(full_memory)
        assert "# LLM Memory State" in md
    
    def test_includes_metadata(self, full_memory):
        """Should include metadata section."""
        md = export_to_markdown(full_memory, include_meta=True)
        assert "## Metadata" in md
        assert "test-model" in md
        assert "42" in md  # turns
    
    def test_excludes_metadata_when_disabled(self, full_memory):
        """Should exclude metadata when requested."""
        md = export_to_markdown(full_memory, include_meta=False)
        assert "## Metadata" not in md
    
    def test_includes_goals(self, full_memory):
        """Should include goals section."""
        md = export_to_markdown(full_memory)
        assert "## Goals" in md
        assert "Goal 1" in md
        assert "Goal 2" in md
    
    def test_includes_context(self, full_memory):
        """Should include context section."""
        md = export_to_markdown(full_memory)
        assert "## Context" in md
        assert "Context fact 1" in md
    
    def test_includes_decisions_table(self, full_memory):
        """Should include decisions as a table."""
        md = export_to_markdown(full_memory)
        assert "## Decisions" in md
        assert "| ID |" in md
        assert "d1" in md
        assert "First decision" in md
        assert "✅" in md  # on status
        assert "❌" in md  # off status
    
    def test_includes_facts_table(self, full_memory):
        """Should include facts as a table."""
        md = export_to_markdown(full_memory)
        assert "## Facts" in md
        assert "| Key |" in md
        assert "key1" in md
        assert "value1" in md
    
    def test_includes_constraints(self, full_memory):
        """Should include constraints section."""
        md = export_to_markdown(full_memory)
        assert "## Constraints" in md
        assert "Hard Constraints" in md
        assert "Soft Constraints" in md
        assert "🔒" in md  # hard constraint icon
        assert "💡" in md  # soft constraint icon
    
    def test_includes_state(self, full_memory):
        """Should include state section."""
        md = export_to_markdown(full_memory)
        assert "## Current State" in md
        assert "### Done" in md
        assert "### Next" in md
        assert "### Blocked" in md
        assert "✅" in md  # done icon
        assert "⏳" in md  # next icon
        assert "🚫" in md  # blocked icon
    
    def test_includes_open_questions(self, full_memory):
        """Should include open questions."""
        md = export_to_markdown(full_memory)
        assert "## Open Questions" in md
        assert "❓" in md
        assert "Open question 1?" in md
    
    def test_includes_notes(self, full_memory):
        """Should include notes section."""
        md = export_to_markdown(full_memory)
        assert "## Notes" in md
        assert "Test notes here." in md
    
    def test_includes_entities(self, full_memory):
        """Should include entities table."""
        md = export_to_markdown(full_memory)
        assert "## Entities" in md
        assert "Test Project" in md
        assert "project" in md
    
    def test_includes_threads(self, memory_with_threads):
        """Should include threads section."""
        md = export_to_markdown(memory_with_threads)
        assert "## Threads" in md
        assert "main" in md
        assert "code" in md
        assert "🔵" in md  # active thread marker
    
    def test_includes_json_when_requested(self, full_memory):
        """Should include raw JSON when requested."""
        md = export_to_markdown(full_memory, include_json=True)
        assert "## Raw JSON" in md
        assert "```json" in md
    
    def test_empty_sections_omitted(self):
        """Should omit empty sections."""
        minimal = create_empty_memory()
        md = export_to_markdown(minimal)
        assert "## Goals" not in md  # Empty goals
        assert "## Open Questions" not in md  # Empty oq


# --- HTML Export Tests ---

class TestExportToHtml:
    """Tests for HTML export."""
    
    def test_valid_html_structure(self, full_memory):
        """Should produce valid HTML structure."""
        html = export_to_html(full_memory)
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html
    
    def test_includes_title(self, full_memory):
        """Should include title."""
        html = export_to_html(full_memory)
        assert "<title>LLM Memory State</title>" in html
        assert "<h1>" in html
    
    def test_includes_styles(self, full_memory):
        """Should include CSS styles by default."""
        html = export_to_html(full_memory, include_styles=True)
        assert "<style>" in html
        assert "font-family" in html
    
    def test_excludes_styles_when_disabled(self, full_memory):
        """Should exclude styles when requested."""
        html = export_to_html(full_memory, include_styles=False)
        assert "<style>" not in html
    
    def test_dark_mode(self, full_memory):
        """Should use dark colors in dark mode."""
        html = export_to_html(full_memory, dark_mode=True)
        assert "#1e1e1e" in html  # dark background
    
    def test_light_mode(self, full_memory):
        """Should use light colors in light mode."""
        html = export_to_html(full_memory, dark_mode=False)
        assert "#ffffff" in html  # light background
    
    def test_includes_metadata_box(self, full_memory):
        """Should include metadata in styled box."""
        html = export_to_html(full_memory)
        assert "meta-box" in html
        assert "test-model" in html
    
    def test_includes_goals(self, full_memory):
        """Should include goals section."""
        html = export_to_html(full_memory)
        assert "Goals" in html
        assert "Goal 1" in html
    
    def test_includes_decisions_table(self, full_memory):
        """Should include decisions as HTML table."""
        html = export_to_html(full_memory)
        assert "<table>" in html
        assert "d1" in html
        assert "status-on" in html
        assert "status-off" in html
    
    def test_escapes_html_characters(self):
        """Should escape HTML characters in content."""
        mem = create_empty_memory()
        mem["g"] = ["Goal with <script>alert('xss')</script>"]
        
        html = export_to_html(mem)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
    
    def test_includes_entities(self, full_memory):
        """Should include entities table."""
        html = export_to_html(full_memory)
        assert "Entities" in html
        assert "Test Project" in html
    
    def test_includes_threads(self, memory_with_threads):
        """Should include threads section."""
        html = export_to_html(memory_with_threads)
        assert "Threads" in html
        assert "thread-active" in html


# --- Plain Text Export Tests ---

class TestExportToText:
    """Tests for plain text export."""
    
    def test_includes_header(self, full_memory):
        """Should include header."""
        text = export_to_text(full_memory)
        assert "LLM MEMORY STATE" in text
        assert "=" in text  # separator
    
    def test_includes_source(self, full_memory):
        """Should include source info."""
        text = export_to_text(full_memory)
        assert "Source: test-model" in text
    
    def test_includes_goals(self, full_memory):
        """Should include goals."""
        text = export_to_text(full_memory)
        assert "GOALS:" in text
        assert "Goal 1" in text
    
    def test_includes_context(self, full_memory):
        """Should include context."""
        text = export_to_text(full_memory)
        assert "CONTEXT:" in text
        assert "Context fact 1" in text
    
    def test_includes_decisions(self, full_memory):
        """Should include decisions with status."""
        text = export_to_text(full_memory)
        assert "DECISIONS:" in text
        assert "[ON]" in text
        assert "[OFF]" in text
    
    def test_includes_facts(self, full_memory):
        """Should include facts."""
        text = export_to_text(full_memory)
        assert "FACTS:" in text
        assert "key1: value1" in text
    
    def test_includes_notes(self, full_memory):
        """Should include notes."""
        text = export_to_text(full_memory)
        assert "NOTES:" in text
        assert "Test notes here." in text
    
    def test_omits_empty_sections(self):
        """Should omit empty sections."""
        minimal = create_empty_memory()
        text = export_to_text(minimal)
        assert "GOALS:" not in text  # Empty


# --- Edge Cases ---

class TestExportEdgeCases:
    """Tests for edge cases in exports."""
    
    def test_empty_memory(self):
        """Should handle empty memory gracefully."""
        empty = create_empty_memory()
        
        md = export_to_markdown(empty)
        assert "# LLM Memory State" in md
        
        html = export_to_html(empty)
        assert "<!DOCTYPE html>" in html
        
        text = export_to_text(empty)
        assert "LLM MEMORY STATE" in text
    
    def test_very_long_strings(self):
        """Should handle long strings."""
        mem = create_empty_memory()
        mem["g"] = ["A" * 500]  # Very long goal
        
        md = export_to_markdown(mem)
        assert "A" * 100 in md  # Should contain the string
    
    def test_unicode_content(self):
        """Should handle Unicode content."""
        mem = create_empty_memory()
        mem["g"] = ["日本語のゴール", "🎯 Emoji goal"]
        mem["n"] = "Notes with émojis 🚀"
        
        md = export_to_markdown(mem)
        assert "日本語のゴール" in md
        assert "🎯" in md
        
        html = export_to_html(mem)
        assert "日本語のゴール" in html
    
    def test_special_characters_in_notes(self):
        """Should handle special characters."""
        mem = create_empty_memory()
        mem["n"] = "Notes with | pipe and * asterisk"
        
        md = export_to_markdown(mem)
        assert "pipe" in md

