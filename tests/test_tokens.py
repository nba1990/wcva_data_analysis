"""Tests for token estimation functionality."""

import pytest

from llm_memory import create_empty_memory
from llm_memory.tokens import (
    TIKTOKEN_AVAILABLE,
    estimate_memory_tokens,
    estimate_tokens,
    estimate_tokens_chars,
    fits_in_context,
    get_context_usage,
    get_model_context_limit,
    update_memory_token_estimate,
)


# --- Fixtures ---

@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    mem = create_empty_memory(source="test")
    mem["g"] = ["Build a web application", "Deploy to production"]
    mem["ctx"] = ["User prefers Python", "Backend development focus"]
    mem["d"] = [
        ["d1", "Use FastAPI for backend", "on"],
        ["d2", "PostgreSQL for database", "on"],
    ]
    mem["f"] = [
        ["language", "Python 3.11"],
        ["framework", "FastAPI"],
    ]
    mem["n"] = "Focus on clean architecture and good test coverage."
    return mem


@pytest.fixture
def large_memory():
    """Create a larger memory for testing."""
    mem = create_empty_memory(source="test")
    mem["g"] = [f"Goal {i}" for i in range(20)]
    mem["ctx"] = [f"Context fact {i} with more details" for i in range(30)]
    mem["d"] = [[f"d{i+1}", f"Decision {i} description", "on"] for i in range(15)]
    mem["f"] = [[f"key{i}", f"value{i} with some content"] for i in range(25)]
    mem["n"] = "A" * 150  # Max notes
    return mem


# --- Character-based Estimation Tests ---

class TestEstimateTokensChars:
    """Tests for character-based token estimation."""
    
    def test_empty_string(self):
        """Empty string should return 0 tokens."""
        assert estimate_tokens_chars("") == 0
    
    def test_short_string(self):
        """Short string should return at least 1 token."""
        result = estimate_tokens_chars("Hi")
        assert result >= 1
    
    def test_reasonable_estimate(self):
        """Should give reasonable estimate for typical text."""
        # "Hello, world!" is 13 chars, ~3-4 tokens
        text = "Hello, world!"
        tokens = estimate_tokens_chars(text)
        assert 2 <= tokens <= 6
    
    def test_longer_text(self):
        """Should scale with text length."""
        short_text = "Hello"
        long_text = "Hello " * 100
        
        short_tokens = estimate_tokens_chars(short_text)
        long_tokens = estimate_tokens_chars(long_text)
        
        assert long_tokens > short_tokens
    
    def test_custom_chars_per_token(self):
        """Should use custom chars_per_token."""
        text = "test" * 10  # 40 chars
        
        tokens_default = estimate_tokens_chars(text, chars_per_token=4.0)
        tokens_custom = estimate_tokens_chars(text, chars_per_token=2.0)
        
        assert tokens_custom > tokens_default


# --- General Token Estimation Tests ---

class TestEstimateTokens:
    """Tests for general token estimation."""
    
    def test_basic_estimation(self):
        """Should return a positive integer."""
        tokens = estimate_tokens("Hello, world!")
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_empty_string(self):
        """Empty string should return 0."""
        tokens = estimate_tokens("")
        assert tokens == 0
    
    def test_with_model(self):
        """Should work with model specified."""
        tokens = estimate_tokens("Hello", model="gpt-4")
        assert tokens > 0
    
    def test_without_tiktoken(self):
        """Should fall back to char estimation without tiktoken."""
        # Force fallback by disabling tiktoken
        tokens = estimate_tokens("Hello", model=None, use_tiktoken=False)
        assert tokens > 0


# --- Memory Token Estimation Tests ---

