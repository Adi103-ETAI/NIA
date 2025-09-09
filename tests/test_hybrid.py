import asyncio
import time
import pytest

from core.autonomy_agent import AutonomyAgent, AutonomousSuggestion
from core.stt_manager import STTManager
from core.confirmation_manager import ConfirmationManager, BatchedSuggestion
from core.memory_manager import MemoryManager


@pytest.mark.asyncio
async def test_autonomy_queueing(monkeypatch):
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    agent.enabled = True
    agent.interval_seconds = 1
    agent.confidence_threshold = 0.1  # Very low threshold for testing
    agent.start()
    agent.resume()
    
    # Provide some user input to trigger context-aware suggestions
    agent.update_user_input("I need help with this work project")
    
    try:
        # Wait up to 5s for a suggestion (allow thread startup jitter)
        for _ in range(50):
            s = await agent.get_next_suggestion_async(timeout_s=0.2)
            if s:
                assert s.text and isinstance(s.text, str)
                assert s.confidence > 0
                assert s.trigger_type
                return
            await asyncio.sleep(0.1)
        assert False, "No autonomous suggestion produced in time"
    finally:
        agent.stop()


def test_wake_word_contains_helper():
    # Create instance without calling __init__ to avoid loading models
    mgr = STTManager.__new__(STTManager)
    mgr.wake_words = ["nia", "hey nia", "okay nia"]
    assert mgr._contains_wake_word("hello nia")
    assert mgr._contains_wake_word("Hey NIA, what's up?")
    assert not mgr._contains_wake_word("hello world")


@pytest.mark.asyncio
async def test_autonomy_pause_blocks_suggestions():
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    agent.enabled = True
    agent.interval_seconds = 1
    agent.confidence_threshold = 0.1  # Very low threshold for testing
    agent.start()
    # leave paused (default)
    try:
        # Ensure no suggestions arrive during pause (wait 3s)
        t0 = time.time()
        while time.time() - t0 < 3.0:
            s = await agent.get_next_suggestion_async(timeout_s=0.2)
            assert s is None
        # Resume and provide input to trigger suggestions
        agent.resume()
        agent.update_user_input("I need help with this work project")
        for _ in range(50):
            s = await agent.get_next_suggestion_async(timeout_s=0.2)
            if s:
                assert s.text
                return
            await asyncio.sleep(0.1)
        assert False, "No suggestion after resume()"
    finally:
        agent.stop()


@pytest.mark.asyncio
async def test_context_aware_suggestions():
    """Test that autonomy agent generates context-aware suggestions."""
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    agent.enabled = True
    agent.confidence_threshold = 0.3  # Lower threshold for testing
    agent.start()
    agent.resume()
    
    try:
        # Test decision keyword detection
        agent.update_user_input("I'm not sure what I should do about this project")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is not None
        assert suggestion.confidence > 0.3
        assert suggestion.trigger_type == "decision_keyword"
        assert "help" in suggestion.text.lower() or "work" in suggestion.text.lower()
        
        # Test high-value topic detection
        agent.update_user_input("I have a meeting tomorrow about the deadline")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is not None
        assert suggestion.confidence > 0.3
        assert suggestion.trigger_type == "high_value_topic"
        assert "deadline" in suggestion.text.lower()  # "deadline" is the detected topic
        
        # Test hesitation detection
        agent.update_user_input("Well, um, I mean, uh, you know, it's like...")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is not None
        assert suggestion.confidence > 0.3
        assert suggestion.trigger_type == "hesitation"
        
    finally:
        agent.stop()


def test_batched_suggestion_creation():
    """Test that ConfirmationManager properly batches suggestions."""
    # Mock TTS and STT managers
    class MockTTS:
        async def speak_async(self, text): pass
    
    class MockSTT:
        async def listen_and_transcribe(self): return "yes"
    
    loop = asyncio.get_event_loop()
    tts = MockTTS()
    stt = MockSTT()
    manager = ConfirmationManager(tts, stt, loop)
    
    # Create test suggestions
    suggestions = [
        AutonomousSuggestion("First suggestion", 0.8, "decision_keyword", "work", time.time()),
        AutonomousSuggestion("Second suggestion", 0.6, "high_value_topic", "project", time.time()),
        AutonomousSuggestion("Third suggestion", 0.4, "hesitation", None, time.time())
    ]
    
    manager._pending_suggestions = suggestions
    batched = manager._create_batched_suggestion()
    
    assert batched is not None
    assert len(batched.suggestions) == 3
    assert batched.highest_confidence == 0.8
    assert batched.primary_trigger == "decision_keyword"
    assert "first suggestion" in batched.combined_text.lower()
    assert "second suggestion" in batched.combined_text.lower()
    assert "third suggestion" in batched.combined_text.lower()


