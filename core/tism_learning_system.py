#!/usr/bin/env python3
"""
TISM Learning System
Continuously improves the TISM Tree logic through experience
"""

import json
import sqlite3
import pickle
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import re

class TISMLearningSystem:
    """System that learns from every prediction to improve TISM logic"""
    
    def __init__(self, db_path='tism_learning.db'):
        self.db_path = db_path
        self._init_database()
        self.pattern_success_rates = defaultdict(lambda: {'correct': 0, 'total': 0})
        self.keyword_associations = defaultdict(Counter)
        self.load_learning_data()
    
    def _init_database(self):
        """Initialize learning database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT,
            question_type TEXT,
            format TEXT,
            predicted TEXT,
            correct TEXT,
            was_correct BOOLEAN,
            timestamp DATETIME,
            patterns_matched TEXT,
            confidence REAL
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS pattern_performance (
            pattern TEXT PRIMARY KEY,
            success_rate REAL,
            total_uses INTEGER,
            last_updated DATETIME
        )
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS keyword_learning (
            keyword TEXT,
            context TEXT,
            associated_with_correct BOOLEAN,
            stack_level TEXT,
            timestamp DATETIME
        )
        """)
        
        conn.commit()
        conn.close()
    
    def record_prediction(self, question_id: str, question_type: str, format: str,
                         predicted: Set[str], correct: Set[str], 
                         patterns_matched: List[str], confidence: float):
        """Record a prediction for learning"""
        was_correct = predicted == correct
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        INSERT INTO predictions 
        (question_id, question_type, format, predicted, correct, was_correct, 
         timestamp, patterns_matched, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id, question_type, format,
            json.dumps(list(predicted)), json.dumps(list(correct)),
            was_correct, datetime.now().isoformat(),
            json.dumps(patterns_matched), confidence
        ))
        conn.commit()
        conn.close()
        
        # Update pattern performance
        self._update_pattern_performance(patterns_matched, was_correct)
    
    def _update_pattern_performance(self, patterns: List[str], was_correct: bool):
        """Update success rates for patterns"""
        for pattern in patterns:
            self.pattern_success_rates[pattern]['total'] += 1
            if was_correct:
                self.pattern_success_rates[pattern]['correct'] += 1
    
    def learn_from_mistake(self, question_stem: str, options: Dict[str, str],
                          predicted: Set[str], correct: Set[str]):
        """Learn from an incorrect prediction"""
        # Extract keywords from correct answers
        correct_keywords = []
        for key in correct:
            if key in options:
                text = options[key].lower()
                # Extract medical/nursing keywords
                keywords = re.findall(r'\b(\w+(?:ing|ed|ion|ment|ure|sis|tic))\b', text)
                correct_keywords.extend(keywords)
        
        # Store associations
        for keyword in correct_keywords:
            self.keyword_associations[keyword]['correct'] += 1
        
        # Extract keywords from incorrect predictions
        for key in predicted:
            if key in options and key not in correct:
                text = options[key].lower()
                keywords = re.findall(r'\b(\w+(?:ing|ed|ion|ment|ure|sis|tic))\b', text)
                for keyword in keywords:
                    self.keyword_associations[keyword]['incorrect'] += 1
    
    def get_enhanced_patterns(self) -> Dict[str, List[str]]:
        """Get patterns enhanced by learning"""
        enhanced = defaultdict(list)
        
        # Add successful keywords to patterns
        for keyword, counts in self.keyword_associations.items():
            if counts['correct'] > counts['incorrect'] * 2:  # Strong positive association
                # Determine which stack this belongs to
                if any(term in keyword for term in ['breath', 'oxygen', 'respiratory']):
                    enhanced['BREATHING'].append(rf'\b{keyword}\b')
                elif any(term in keyword for term in ['assess', 'monitor', 'check']):
                    enhanced['ASSESSMENT'].append(rf'\b{keyword}\b')
                elif any(term in keyword for term in ['safety', 'fall', 'restrain']):
                    enhanced['SAFETY'].append(rf'\b{keyword}\b')
        
        return enhanced
    
    def get_adaptive_weights(self) -> Dict[str, float]:
        """Get adaptive weights based on pattern performance"""
        weights = {}
        
        for pattern, stats in self.pattern_success_rates.items():
            if stats['total'] > 10:  # Enough data
                success_rate = stats['correct'] / stats['total']
                weights[pattern] = 0.5 + (success_rate * 0.5)  # Scale 0.5 to 1.0
            else:
                weights[pattern] = 1.0  # Default weight
        
        return weights
    
    def save_learning_data(self):
        """Save learning data to disk"""
        data = {
            'pattern_success_rates': dict(self.pattern_success_rates),
            'keyword_associations': dict(self.keyword_associations),
            'timestamp': datetime.now().isoformat()
        }
        
        with open('tism_learning_data.pkl', 'wb') as f:
            pickle.dump(data, f)
    
    def load_learning_data(self):
        """Load previous learning data"""
        try:
            with open('tism_learning_data.pkl', 'rb') as f:
                data = pickle.load(f)
                self.pattern_success_rates.update(data['pattern_success_rates'])
                self.keyword_associations.update(data['keyword_associations'])
        except FileNotFoundError:
            pass  # No previous data
    
    def generate_learning_report(self) -> str:
        """Generate a report on what the system has learned"""
        report = []
        report.append("TISM LEARNING SYSTEM REPORT")
        report.append("="*50)
        
        # Most successful patterns
        report.append("\nMOST SUCCESSFUL PATTERNS:")
        pattern_scores = []
        for pattern, stats in self.pattern_success_rates.items():
            if stats['total'] > 5:
                success_rate = stats['correct'] / stats['total']
                pattern_scores.append((pattern, success_rate, stats['total']))
        
        for pattern, rate, total in sorted(pattern_scores, key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  {pattern}: {rate:.1%} success ({total} uses)")
        
        # Most reliable keywords
        report.append("\nMOST RELIABLE KEYWORDS:")
        keyword_scores = []
        for keyword, counts in self.keyword_associations.items():
            total = counts['correct'] + counts['incorrect']
            if total > 3:
                reliability = counts['correct'] / total
                keyword_scores.append((keyword, reliability, total))
        
        for keyword, reliability, total in sorted(keyword_scores, key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  {keyword}: {reliability:.1%} reliability ({total} occurrences)")
        
        return "\n".join(report)


class AdaptiveTISMTree:
    """TISM Tree that adapts based on learning"""
    
    def __init__(self, learning_system: TISMLearningSystem):
        self.learning_system = learning_system
        self.base_patterns = {
            'BREATHING': [r'\b(breath|oxygen|respiratory|dyspnea)'],
            'CIRCULATION': [r'\b(pulse|heart|cardiac|blood|bleeding)'],
            'ASSESSMENT': [r'\b(assess|check|monitor|measure)'],
            'SAFETY': [r'\b(safety|fall|harm|restrain)'],
        }
        
        # Add learned patterns
        enhanced = learning_system.get_enhanced_patterns()
        for stack, patterns in enhanced.items():
            if stack in self.base_patterns:
                self.base_patterns[stack].extend(patterns)
        
        # Get adaptive weights
        self.weights = learning_system.get_adaptive_weights()
    
    def predict_with_learning(self, question_id: str, stem: str, 
                             options: Dict[str, str], format: str) -> Set[str]:
        """Make prediction and learn from it"""
        # Make prediction using weighted patterns
        predicted = self._make_prediction(stem, options, format)
        
        # Record patterns that were matched
        patterns_matched = self._get_matched_patterns(options, predicted)
        
        return predicted, patterns_matched
    
    def _make_prediction(self, stem: str, options: Dict[str, str], format: str) -> Set[str]:
        """Make prediction using adaptive patterns"""
        if format == 'single':
            # Score each option
            scores = {}
            for opt_key, opt_text in options.items():
                score = 0
                for stack, patterns in self.base_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, opt_text, re.IGNORECASE):
                            # Apply learned weight
                            weight = self.weights.get(pattern, 1.0)
                            score += 100 * weight
                scores[opt_key] = score
            
            # Return highest scoring
            if scores:
                best = max(scores.keys(), key=lambda k: scores[k])
                return {best}
            return {list(options.keys())[0]}
        
        else:  # SATA
            selected = set()
            for opt_key, opt_text in options.items():
                score = 0
                for stack, patterns in self.base_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, opt_text, re.IGNORECASE):
                            weight = self.weights.get(pattern, 1.0)
                            score += 50 * weight
                
                if score > 50:  # Adaptive threshold
                    selected.add(opt_key)
            
            return selected if selected else {list(options.keys())[0]}
    
    def _get_matched_patterns(self, options: Dict[str, str], predicted: Set[str]) -> List[str]:
        """Get patterns that matched in prediction"""
        matched = []
        for key in predicted:
            if key in options:
                text = options[key]
                for stack, patterns in self.base_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            matched.append(pattern)
        return matched