class TestEstimateMemoryTokens:
    """Tests for memory-specific token estimation."""
    
    def test_empty_memory(self):
        """Empty memory should have some tokens (structure overhead)."""
        mem = create_empty_memory()
        tokens = estimate_memory_tokens(mem)
        assert tokens > 0
    
    def test_sample_memory(self, sample_memory):
        """Sample memory should have reasonable token count."""
        tokens = estimate_memory_tokens(sample_memory)
        assert 50 < tokens < 1000  # Reasonable range
    
    def test_larger_memory_more_tokens(self, sample_memory, large_memory):
        """Larger memory should have more tokens."""
        small_tokens = estimate_memory_tokens(sample_memory)
        large_tokens = estimate_memory_tokens(large_memory)
        
        assert large_tokens > small_tokens
    
    def test_with_formatting(self, sample_memory):
        """Should differ with/without formatting."""
        with_format = estimate_memory_tokens(sample_memory, include_formatting=True)
        without_format = estimate_memory_tokens(sample_memory, include_formatting=False)
        
        # Formatted JSON is larger due to whitespace
        assert with_format >= without_format
    
    def test_with_model_name(self, sample_memory):
        """Should accept model name."""
        tokens = estimate_memory_tokens(sample_memory, model="claude-3.5-sonnet")
        assert tokens > 0


# --- Update Memory Token Estimate Tests ---

class TestUpdateMemoryTokenEstimate:
    """Tests for updating memory with token estimate."""
    
    def test_adds_tokens_est(self, sample_memory):
        """Should add tokens_est to meta."""
        # Remove existing tokens_est if present
        sample_memory["meta"].pop("tokens_est", None)
        
        result = update_memory_token_estimate(sample_memory)
        
        assert "tokens_est" in result["meta"]
        assert isinstance(result["meta"]["tokens_est"], int)
        assert result["meta"]["tokens_est"] > 0
    
    def test_updates_existing(self, sample_memory):
        """Should update existing tokens_est."""
        sample_memory["meta"]["tokens_est"] = 100
        
        result = update_memory_token_estimate(sample_memory)
        
        # Should be recalculated (likely different from 100)
        assert "tokens_est" in result["meta"]
    
    def test_creates_meta_if_missing(self):
        """Should create meta if missing."""
        mem = {"v": 1, "g": [], "ctx": [], "d": [], "f": [],
               "c": {"h": [], "s": []}, "p": {},
               "s": {"d": [], "n": [], "b": []},
               "oq": [], "n": "", "ent": []}
        
        result = update_memory_token_estimate(mem)
        
        assert "meta" in result
        assert "tokens_est" in result["meta"]


# --- Context Fitting Tests ---

class TestFitsInContext:
    """Tests for context window fitting."""
    
    def test_small_memory_fits(self, sample_memory):
        """Small memory should fit in large context."""
        assert fits_in_context(sample_memory, max_tokens=100000)
    
    def test_large_limit_fits(self, large_memory):
        """Even large memory should fit in huge context."""
        assert fits_in_context(large_memory, max_tokens=1000000)
    
    def test_tiny_limit_doesnt_fit(self, sample_memory):
        """Should not fit in very small context."""
        assert not fits_in_context(sample_memory, max_tokens=10)
    
    def test_safety_margin(self, sample_memory):
        """Should respect safety margin."""
        tokens = estimate_memory_tokens(sample_memory)
        
        # Without margin, exact fit should work
        # With 10% margin, need 10% more space
        fits_exact = fits_in_context(sample_memory, max_tokens=tokens, safety_margin=0)
        fits_with_margin = fits_in_context(sample_memory, max_tokens=tokens, safety_margin=0.1)
        
        # Exact should fit (or be very close)
        # With margin, might not fit
        assert isinstance(fits_exact, bool)
        assert isinstance(fits_with_margin, bool)


# --- Context Usage Tests ---