def test_confidence_scoring():
    """Test that confidence scoring works correctly."""
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    agent.confidence_threshold = 0.5
    
    # Test high confidence decision keyword
    agent.update_user_input("I'm not sure what I should do about this work project")
    confidence, trigger, topic = agent._analyze_context()
    assert confidence > 0.5
    assert trigger == "decision_keyword"
    assert topic == "project"  # "project" is detected as high-value topic
    
    # Test low confidence input
    agent.update_user_input("hello there")
    confidence, trigger, topic = agent._analyze_context()
    assert confidence < 0.5
    assert trigger == "periodic"


@pytest.mark.asyncio
async def test_decision_point_detection():
    """Test that suggestions are only generated for decision points, not periodic ones."""
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    agent.enabled = True
    agent.confidence_threshold = 0.3
    agent.start()
    agent.resume()
    
    try:
        # Test decision point detection - should generate suggestion
        agent.update_user_input("I'm not sure what I should do about this project")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is not None
        assert suggestion.trigger_type == "decision_keyword"
        assert suggestion.confidence > 0.3
        
        # Test high-value topic detection - should generate suggestion
        agent.update_user_input("I have a meeting tomorrow about the deadline")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is not None
        assert suggestion.trigger_type == "high_value_topic"
        assert suggestion.confidence > 0.3
        
        # Test hesitation detection - should generate suggestion
        agent.update_user_input("Well, um, I mean, uh, you know...")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is not None
        assert suggestion.trigger_type == "hesitation"
        assert suggestion.confidence > 0.3
        
        # Test non-decision input - should NOT generate suggestion
        agent.update_user_input("Hello there, how are you?")
        suggestion = agent._generate_context_aware_suggestion()
        assert suggestion is None  # Should be None for non-decision input
        
    finally:
        agent.stop()


@pytest.mark.asyncio
async def test_confirmation_flow():
    """Test the confirmation flow with yes/no responses."""
    # Mock TTS and STT managers
    class MockTTS:
        async def speak_async(self, text): 
            pass
    
    class MockSTT:
        def __init__(self, response):
            self.response = response
        async def listen_and_transcribe(self): 
            return self.response
    
    loop = asyncio.get_event_loop()
    tts = MockTTS()
    
    # Test yes response
    stt_yes = MockSTT("yes")
    manager_yes = ConfirmationManager(tts, stt_yes, loop)
    
    suggestion = AutonomousSuggestion("Test suggestion", 0.8, "decision_keyword", "work", time.time())
    manager_yes._pending_suggestions = [suggestion]
    batched = manager_yes._create_batched_suggestion()
    
    confirmed = await manager_yes._present_confirmation(batched)
    assert confirmed is True
    
    # Test no response
    stt_no = MockSTT("no")
    manager_no = ConfirmationManager(tts, stt_no, loop)
    
    confirmed = await manager_no._present_confirmation(batched)
    assert confirmed is False
    
    # Test timeout
    class MockSTTTimeout:
        async def listen_and_transcribe(self):
            await asyncio.sleep(5)  # Longer than timeout
            return "yes"
    
    stt_timeout = MockSTTTimeout()
    manager_timeout = ConfirmationManager(tts, stt_timeout, loop)


@pytest.mark.asyncio
async def test_brain_used_for_speaking_with_memory_context(monkeypatch):
    """Ensure ConfirmationManager uses Brain with memory context if provided."""
    class MockTTS:
        def __init__(self):
            self.spoken = []
        async def speak_async(self, text):
            self.spoken.append(text)

    class MockSTT:
        async def listen_and_transcribe(self):
            return "yes"

    class MockBrain:
        async def generate_stream(self, prompt, context_snippets=None):
            # Yield a single chunk synthesizing context size into the response
            ctx_count = len(context_snippets or [])
            yield {"response": f"Here are {ctx_count} context-backed ideas.", "done": False}
            yield {"response": "", "done": True}

    loop = asyncio.get_event_loop()
    tts = MockTTS()
    stt = MockSTT()
    brain = MockBrain()
    manager = ConfirmationManager(tts, stt, loop, brain)

    # Build batched suggestion with memory context metadata
    s1 = AutonomousSuggestion("S1", 0.8, "decision_keyword", "work", time.time(), metadata={"memory_context": ["[t] user: a", "[t] nia: b"]})
    s2 = AutonomousSuggestion("S2", 0.6, "high_value_topic", "project", time.time(), metadata={"memory_context": ["[t] user: c"]})
    batched = BatchedSuggestion([s1, s2], "combined", 0.8, "decision_keyword")

    await manager._speak_suggestions(batched)
    assert any("context-backed" in x for x in tts.spoken)