# Student-friendly quick reference generator
def generate_student_quickref(learning_system: TISMLearningSystem) -> str:
    """Generate a student-friendly quick reference based on learning"""
    ref = []
    ref.append("TISM QUICK REFERENCE CARD")
    ref.append("="*30)
    ref.append("\n🎯 PRIORITY ORDER:")
    ref.append("1. AIRWAY/BREATHING - Look for: oxygen, respiratory, dyspnea, position")
    ref.append("2. CIRCULATION - Look for: bleeding, pulse, cardiac, compress")
    ref.append("3. SAFETY - Look for: fall, restraint, infection")
    ref.append("4. ASSESSMENT - Look for: check, monitor, vital signs")
    
    # Add top learned keywords
    ref.append("\n💡 KEY WORDS TO SPOT:")
    keywords = learning_system.keyword_associations
    top_keywords = sorted(keywords.items(), 
                         key=lambda x: x[1]['correct'], 
                         reverse=True)[:10]
    
    for keyword, counts in top_keywords:
        if counts['correct'] > counts['incorrect']:
            ref.append(f"  • {keyword}")
    
    ref.append("\n📝 REMEMBER:")
    ref.append("• Assessment before intervention")
    ref.append("• Physical before psychosocial")
    ref.append("• Actual problems before potential")
    
    return "\n".join(ref)


if __name__ == "__main__":
    # Initialize learning system
    learning = TISMLearningSystem()
    
    # Create adaptive TISM
    adaptive_tism = AdaptiveTISMTree(learning)
    
    print("TISM Learning System initialized")
    print("\nThe system will:")
    print("1. Learn from every prediction")
    print("2. Identify successful patterns")
    print("3. Build keyword associations")
    print("4. Generate student quick-reference cards")
    print("\nAll learning happens without AI seeing questions!")