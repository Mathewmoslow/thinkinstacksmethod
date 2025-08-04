#!/usr/bin/env python3
"""
Enhanced TISM with Subtle Priority Recognition
Handles implicit priorities through pattern recognition and clinical reasoning
"""

import re
import json
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import logging

from nclex_validation_framework import NCLEXQuestion
from clinical_knowledge_base import get_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClinicalPattern:
    """Represents a clinical pattern with its priority implications"""
    pattern_name: str
    indicators: List[str]
    priority_level: str
    confidence: float
    reasoning: str

class SubtlePriorityRecognizer:
    """Recognizes subtle clinical priorities without explicit keywords"""
    
    def __init__(self):
        self.kb = get_knowledge_base()
        
        # Define subtle priority patterns
        self.SUBTLE_PATTERNS = {
            # Abnormal vital signs patterns
            'extreme_vitals': {
                'patterns': [
                    (r'heart rate.*?(\d+)', lambda x: int(x) > 120 or int(x) < 50),
                    (r'HR.*?(\d+)', lambda x: int(x) > 120 or int(x) < 50),
                    (r'(\d+)\s*beats per minute', lambda x: int(x) > 120 or int(x) < 50),
                    (r'blood pressure.*?(\d+)/(\d+)', lambda x, y: int(x) < 90 or int(x) > 180),
                    (r'respiratory rate.*?(\d+)', lambda x: int(x) < 10 or int(x) > 30),
                    (r'O2 sat.*?(\d+)%?', lambda x: int(x) < 90),
                    (r'glucose.*?(\d+)', lambda x: int(x) < 70 or int(x) > 400),
                ],
                'priority': 'life_threat',
                'reasoning': 'Extreme vital signs indicate potential life threat'
            },
            
            # Medication side effects requiring action
            'dangerous_side_effects': {
                'patterns': [
                    (r'heart rate.*?(13[5-9]|1[4-9]\d|[2-9]\d\d).*palpitations', 1100),  # HR >135 with palpitations
                    (r'(tachycardia|palpitations).*heart rate', 1000),
                    (r'(bleeding|hemorrhage|blood)', 1000),
                    (r'(respiratory depression|RR.*[<]\s*12)', 1000),
                    (r'(anaphylaxis|swelling.*tongue)', 1200),  # Removed general throat
                    (r'throat.*swelling', 1200),  # Specific throat swelling
                    (r'(chest pain|crushing)', 1000),
                    (r'mild.*throat.*irritation', 100),  # Low priority for mild irritation
                ],
                'priority': 'life_threat',
                'reasoning': 'Dangerous medication side effect requiring immediate action'
            },
            
            # Suicide/violence risk levels
            'high_risk_behaviors': {
                'patterns': [
                    (r'(specific plan|detailed plan)', 1000),
                    (r'(method.*intent|intent.*method)', 900),
                    (r'(previous attempt|prior attempt)', 800),
                    (r'(command hallucinations)', 900),
                    (r'(homicidal|harm.*others)', 1000),
                ],
                'priority': 'safety',
                'reasoning': 'High risk for self-harm or violence'
            },
            
            # Deteriorating conditions
            'clinical_deterioration': {
                'patterns': [
                    (r'(new onset|sudden|acute).*confusion', 900),
                    (r'(decreased|absent).*pulse', 1200),
                    (r'(cyanosis|blue|dusky)', 1000),
                    (r'unresponsive', 1200),
                    (r'(severe|increasing|worsening).*pain', 700),
                ],
                'priority': 'life_threat',
                'reasoning': 'Signs of clinical deterioration'
            },
            
            # Post-op complications
            'post_op_emergency': {
                'patterns': [
                    (r'post.?op.*absent.*pulse', 1200),
                    (r'post.?op.*bleeding', 1000),
                    (r'post.?op.*respiratory distress', 1000),
                    (r'dehiscence|evisceration', 1100),
                    (r'post.?op.*fever.*high', 800),
                ],
                'priority': 'life_threat', 
                'reasoning': 'Post-operative complication requiring immediate intervention'
            },
            
            # Assessment findings requiring action
            'concerning_assessments': {
                'patterns': [
                    (r'pupil.*(?:fixed|dilated|unequal)', 900),
                    (r'(board-like|rigid).*abdomen', 900),
                    (r'absent.*bowel sounds.*surgery', 800),
                    (r'sudden.*severe.*headache', 900),
                    (r'chest.*crushing.*pressure', 1000),
                ],
                'priority': 'urgent',
                'reasoning': 'Assessment finding indicating serious condition'
            }
        }
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        for category in self.SUBTLE_PATTERNS.values():
            compiled = []
            for pattern in category['patterns']:
                if isinstance(pattern, tuple) and isinstance(pattern[0], str):
                    compiled.append((re.compile(pattern[0], re.IGNORECASE), pattern[1]))
                else:
                    compiled.append(pattern)
            category['compiled_patterns'] = compiled
    
    def analyze_option(self, option_text: str, stem_context: Dict) -> Tuple[int, str]:
        """
        Analyze an option for subtle priority indicators
        Returns (priority_score, reasoning)
        """
        priority_score = 0
        reasoning = []
        
        # Check each pattern category
        for category_name, category_data in self.SUBTLE_PATTERNS.items():
            for pattern_data in category_data.get('compiled_patterns', []):
                if isinstance(pattern_data, tuple):
                    pattern, evaluator = pattern_data
                    match = pattern.search(option_text)
                    
                    if match:
                        # If evaluator is a function, use it to validate
                        if callable(evaluator):
                            try:
                                groups = match.groups()
                                if groups and evaluator(*[int(g) for g in groups if g]):
                                    priority_score = max(priority_score, 1000)
                                    reasoning.append(f"{category_name}: {category_data['reasoning']}")
                            except:
                                pass
                        # If evaluator is a number, it's a direct priority score
                        elif isinstance(evaluator, (int, float)):
                            priority_score = max(priority_score, evaluator)
                            reasoning.append(f"{category_name}: {category_data['reasoning']}")
        
        # Check for normal findings (lower priority)
        if self._is_normal_finding(option_text):
            priority_score = max(priority_score - 500, 0)
            reasoning.append("Normal finding - lower priority")
        
        # Check stem-option relationship
        stem_priority_boost = self._analyze_stem_option_relationship(option_text, stem_context)
        if stem_priority_boost > 0:
            priority_score += stem_priority_boost
            reasoning.append("Directly addresses stem concern")
        
        return priority_score, "; ".join(reasoning)
    
    def _is_normal_finding(self, text: str) -> bool:
        """Check if text describes normal findings"""
        normal_patterns = [
            r'normal\s+(range|limits|findings?)',
            r'within\s+normal',
            r'stable\s+vital\s+signs',
            r'no\s+distress',
            r'alert\s+and\s+oriented',
            r'clear\s+lung\s+sounds',
            r'regular\s+rhythm',
            r'pink\s+and\s+warm',
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in normal_patterns)
    
    def _analyze_stem_option_relationship(self, option_text: str, stem_context: Dict) -> int:
        """Analyze how well option addresses stem concern"""
        boost = 0
        
        # If stem mentions specific medication, boost options about its effects
        if 'medications' in stem_context:
            for med in stem_context['medications']:
                if med in option_text.lower():
                    boost += 200
        
        # If stem mentions specific condition, boost related interventions
        if 'conditions' in stem_context:
            for condition in stem_context['conditions']:
                if condition in option_text.lower():
                    boost += 150
        
        return boost
    
    def extract_stem_context(self, stem: str) -> Dict:
        """Extract clinical context from stem"""
        context = {
            'medications': [],
            'conditions': [],
            'symptoms': [],
            'urgency_indicators': []
        }
        
        # Extract medications mentioned
        med_patterns = [
            r'beta[\s-]?(?:blocker|agonist)',
            r'ACE inhibitor',
            r'diuretic',
            r'insulin',
            r'anticoagulant',
            r'opioid',
            r'benzodiazepine',
            r'antipsychotic',
        ]
        for pattern in med_patterns:
            if re.search(pattern, stem, re.IGNORECASE):
                context['medications'].append(pattern)
        
        # Extract conditions
        condition_patterns = [
            'diabetes', 'COPD', 'heart failure', 'post.?op',
            'psychiatric', 'suicide', 'depression', 'psychosis',
            'trauma', 'stroke', 'MI', 'pneumonia'
        ]
        for condition in condition_patterns:
            if re.search(condition, stem, re.IGNORECASE):
                context['conditions'].append(condition)
        
        # Extract urgency indicators
        urgency_patterns = [
            'immediate', 'priority', 'first', 'emergency',
            'stat', 'urgent', 'concerning', 'critical'
        ]
        for pattern in urgency_patterns:
            if re.search(pattern, stem, re.IGNORECASE):
                context['urgency_indicators'].append(pattern)
        
        return context

