import pytest
from datetime import datetime
from src.core.autonomous_manager import AutonomousManager, DecisionContext

@pytest.fixture
def autonomous_manager():
    """Create a test autonomous manager."""
    return AutonomousManager("test-api-key", ".")

def test_make_decision_with_no_history(autonomous_manager):
    """Test decision making with no learning history."""
    context = {
        "previous_attempts": [],
        "system_resources": {"cpu": 0.5, "memory": 0.7}
    }
    
    # Test low complexity decision
    decision = autonomous_manager.make_decision("refactor", 3, context)
    assert decision == "standard_approach"
    
    # Test medium complexity decision
    decision = autonomous_manager.make_decision("refactor", 5, context)
    assert decision in ["standard_approach", "conservative_approach"]
    
    # Test high complexity decision
    decision = autonomous_manager.make_decision("refactor", 8, context)
    assert decision == "break_down_task"

def test_decision_learning_and_improvement(autonomous_manager):
    """Test that decisions improve based on learning."""
    context = {
        "previous_attempts": [],
        "system_resources": {"cpu": 0.5, "memory": 0.7}
    }
    
    # Make initial decision
    task_type = "refactor"
    complexity = 5
    
    # Record several successful outcomes for a specific decision
    for _ in range(5):
        decision = autonomous_manager.make_decision(task_type, complexity, context)
        autonomous_manager.record_outcome(
            task_type, complexity, context,
            "successful_pattern", "success"
        )
    
    # The system should now prefer the successful pattern
    decision = autonomous_manager.make_decision(task_type, complexity, context)
    assert decision == "successful_pattern"

def test_error_handling_and_learning(autonomous_manager):
    """Test error handling with learning."""
    error = "RuntimeError: maximum recursion depth exceeded"
    solution = "Implement iterative approach instead of recursive"
    
    # Record a successful solution
    autonomous_manager.learning_system.learn_from_errors(error, solution, True)
    
    # System should suggest the successful solution
    suggested_solution = autonomous_manager.handle_error(error)
    assert suggested_solution == solution

def test_risk_assessment(autonomous_manager):
    """Test risk assessment based on complexity."""
    context = {}
    
    assert autonomous_manager._assess_risk(3, context) == "low"
    assert autonomous_manager._assess_risk(5, context) == "medium"
    assert autonomous_manager._assess_risk(8, context) == "high"

def test_persistence_of_learning(autonomous_manager):
    """Test that learning persists across manager instances."""
    context = {
        "previous_attempts": [],
        "system_resources": {"cpu": 0.5, "memory": 0.7}
    }
    
    # Record decisions in first instance
    task_type = "refactor"
    complexity = 5
    
    autonomous_manager.record_outcome(
        task_type, complexity, context,
        "optimal_pattern", "success"
    )
    
    # Create new instance
    new_manager = AutonomousManager("test-api-key", ".")
    
    # New instance should have access to previous learning
    decision = new_manager.make_decision(task_type, complexity, context)
    assert decision == "optimal_pattern"  # Should use the learned successful pattern 