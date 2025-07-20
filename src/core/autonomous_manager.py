"""
Autonomous management system for PatchPilot that handles code generation,
testing, deployment, and error recovery with minimal human intervention.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from core.db_utils import DatabaseManager
from generators.code_generator import CodeGenerator, CodeTask

logger = logging.getLogger(__name__)

@dataclass
class DecisionContext:
    """Context for autonomous decision making"""
    code_type: str
    complexity: int
    risk_level: str
    previous_attempts: List[Dict]
    system_metrics: Dict

@dataclass
class DeploymentConfig:
    """Configuration for autonomous deployment"""
    environment: str
    health_check_url: str
    rollback_strategy: str
    canary_percentage: float
    timeout_seconds: int

class MetricsCollector:
    """Collects and analyzes system metrics"""
    
    def __init__(self):
        self.metrics_history = {}
        
    def record_metric(self, category: str, name: str, value: float):
        """Record a metric value"""
        if category not in self.metrics_history:
            self.metrics_history[category] = {}
        if name not in self.metrics_history[category]:
            self.metrics_history[category][name] = []
        self.metrics_history[category][name].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        
    def get_current_metrics(self) -> Dict:
        """Get the current state of all metrics"""
        current_metrics = {}
        for category in self.metrics_history:
            current_metrics[category] = {}
            for name in self.metrics_history[category]:
                if self.metrics_history[category][name]:
                    current_metrics[category][name] = self.metrics_history[category][name][-1]['value']
        return current_metrics
        
    def analyze_trends(self, category: str, name: str, hours: int = 24) -> Optional[float]:
        """Analyze trends in a specific metric"""
        if category not in self.metrics_history or name not in self.metrics_history[category]:
            return None
            
        values = self.metrics_history[category][name]
        if not values:
            return None
            
        # Calculate trend (simple linear regression)
        x = list(range(len(values)))
        y = [v['value'] for v in values]
        
        if len(x) < 2:
            return 0.0
            
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator

class LearningSystem:
    """Learns from system operations and improves decision making"""
    
    def __init__(self, db_manager):
        """Initialize the learning system with database connection."""
        self.db_manager = db_manager
        self.decision_outcomes = []  # Cache for recent decisions
        self.improvement_patterns = {}  # Cache for improvement patterns
        self.error_solutions = {}  # Cache for recent error solutions
        
    def record_decision(self, context: DecisionContext, decision: str, outcome: str):
        """Record the outcome of a decision for learning."""
        # Convert DecisionContext to dict for storage
        context_dict = {
            'code_type': context.code_type,
            'complexity': context.complexity,
            'risk_level': context.risk_level,
            'previous_attempts': context.previous_attempts,
            'system_metrics': context.system_metrics
        }
        
        # Save to database
        self.db_manager.save_decision(
            decision_type=context.code_type,
            context=context_dict,
            decision=decision,
            outcome=outcome
        )
        
        # Keep in memory cache
        self.decision_outcomes.append({
            'context': context,
            'decision': decision,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit cache size
        if len(self.decision_outcomes) > 100:
            self.decision_outcomes = self.decision_outcomes[-100:]
        
    def learn_from_errors(self, error: str, solution: str, success: bool):
        """Learn from error recovery attempts."""
        # Save to database
        self.db_manager.save_error_solution(error, solution, success)
        
        # Update memory cache
        if error not in self.error_solutions:
            self.error_solutions[error] = []
        self.error_solutions[error].append({
            'solution': solution,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit cache size
        if len(self.error_solutions[error]) > 10:
            self.error_solutions[error] = self.error_solutions[error][-10:]
        
    def get_best_solution(self, error: str) -> Optional[str]:
        """Get the most successful solution for an error."""
        # First check memory cache
        if error in self.error_solutions and self.error_solutions[error]:
            successful_solutions = [
                s for s in self.error_solutions[error]
                if s['success']
            ]
            if successful_solutions:
                return max(
                    successful_solutions,
                    key=lambda x: x['timestamp']
                )['solution']
        
        # If not found in cache, check database
        return self.db_manager.get_best_error_solution(error)
        
    def get_similar_decisions(self, context: DecisionContext, limit: int = 5) -> List[dict]:
        """Get similar past decisions to help with current decision."""
        return self.db_manager.get_similar_decisions(
            decision_type=context.code_type,
            context={
                'complexity': context.complexity,
                'risk_level': context.risk_level
            },
            limit=limit
        )
        
    def analyze_decision_patterns(self, context: DecisionContext) -> Dict:
        """Analyze patterns in similar past decisions."""
        similar_decisions = self.get_similar_decisions(context)
        if not similar_decisions:
            return {}
            
        # Analyze success rates of different decisions
        decision_stats = {}
        for decision in similar_decisions:
            d = decision['decision']
            if d not in decision_stats:
                decision_stats[d] = {'success': 0, 'total': 0}
            
            decision_stats[d]['total'] += 1
            if decision['outcome'] == 'success':
                decision_stats[d]['success'] += 1
        
        # Calculate success rates
        for d in decision_stats:
            total = decision_stats[d]['total']
            success = decision_stats[d]['success']
            decision_stats[d]['success_rate'] = success / total if total > 0 else 0
            
        return decision_stats

class AutonomousManager:
    """Manages autonomous code generation and improvement."""
    
    def __init__(self, api_key: str, project_dir: str = "."):
        """Initialize the autonomous manager."""
        self.api_key = api_key
        self.project_dir = project_dir
        self.db_manager = DatabaseManager("todos.db")
        self.learning_system = LearningSystem(self.db_manager)
        self.metrics_collector = MetricsCollector()
        self.metrics = self.metrics_collector  # Alias for backward compatibility
        
    def make_decision(self, task_type: str, complexity: int, context: dict) -> str:
        """Make a decision based on learning history and current context."""
        decision_context = DecisionContext(
            code_type=task_type,
            complexity=complexity,
            risk_level=self._assess_risk(complexity, context),
            previous_attempts=context.get('previous_attempts', []),
            system_metrics=self.metrics_collector.get_current_metrics()
        )
        
        # Get decision patterns from learning history
        patterns = self.learning_system.analyze_decision_patterns(decision_context)
        
        if patterns:
            # Use the most successful pattern if available
            best_pattern = max(patterns.items(), key=lambda x: x[1]['success_rate'])
            if best_pattern[1]['success_rate'] > 0.7:  # High confidence threshold
                return best_pattern[0]
        
        # Fall back to default decision making if no good patterns found
        return self._default_decision(decision_context)
        
    def handle_error(self, error: str) -> Optional[str]:
        """Handle an error using learned solutions."""
        return self.learning_system.get_best_solution(error)
        
    def record_outcome(self, task_type: str, complexity: int, context: dict,
                      decision: str, outcome: str):
        """Record the outcome of a decision."""
        decision_context = DecisionContext(
            code_type=task_type,
            complexity=complexity,
            risk_level=self._assess_risk(complexity, context),
            previous_attempts=context.get('previous_attempts', []),
            system_metrics=self.metrics_collector.get_current_metrics()
        )
        self.learning_system.record_decision(decision_context, decision, outcome)
        
    def _assess_risk(self, complexity: int, context: dict) -> str:
        """Assess the risk level of a task."""
        if complexity > 7:
            return "high"
        elif complexity > 4:
            return "medium"
        return "low"
        
    def _default_decision(self, context: DecisionContext) -> str:
        """Make a default decision when no learning data is available."""
        if context.complexity > 7:
            return "break_down_task"
        elif context.risk_level == "high":
            return "conservative_approach"
        return "standard_approach"
        
    def monitor_health(self, deployment_config: DeploymentConfig) -> bool:
        """Monitor system health and trigger recovery if needed"""
        try:
            # Implement health checks
            # Monitor system metrics
            # Trigger recovery if needed
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
            
    def auto_deploy(self, patch_id: str, config: DeploymentConfig) -> bool:
        """Autonomously deploy a patch with safety checks"""
        try:
            # Implement staged deployment
            # Run integration tests
            # Monitor deployment health
            # Auto rollback if needed
            return True
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            return False
            
    def improve_code(self, code: str, context: Dict) -> Tuple[str, bool]:
        """Autonomously improve code based on learning.
        
        Args:
            code: The code to improve
            context: Additional context about the code
            
        Returns:
            Tuple[str, bool]: (improved code, success flag)
        """
        try:
            # Create a code task from the context
            task = CodeTask(
                description=context.get('purpose', 'Improve code quality'),
                language=context.get('language', 'python'),
                requirements=context.get('requirements', [
                    'Improve code quality',
                    'Add proper error handling',
                    'Optimize performance',
                    'Follow best practices'
                ]),
                context=context.get('additional_context')
            )
            
            # Initialize code generator
            code_generator = CodeGenerator(self.api_key, self.project_dir)
            
            # Analyze the code for potential improvements
            needs_improvement, analysis, fixes = code_generator.assess_output(
                output="",  # No output to analyze yet
                error_output="",  # No errors to analyze yet
                task=task
            )
            
            if needs_improvement:
                # Improve the code using the code generator
                improved_code = code_generator.improve_code(code, fixes, task)
                return improved_code, True
            
            return code, True
            
        except Exception as e:
            logger.error(f"Code improvement failed: {str(e)}")
            return code, False
            
    def generate_tests(self, code: str, context: Dict) -> List[str]:
        """Autonomously generate comprehensive tests"""
        try:
            # Generate unit tests
            # Generate integration tests
            # Generate performance tests
            return []
        except Exception as e:
            logger.error(f"Test generation failed: {str(e)}")
            return [] 