@pytest.mark.asyncio
async def test_idle_detection():
    """Test that confirmation only happens when user is idle."""
    class MockTTS:
        async def speak_async(self, text): pass
    
    class MockSTT:
        async def listen_and_transcribe(self): return "yes"
    
    loop = asyncio.get_event_loop()
    tts = MockTTS()
    stt = MockSTT()
    manager = ConfirmationManager(tts, stt, loop)
    
    # Simulate recent activity
    manager.update_activity()
    assert not manager.is_idle()
    
    # Wait for idle period
    await asyncio.sleep(3.1)  # Slightly longer than idle detection time
    assert manager.is_idle()


@pytest.mark.asyncio
async def test_suggestion_batching():
    """Test that multiple suggestions are properly batched."""
    class MockTTS:
        async def speak_async(self, text): pass
    
    class MockSTT:
        async def listen_and_transcribe(self): return "yes"
    
    loop = asyncio.get_event_loop()
    tts = MockTTS()
    stt = MockSTT()
    manager = ConfirmationManager(tts, stt, loop)
    
    # Add multiple suggestions
    suggestions = [
        AutonomousSuggestion("First suggestion", 0.8, "decision_keyword", "work", time.time()),
        AutonomousSuggestion("Second suggestion", 0.6, "high_value_topic", "project", time.time()),
        AutonomousSuggestion("Third suggestion", 0.4, "hesitation", None, time.time())
    ]
    
    for suggestion in suggestions:
        await manager.add_suggestion(suggestion)
    
    # Wait for batching to complete
    await asyncio.sleep(2.1)
    
    # Check that suggestions were batched
    assert len(manager._pending_suggestions) == 0  # Should be cleared after batching


@pytest.mark.asyncio
async def test_barge_in_clears_confirmations():
    """Test that barge-in clears pending confirmations."""
    class MockTTS:
        async def speak_async(self, text): pass
    
    class MockSTT:
        async def listen_and_transcribe(self): return "yes"
    
    loop = asyncio.get_event_loop()
    tts = MockTTS()
    stt = MockSTT()
    manager = ConfirmationManager(tts, stt, loop)
    
    # Add a suggestion
    suggestion = AutonomousSuggestion("Test suggestion", 0.8, "decision_keyword", "work", time.time())
    manager._pending_suggestions = [suggestion]
    manager._batching_task = asyncio.create_task(asyncio.sleep(10))  # Long running task
    
    # Simulate barge-in
    manager.clear_pending()
    
    # Check that pending suggestions are cleared
    assert len(manager._pending_suggestions) == 0
    assert manager._batching_task is None or manager._batching_task.cancelled()


def test_decision_keywords_configuration():
    """Test that decision keywords are properly configured and detected."""
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    
    # Test various decision keywords
    test_inputs = [
        "should i do this",
        "what if i try that",
        "maybe i should",
        "i think i need to",
        "i'm not sure about this",
        "help me decide",
        "what do you think",
        "any suggestions",
        "what would you do"
    ]
    
    for input_text in test_inputs:
        agent.update_user_input(input_text)
        confidence, trigger, topic = agent._analyze_context()
        assert trigger == "decision_keyword"
        assert confidence > 0.3


def test_high_value_topics_detection():
    """Test that high-value topics are properly detected."""
    loop = asyncio.get_event_loop()
    agent = AutonomyAgent(loop)
    
    # Test various high-value topics (avoiding decision keywords and multiple topics)
    test_cases = [
        ("Work is important", "work"),
        ("This project is important", "project"),
        ("The meeting is tomorrow", "meeting"),
        ("Plan this carefully", "plan"),
        ("Schedule this event", "schedule"),
        ("Fix this problem", "problem"),
        ("Choice is available", "choice"),
        ("This is an option", "option")
    ]
    
    for input_text, expected_topic in test_cases:
        agent.update_user_input(input_text)
        confidence, trigger, topic = agent._analyze_context()
        assert trigger == "high_value_topic"
        assert topic == expected_topic
        assert confidence > 0.3


