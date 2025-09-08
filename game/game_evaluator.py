import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CommandEvent:
    """Record of a single command event"""
    timestamp: float
    intended_command: str
    actual_command: str
    character_position: float
    success: bool

@dataclass
class CollisionEvent:
    """Record of a collision event"""
    timestamp: float
    meteor_x: float
    character_x: float
    avoidable: bool  # Could collision have been avoided?

class GameEvaluator:
    """
    Game performance evaluator implementing research metrics
    Calculates Precision, Sensitivity, and Specificity for 3-class classification
    """
    
    def __init__(self):
        # Performance tracking
        self.command_events: List[CommandEvent] = []
        self.collision_events: List[CollisionEvent] = []
        
        # Classification metrics (research formula)
        self.true_positives = defaultdict(int)    # TP
        self.true_negatives = defaultdict(int)    # TN
        self.false_positives = defaultdict(int)   # FP
        self.false_negatives = defaultdict(int)   # FN
        
        # Game scoring
        self.score = 0
        self.meteors_avoided = 0
        self.total_meteors = 0
        
        # Session tracking
        self.session_start_time = time.time()
        self.game_duration = 0.0
        
        print("📊 Game evaluator initialized with research metrics")
    
    def record_command(self, command: str, character_pos: float, intended: Optional[str] = None):
        """
        Record a command execution for evaluation
        
        Args:
            command: Actual command executed ("left", "right", "idle")
            character_pos: Character position when command executed
            intended: Intended command (if different from actual)
        """
        current_time = time.time()
        intended_cmd = intended or command
        success = (intended_cmd == command)
        
        event = CommandEvent(
            timestamp=current_time,
            intended_command=intended_cmd,
            actual_command=command,
            character_position=character_pos,
            success=success
        )
        
        self.command_events.append(event)
        
        # Update classification metrics
        self._update_classification_metrics(intended_cmd, command)
        
        print(f"📊 Command recorded: {intended_cmd} → {command} (Success: {success})")
    
    def record_collision(self, meteor_x: float, character_x: float):
        """
        Record a collision event
        
        Args:
            meteor_x: X position of meteor
            character_x: X position of character
        """
        current_time = time.time()
        
        # Determine if collision was avoidable (within reasonable distance)
        distance = abs(meteor_x - character_x)
        avoidable = distance < 100  # If meteor was close, could have been avoided
        
        event = CollisionEvent(
            timestamp=current_time,
            meteor_x=meteor_x,
            character_x=character_x,
            avoidable=avoidable
        )
        
        self.collision_events.append(event)
        self.total_meteors += 1
        
        # Penalty for collision
        if avoidable:
            self.score = max(0, self.score - 10)
        
        print(f"💥 Collision recorded at x={character_x:.0f} (Avoidable: {avoidable})")
    
    def record_meteor_avoided(self):
        """Record when a meteor is successfully avoided"""
        self.meteors_avoided += 1
        self.total_meteors += 1
        self.score += 5
        
        print(f"✅ Meteor avoided! Score: {self.score}")
    
    def _update_classification_metrics(self, intended: str, actual: str):
        """
        Update TP, TN, FP, FN for 3-class classification
        Based on research formulas for precision, sensitivity, specificity
        """
        classes = ["left", "right", "idle"]
        
        for class_name in classes:
            if intended == class_name and actual == class_name:
                # True Positive: Correctly identified the class
                self.true_positives[class_name] += 1
            elif intended == class_name and actual != class_name:
                # False Negative: Missed the class
                self.false_negatives[class_name] += 1
            elif intended != class_name and actual == class_name:
                # False Positive: Incorrectly identified as this class
                self.false_positives[class_name] += 1
            elif intended != class_name and actual != class_name:
                # True Negative: Correctly rejected the class
                self.true_negatives[class_name] += 1
    
    def calculate_precision(self, class_name: str) -> float:
        """
        Calculate Precision for a specific class
        Formula: Precision = TP / (TP + FP) × 100
        """
        tp = self.true_positives[class_name]
        fp = self.false_positives[class_name]
        
        if tp + fp == 0:
            return 0.0
        
        return (tp / (tp + fp)) * 100
    
    def calculate_sensitivity(self, class_name: str) -> float:
        """
        Calculate Sensitivity (Recall) for a specific class
        Formula: Sensitivity = TP / (TP + FN) × 100
        """
        tp = self.true_positives[class_name]
        fn = self.false_negatives[class_name]
        
        if tp + fn == 0:
            return 0.0
        
        return (tp / (tp + fn)) * 100
    
    def calculate_specificity(self, class_name: str) -> float:
        """
        Calculate Specificity for a specific class
        Formula: Specificity = TN / (TN + FP) × 100
        """
        tn = self.true_negatives[class_name]
        fp = self.false_positives[class_name]
        
        if tn + fp == 0:
            return 0.0
        
        return (tn / (tn + fp)) * 100
    
    def get_metrics(self) -> Optional[Dict[str, float]]:
        """
        Get overall performance metrics averaged across all classes
        Returns dict with precision, sensitivity, specificity
        """
        if not self.command_events:
            return None
        
        classes = ["left", "right", "idle"]
        
        # Calculate averages across classes
        total_precision = sum(self.calculate_precision(cls) for cls in classes)
        total_sensitivity = sum(self.calculate_sensitivity(cls) for cls in classes)
        total_specificity = sum(self.calculate_specificity(cls) for cls in classes)
        
        return {
            "precision": total_precision / len(classes),
            "sensitivity": total_sensitivity / len(classes),
            "specificity": total_specificity / len(classes)
        }
    
    def get_detailed_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get detailed per-class metrics"""
        classes = ["left", "right", "idle"]
        detailed = {}
        
        for cls in classes:
            detailed[cls] = {
                "precision": self.calculate_precision(cls),
                "sensitivity": self.calculate_sensitivity(cls),
                "specificity": self.calculate_specificity(cls),
                "tp": self.true_positives[cls],
                "tn": self.true_negatives[cls],
                "fp": self.false_positives[cls],
                "fn": self.false_negatives[cls]
            }
        
        return detailed
    
    def get_score(self) -> int:
        """Get current game score"""
        return self.score
    
    def get_avoidance_rate(self) -> float:
        """Calculate meteor avoidance rate as percentage"""
        if self.total_meteors == 0:
            return 100.0
        
        return (self.meteors_avoided / self.total_meteors) * 100
    
    def get_session_summary(self) -> Dict[str, any]:
        """Get comprehensive session summary"""
        current_time = time.time()
        self.game_duration = current_time - self.session_start_time
        
        metrics = self.get_metrics()
        detailed = self.get_detailed_metrics()
        
        return {
            "session_info": {
                "duration_seconds": self.game_duration,
                "total_commands": len(self.command_events),
                "total_collisions": len(self.collision_events),
                "score": self.score
            },
            "performance": {
                "avoidance_rate": self.get_avoidance_rate(),
                "command_accuracy": self._calculate_command_accuracy(),
                "average_response_time": self._calculate_response_time()
            },
            "research_metrics": metrics,
            "detailed_metrics": detailed,
            "events": {
                "commands": len(self.command_events),
                "collisions": len(self.collision_events),
                "meteors_total": self.total_meteors,
                "meteors_avoided": self.meteors_avoided
            }
        }
    
    def _calculate_command_accuracy(self) -> float:
        """Calculate overall command execution accuracy"""
        if not self.command_events:
            return 0.0
        
        successful_commands = sum(1 for event in self.command_events if event.success)
        return (successful_commands / len(self.command_events)) * 100
    
    def _calculate_response_time(self) -> float:
        """Calculate average response time (placeholder for future implementation)"""
        # This would require timing between EOG detection and game response
        # For now, return a placeholder value
        return 0.1  # 100ms placeholder
    
    def reset(self):
        """Reset all evaluation metrics"""
        self.command_events.clear()
        self.collision_events.clear()
        
        self.true_positives.clear()
        self.true_negatives.clear()
        self.false_positives.clear()
        self.false_negatives.clear()
        
        self.score = 0
        self.meteors_avoided = 0
        self.total_meteors = 0
        
        self.session_start_time = time.time()
        self.game_duration = 0.0
        
        print("📊 Game evaluator reset")
    
    def export_session_data(self, filename: Optional[str] = None) -> str:
        """
        Export session data to JSON file for analysis
        Returns filename of exported data
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"eog_game_session_{timestamp}.json"
        
        session_data = self.get_session_summary()
        
        # Add raw event data
        session_data["raw_events"] = {
            "commands": [
                {
                    "timestamp": event.timestamp,
                    "intended": event.intended_command,
                    "actual": event.actual_command,
                    "position": event.character_position,
                    "success": event.success
                }
                for event in self.command_events
            ],
            "collisions": [
                {
                    "timestamp": event.timestamp,
                    "meteor_x": event.meteor_x,
                    "character_x": event.character_x,
                    "avoidable": event.avoidable
                }
                for event in self.collision_events
            ]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"📊 Session data exported to {filename}")
            return filename
        except Exception as e:
            print(f"📊 Error exporting session data: {e}")
            return ""
    
    def print_summary(self):
        """Print a summary of current performance"""
        metrics = self.get_metrics()
        
        print("\n" + "="*50)
        print("📊 GAME PERFORMANCE SUMMARY")
        print("="*50)
        print(f"Score: {self.score}")
        print(f"Meteors Avoided: {self.meteors_avoided}/{self.total_meteors}")
        print(f"Avoidance Rate: {self.get_avoidance_rate():.1f}%")
        
        if metrics:
            print(f"\nResearch Metrics:")
            print(f"Precision: {metrics['precision']:.1f}%")
            print(f"Sensitivity: {metrics['sensitivity']:.1f}%") 
            print(f"Specificity: {metrics['specificity']:.1f}%")
        
        print(f"\nCommands Executed: {len(self.command_events)}")
        print(f"Command Accuracy: {self._calculate_command_accuracy():.1f}%")
        print("="*50)