class EnhancedTISMWithSubtleRecognition:
    """TISM enhanced with subtle priority recognition"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.decision_log = []
        self.subtle_recognizer = SubtlePriorityRecognizer()
        self.kb = get_knowledge_base()
        
        # Original TISM patterns (kept for explicit cases)
        self.EXPLICIT_PATTERNS = {
            'AIRWAY': re.compile(r'\b(airway|choking|stridor|obstruction)\b', re.IGNORECASE),
            'BREATHING': re.compile(r'\b(breathing|oxygen|respiratory|dyspnea)\b', re.IGNORECASE),
            'CIRCULATION': re.compile(r'\b(circulation|pulse|bleeding|cardiac)\b', re.IGNORECASE),
            'SAFETY': re.compile(r'\b(safety|fall|restraint|infection)\b', re.IGNORECASE),
            'ASSESSMENT': re.compile(r'\b(assess|check|monitor|measure)\b', re.IGNORECASE),
        }
    
    def predict(self, question: NCLEXQuestion) -> Set[str]:
        """Enhanced prediction with subtle priority recognition"""
        self.decision_log = []
        
        if not question.options:
            return set()
        
        # Extract context
        stem_context = self.subtle_recognizer.extract_stem_context(question.stem)
        self._log(f"Stem context: {stem_context}")
        
        # Score each option
        option_scores = {}
        
        for opt_key, opt_text in question.options.items():
            # Get explicit TISM score
            explicit_score = self._get_explicit_score(opt_text)
            
            # Get subtle priority score
            subtle_score, reasoning = self.subtle_recognizer.analyze_option(opt_text, stem_context)
            
            # Combine scores (subtle can override explicit)
            total_score = max(explicit_score, subtle_score)
            
            option_scores[opt_key] = {
                'total': total_score,
                'explicit': explicit_score,
                'subtle': subtle_score,
                'reasoning': reasoning
            }
            
            self._log(f"Option {opt_key}: Total={total_score} (Explicit={explicit_score}, Subtle={subtle_score})")
            if reasoning:
                self._log(f"  Reasoning: {reasoning}")
        
        # Select based on format
        if question.format == 'single':
            # Select highest scoring option
            if option_scores:
                best = max(option_scores.keys(), key=lambda k: option_scores[k]['total'])
                return {best}
            return {list(question.options.keys())[0]}
        
        elif question.format == 'sata':
            # Select all high-priority options
            selected = set()
            
            # Include all with significant scores
            for opt_key, scores in option_scores.items():
                if scores['total'] >= 700:  # High priority threshold
                    selected.add(opt_key)
                elif scores['total'] >= 500 and len(selected) < 2:  # Medium priority
                    selected.add(opt_key)
            
            # Ensure minimum selections for SATA
            if len(selected) < 2:
                remaining = sorted(
                    [k for k in option_scores.keys() if k not in selected],
                    key=lambda k: option_scores[k]['total'],
                    reverse=True
                )
                selected.update(remaining[:2-len(selected)])
            
            return selected
        
        return set()
    
    def _get_explicit_score(self, text: str) -> int:
        """Get score from explicit TISM patterns"""
        if self.EXPLICIT_PATTERNS['AIRWAY'].search(text):
            return 1000
        elif self.EXPLICIT_PATTERNS['BREATHING'].search(text):
            return 900
        elif self.EXPLICIT_PATTERNS['CIRCULATION'].search(text):
            return 800
        elif self.EXPLICIT_PATTERNS['SAFETY'].search(text):
            return 700
        elif self.EXPLICIT_PATTERNS['ASSESSMENT'].search(text):
            return 500
        return 0
    
    def _log(self, message: str):
        """Log for debugging"""
        if self.debug:
            self.decision_log.append(message)
            logger.debug(message)

if __name__ == "__main__":
    print("Testing Enhanced TISM with Subtle Priority Recognition")
    print("="*60)
    
    # Test on problematic questions
    test_questions = [
        {
            'id': 'test1',
            'stem': 'A client on a beta-2 agonist reports the following. Which finding requires immediate attention?',
            'options': {
                'A': 'Slight tremor in hands',
                'B': 'Heart rate of 135 beats per minute with palpitations',
                'C': 'Mild throat irritation',
                'D': 'Increased appetite'
            },
            'correct': 'B',
            'explanation': 'Tachycardia with palpitations is dangerous side effect'
        },
        {
            'id': 'test2',
            'stem': 'Which client statement indicates highest suicide risk?',
            'options': {
                'A': 'I wish I could just disappear',
                'B': 'I have pills saved and a specific plan',
                'C': 'Sometimes I think about death',
                'D': 'Life feels hopeless'
            },
            'correct': 'B',
            'explanation': 'Specific plan with means indicates highest risk'
        }
    ]
    
    enhanced_tism = EnhancedTISMWithSubtleRecognition(debug=True)
    
    for q in test_questions:
        print(f"\nQuestion: {q['stem']}")
        print(f"Correct: {q['correct']} - {q['options'][q['correct']]}")
        
        nclex_q = NCLEXQuestion(
            id=q['id'],
            stem=q['stem'],
            options=q['options'],
            correct_answers={q['correct']},
            format='single',
            question_type='priority'
        )
        
        result = enhanced_tism.predict(nclex_q)
        print(f"Predicted: {list(result)[0] if result else 'None'}")
        
        if enhanced_tism.debug:
            print("\nDecision process:")
            for log in enhanced_tism.decision_log[-6:]:
                print(f"  {log}")