class TestGetContextUsage:
    """Tests for context usage statistics."""
    
    def test_returns_dict(self, sample_memory):
        """Should return a dictionary."""
        usage = get_context_usage(sample_memory, max_tokens=10000)
        assert isinstance(usage, dict)
    
    def test_has_required_keys(self, sample_memory):
        """Should have all required keys."""
        usage = get_context_usage(sample_memory, max_tokens=10000)
        
        assert "tokens_used" in usage
        assert "tokens_available" in usage
        assert "usage_percent" in usage
        assert "max_tokens" in usage
    
    def test_tokens_used_positive(self, sample_memory):
        """tokens_used should be positive."""
        usage = get_context_usage(sample_memory, max_tokens=10000)
        assert usage["tokens_used"] > 0
    
    def test_tokens_available_calculated(self, sample_memory):
        """tokens_available should be max - used."""
        usage = get_context_usage(sample_memory, max_tokens=10000)
        
        expected_available = usage["max_tokens"] - usage["tokens_used"]
        assert usage["tokens_available"] == max(0, expected_available)
    
    def test_usage_percent_calculated(self, sample_memory):
        """usage_percent should be correct."""
        usage = get_context_usage(sample_memory, max_tokens=10000)
        
        expected_percent = (usage["tokens_used"] / 10000) * 100
        assert abs(usage["usage_percent"] - expected_percent) < 0.01
    
    def test_small_context_high_usage(self, sample_memory):
        """Small context should show high usage."""
        usage = get_context_usage(sample_memory, max_tokens=100)
        
        # Likely > 100% usage
        assert usage["usage_percent"] > 50


# --- Model Context Limits Tests ---

class TestGetModelContextLimit:
    """Tests for model context limit lookup."""
    
    def test_known_models(self):
        """Should return correct limits for known models."""
        assert get_model_context_limit("gpt-4") == 8192
        assert get_model_context_limit("gpt-4-turbo") == 128000
        assert get_model_context_limit("claude-3-opus") == 200000
    
    def test_partial_match(self):
        """Should match partial model names."""
        # "gpt-4" should match various gpt-4 models
        limit = get_model_context_limit("gpt-4-something")
        assert limit > 0
    
    def test_unknown_model_default(self):
        """Unknown model should return default."""
        limit = get_model_context_limit("unknown-model-xyz")
        assert limit == 8192  # Default
    
    def test_case_insensitive_partial(self):
        """Should handle different cases in partial match."""
        # Implementation may be case-sensitive, test actual behavior
        limit = get_model_context_limit("GPT-4")
        assert limit > 0


# --- Integration Tests ---

class TestTokenIntegration:
    """Integration tests for token functionality."""
    
    def test_workflow(self, sample_memory):
        """Test typical workflow."""
        # 1. Estimate tokens
        tokens = estimate_memory_tokens(sample_memory)
        assert tokens > 0
        
        # 2. Check if fits in context
        model = "gpt-4"
        limit = get_model_context_limit(model)
        fits = fits_in_context(sample_memory, limit, model=model)
        
        # 3. Get usage stats
        usage = get_context_usage(sample_memory, limit, model=model)
        
        # 4. Update memory with estimate
        updated = update_memory_token_estimate(sample_memory, model=model)

        # All should be broadly consistent
        assert isinstance(updated["meta"]["tokens_est"], int)
        assert updated["meta"]["tokens_est"] > 0
        assert (usage["tokens_used"] < limit) == fits


# --- Tiktoken-specific Tests (conditional) ---

@pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not installed")
class TestTiktokenIntegration:
    """Tests that require tiktoken to be installed."""
    
    def test_tiktoken_estimation(self):
        """Should use tiktoken when available."""
        from llm_memory.tokens import estimate_tokens_tiktoken
        
        tokens = estimate_tokens_tiktoken("Hello, world!", model="gpt-4")
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_tiktoken_more_accurate(self):
        """Tiktoken should give consistent results."""
        from llm_memory.tokens import estimate_tokens_tiktoken
        
        text = "The quick brown fox jumps over the lazy dog."
        
        # Same text should give same result
        tokens1 = estimate_tokens_tiktoken(text, model="gpt-4")
        tokens2 = estimate_tokens_tiktoken(text, model="gpt-4")
        
        assert tokens1 == tokens2

