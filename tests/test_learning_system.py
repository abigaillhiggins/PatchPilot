import pytest
from datetime import datetime
from src.core.autonomous_manager import LearningSystem, DecisionContext
from src.core.db_utils import DatabaseManager

@pytest.fixture
def db_manager():
    """Create a test database manager."""
    db_manager = DatabaseManager(":memory:")  # Use in-memory SQLite for testing
    return db_manager

@pytest.fixture
def learning_system(db_manager):
    """Create a test learning system."""
    return LearningSystem(db_manager)

@pytest.fixture
def sample_context():
    """Create a sample decision context."""
    return DecisionContext(
        code_type="refactor",
        complexity=3,
        risk_level="medium",
        previous_attempts=[],
        system_metrics={"cpu": 0.5, "memory": 0.7}
    )

def test_record_and_retrieve_decision(learning_system, sample_context):
    """Test recording and retrieving decisions."""
    # Record a decision
    learning_system.record_decision(
        context=sample_context,
        decision="apply_pattern_x",
        outcome="success"
    )
    
    # Get similar decisions
    similar = learning_system.get_similar_decisions(sample_context)
    assert len(similar) == 1
    assert similar[0]['decision'] == "apply_pattern_x"
    assert similar[0]['outcome'] == "success"

def test_learn_from_errors(learning_system):
    """Test error learning and solution retrieval."""
    error = "IndexError: list index out of range"
    solution = "Add bounds check before accessing list"
    
    # Record successful solution
    learning_system.learn_from_errors(error, solution, True)
    
    # Get best solution
    best_solution = learning_system.get_best_solution(error)
    assert best_solution == solution

def test_analyze_decision_patterns(learning_system, sample_context):
    """Test decision pattern analysis."""
    # Record multiple decisions
    decisions = [
        ("apply_pattern_x", "success"),
        ("apply_pattern_x", "success"),
        ("apply_pattern_y", "failure"),
        ("apply_pattern_x", "success"),
    ]
    
    for decision, outcome in decisions:
        learning_system.record_decision(sample_context, decision, outcome)
    
    # Analyze patterns
    patterns = learning_system.analyze_decision_patterns(sample_context)
    
    assert "apply_pattern_x" in patterns
    assert patterns["apply_pattern_x"]["success_rate"] == 1.0  # 3/3 success
    assert patterns["apply_pattern_y"]["success_rate"] == 0.0  # 0/1 success

def test_persistence_across_instances(db_manager, sample_context):
    """Test that learning persists across system instances."""
    # First instance
    system1 = LearningSystem(db_manager)
    system1.record_decision(sample_context, "decision_a", "success")
    
    # Second instance
    system2 = LearningSystem(db_manager)
    decisions = system2.get_similar_decisions(sample_context)
    
    assert len(decisions) == 1
    assert decisions[0]['decision'] == "decision_a" 