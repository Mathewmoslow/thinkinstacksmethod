#!/usr/bin/env python3
"""
Context-Aware TISM Implementation
Evaluates clinical context, not just keywords
"""

import re
import logging
from typing import Dict, Set, Optional, Tuple
from nclex_validation_framework import NCLEXQuestion
from nclex_exceptions_handler import NCLEXExceptionHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextAwareTISM:
    """TISM that understands clinical context, not just keywords"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.decision_log = []
        self.exception_handler = NCLEXExceptionHandler()
        
        # Normal ranges for vital signs
        self.NORMAL_RANGES = {
            'heart_rate': (60, 100),  # bpm
            'respiratory_rate': (12, 20),  # breaths/min
            'blood_pressure_systolic': (90, 140),  # mmHg
            'blood_pressure_diastolic': (60, 90),  # mmHg
            'temperature_c': (36.5, 37.5),  # Celsius
            'temperature_f': (97.7, 99.5),  # Fahrenheit
            'oxygen_saturation': (95, 100),  # %
            'blood_glucose': (70, 110),  # mg/dL
        }
        
        # Clinical contexts that modify priority
        self.CLINICAL_CONTEXTS = {
            'medications': {
                'beta_blocker': {
                    'effects': ['bradycardia', 'hypotension', 'fatigue'],
                    'concerning_hr': 60,  # HR below this is concerning
                },
                'opioid': {
                    'effects': ['respiratory_depression', 'sedation', 'constipation'],
                    'concerning_rr': 12,  # RR below this is concerning
                },
                'diuretic': {
                    'effects': ['dehydration', 'hypokalemia', 'hypotension'],
                    'monitor': ['electrolytes', 'blood_pressure', 'urine_output']
                }
            }
        }
    
    def predict(self, question: NCLEXQuestion) -> Set[str]:
        """Context-aware prediction"""
        self.decision_log = []
        
        if not question.options:
            return set()
        
        # Extract context from stem
        stem_context = self._extract_stem_context(question.stem)
        self._log(f"Stem context: {stem_context}")
        
        # Check for exceptions
        exceptions = self.exception_handler.detect_exceptions(question.stem, question.options)
        
        # Evaluate each option in context
        if question.format == 'single':
            prediction = self._solve_single_contextual(question, stem_context)
        elif question.format == 'sata':
            prediction = self._solve_sata_contextual(question, stem_context)
        else:
            prediction = self._solve_ordered_contextual(question, stem_context)
        
        # Apply exceptions if present
        if exceptions:
            prediction = self.exception_handler.apply_exception_rules(
                question.stem, question.options, prediction, exceptions
            )
        
        return prediction
    
    def _extract_stem_context(self, stem: str) -> Dict:
        """Extract clinical context from question stem"""
        context = {
            'medications': [],
            'conditions': [],
            'symptoms': [],
            'timeframe': None,
            'is_emergency': False,
            'clinical_setting': None,
            'vital_signs': {}
        }
        
        stem_lower = stem.lower()
        
        # Extract vital signs from stem too
        stem_vitals = self._extract_vital_signs(stem)
        context['vital_signs'] = stem_vitals
        
        # Extract medications
        med_patterns = [
            r'beta[\s-]?blocker',
            r'ace inhibitor',
            r'diuretic',
            r'opioid',
            r'antibiotic',
            r'antidiarrheal',
            r'antihistamine',
            r'insulin',
            r'Class\s+[IVX]+\s+\w+'
        ]
        for pattern in med_patterns:
            if re.search(pattern, stem_lower, re.IGNORECASE):
                context['medications'].append(pattern.replace('\\s+', ' ').replace('\\', ''))
        
        # Extract conditions
        condition_patterns = [
            r'diabetes', r'hypertension', r'heart failure', r'COPD',
            r'pneumonia', r'diarrhea', r'infection', r'stroke',
            r'hypoglycemia', r'bleeding', r'shock', r'arrhythmia',
            r'irregular heartbeat', r'rapid.*heartbeat'
        ]
        for pattern in condition_patterns:
            if re.search(pattern, stem_lower):
                context['conditions'].append(pattern)
        
        # Extract symptoms
        symptom_patterns = [
            r'headache', r'nausea', r'vomiting', r'pain',
            r'dyspnea', r'shortness of breath', r'dizziness',
            r'fatigue', r'weakness', r'confusion', r'sweaty',
            r'shaky', r'bleeding', r'fever'
        ]
        for pattern in symptom_patterns:
            if re.search(pattern, stem_lower):
                context['symptoms'].append(pattern)
        
        # Check for emergency indicators
        emergency_patterns = [
            r'immediately', r'emergent', r'stat', r'urgent',
            r'first', r'priority', r'life.?threatening'
        ]
        context['is_emergency'] = any(re.search(p, stem_lower) for p in emergency_patterns)
        
        # Extract timeframe
        if re.search(r'three days', stem_lower):
            context['timeframe'] = '3_days'
        elif re.search(r'sudden', stem_lower):
            context['timeframe'] = 'acute'
        elif re.search(r'chronic', stem_lower):
            context['timeframe'] = 'chronic'
        
        return context
    
    def _evaluate_option_in_context(self, option_text: str, stem_context: Dict) -> Dict:
        """Evaluate an option considering the clinical context"""
        evaluation = {
            'priority_score': 0,
            'is_normal': False,
            'is_abnormal': False,
            'is_critical': False,
            'is_expected': False,
            'requires_action': False,
            'clinical_reasoning': []
        }
        
        option_lower = option_text.lower()
        
        # Extract vital signs from option
        vitals = self._extract_vital_signs(option_text)
        
        # Evaluate vital signs in context
        for vital_type, value in vitals.items():
            normal_range = self.NORMAL_RANGES.get(vital_type)
            if normal_range:
                if normal_range[0] <= value <= normal_range[1]:
                    evaluation['is_normal'] = True
                    evaluation['clinical_reasoning'].append(f"{vital_type} is normal")
                else:
                    evaluation['is_abnormal'] = True
                    evaluation['clinical_reasoning'].append(f"{vital_type} is abnormal: {value}")
                    
                    # Check if critical in context
                    if self._is_critical_in_context(vital_type, value, stem_context):
                        evaluation['is_critical'] = True
                        evaluation['priority_score'] = 1000
                        evaluation['clinical_reasoning'].append(f"{vital_type} is CRITICAL given context")
        
        # Check for expected side effects
        for med in stem_context.get('medications', []):
            if 'beta_blocker' in med and 'heart rate' in option_lower:
                hr = vitals.get('heart_rate', 100)
                if hr < 60:
                    evaluation['is_critical'] = True
                    evaluation['requires_action'] = True
                    evaluation['clinical_reasoning'].append("Bradycardia with beta-blocker - critical")
                    evaluation['priority_score'] = 1000
        
        # Check for hypoglycemia context
        stem_glucose = stem_context.get('vital_signs', {}).get('blood_glucose')
        if stem_glucose and stem_glucose < 70:
            # In hypoglycemia, intervention > assessment
            if re.search(r'\b(give|administer|provide).*carbohydrate', option_lower, re.IGNORECASE):
                evaluation['is_critical'] = True
                evaluation['requires_action'] = True
                evaluation['clinical_reasoning'].append("Hypoglycemia intervention - critical")
                evaluation['priority_score'] = 1200  # Higher than assessment
        
        # Check for concerning combinations
        if 'fever' in option_lower and 'bloody' in option_lower and 'diarrhea' in stem_context.get('conditions', []):
            evaluation['is_critical'] = True
            evaluation['requires_action'] = True
            evaluation['clinical_reasoning'].append("Fever + bloody stools = possible infection")
            evaluation['priority_score'] = 900
        
        # Evaluate actions
        if re.search(r'\b(assess|check|monitor|measure)\b', option_lower):
            if evaluation['is_critical']:
                # Assessment is good but not priority in emergency
                evaluation['priority_score'] = max(500, evaluation['priority_score'] - 200)
            else:
                # Assessment is priority when no critical findings
                evaluation['priority_score'] = 600
        
        return evaluation
    
    def _extract_vital_signs(self, text: str) -> Dict[str, float]:
        """Extract numerical vital signs from text"""
        vitals = {}
        
        # Heart rate
        hr_match = re.search(r'(\d+)\s*beats?\s*per\s*minute', text, re.IGNORECASE)
        if hr_match:
            vitals['heart_rate'] = float(hr_match.group(1))
        
        # Respiratory rate
        rr_match = re.search(r'(\d+)\s*breaths?\s*per\s*minute', text, re.IGNORECASE)
        if rr_match:
            vitals['respiratory_rate'] = float(rr_match.group(1))
        
        # Blood pressure
        bp_match = re.search(r'(\d+)/(\d+)\s*mm\s*Hg', text, re.IGNORECASE)
        if bp_match:
            vitals['blood_pressure_systolic'] = float(bp_match.group(1))
            vitals['blood_pressure_diastolic'] = float(bp_match.group(2))
        
        # Temperature
        temp_c_match = re.search(r'(\d+\.?\d*)\s*°?C', text)
        if temp_c_match:
            vitals['temperature_c'] = float(temp_c_match.group(1))
        
        temp_f_match = re.search(r'(\d+\.?\d*)\s*°?F', text)
        if temp_f_match:
            vitals['temperature_f'] = float(temp_f_match.group(1))
        
        # O2 saturation
        o2_match = re.search(r'(\d+)\s*%?\s*O2|SpO2\s*(\d+)', text, re.IGNORECASE)
        if o2_match:
            vitals['oxygen_saturation'] = float(o2_match.group(1) or o2_match.group(2))
        
        # Blood glucose
        glucose_match = re.search(r'glucose\s*(?:is\s*)?(\d+)\s*mg/dL', text, re.IGNORECASE)
        if not glucose_match:
            glucose_match = re.search(r'(\d+)\s*mg/dL', text)
        if glucose_match:
            vitals['blood_glucose'] = float(glucose_match.group(1))
        
        return vitals
    
    def _is_critical_in_context(self, vital_type: str, value: float, context: Dict) -> bool:
        """Determine if a vital sign is critical given the clinical context"""
        # Beta-blocker + low HR
        if vital_type == 'heart_rate' and value < 60:
            if any('beta' in med.lower() for med in context.get('medications', [])):
                return True
        
        # Opioid + low RR
        if vital_type == 'respiratory_rate' and value < 12:
            if any('opioid' in med.lower() for med in context.get('medications', [])):
                return True
        
        # Any extreme values
        if vital_type == 'heart_rate' and (value < 50 or value > 150):
            return True
        if vital_type == 'respiratory_rate' and (value < 10 or value > 30):
            return True
        if vital_type == 'oxygen_saturation' and value < 90:
            return True
        if vital_type == 'blood_glucose' and value < 70:
            return True  # Hypoglycemia is always critical
        
        return False
    
    def _solve_single_contextual(self, question: NCLEXQuestion, stem_context: Dict) -> Set[str]:
        """Solve single answer with context awareness"""
        evaluations = {}
        
        for opt_key, opt_text in question.options.items():
            eval_result = self._evaluate_option_in_context(opt_text, stem_context)
            evaluations[opt_key] = eval_result
            
            self._log(f"Option {opt_key}: Priority={eval_result['priority_score']}, "
                     f"Critical={eval_result['is_critical']}, "
                     f"Reasoning={'; '.join(eval_result['clinical_reasoning'])}")
        
        # Find highest priority option
        best_option = max(evaluations.keys(), 
                         key=lambda k: (evaluations[k]['priority_score'], 
                                       evaluations[k]['is_critical'],
                                       evaluations[k]['requires_action']))
        
        self._log(f"Selected {best_option} based on contextual evaluation")
        return {best_option}
    
    def _solve_sata_contextual(self, question: NCLEXQuestion, stem_context: Dict) -> Set[str]:
        """Solve SATA with context awareness"""
        selected = set()
        
        for opt_key, opt_text in question.options.items():
            eval_result = self._evaluate_option_in_context(opt_text, stem_context)
            
            # Include if clinically appropriate
            should_include = (
                eval_result['is_critical'] or
                eval_result['requires_action'] or
                (eval_result['priority_score'] >= 500 and not eval_result['is_normal']) or
                (self._is_appropriate_nursing_action(opt_text) and not self._is_contraindicated_in_context(opt_text, stem_context))
            )
            
            if should_include:
                selected.add(opt_key)
                self._log(f"SATA included {opt_key}: {eval_result['clinical_reasoning']}")
            else:
                self._log(f"SATA excluded {opt_key}: Normal or not indicated")
        
        # Ensure reasonable number for SATA
        if len(selected) < 2:
            # Add next best options
            remaining = [k for k in question.options.keys() if k not in selected]
            # Just add first remaining options if we don't have evaluations
            for opt_key in remaining[:2-len(selected)]:
                selected.add(opt_key)
        
        return selected
    
    def _solve_ordered_contextual(self, question: NCLEXQuestion, stem_context: Dict) -> Set[str]:
        """Solve ordered response with context awareness"""
        evaluations = {}
        
        for opt_key, opt_text in question.options.items():
            evaluations[opt_key] = self._evaluate_option_in_context(opt_text, stem_context)
        
        # Sort by priority
        ordered = sorted(evaluations.keys(),
                        key=lambda k: (evaluations[k]['priority_score'],
                                      evaluations[k]['is_critical'],
                                      evaluations[k]['requires_action']),
                        reverse=True)
        
        return {','.join(ordered)}
    
    def _is_appropriate_nursing_action(self, text: str) -> bool:
        """Check if text describes appropriate nursing action"""
        action_patterns = [
            r'\b(assess|monitor|check|document|report|notify)\b',
            r'\b(provide|ensure|maintain|position|teach)\b',
            r'\b(administer|give|apply|implement)\b'
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in action_patterns)
    
    def _is_contraindicated_in_context(self, option_text: str, context: Dict) -> bool:
        """Check if option is contraindicated given context"""
        option_lower = option_text.lower()
        
        # Antidiarrheal + signs of infection
        if 'antidiarrheal' in str(context.get('medications', [])):
            if 'fever' in option_lower and 'bloody' in option_lower:
                return True
        
        # Other contraindications can be added here
        
        return False
    
    def _log(self, message: str):
        """Log decision process"""
        if self.debug:
            self.decision_log.append(message)
            logger.debug(message)

if __name__ == "__main__":
    print("Context-Aware TISM Implementation")
    print("="*50)
    
    # Test on problematic question
    tism = ContextAwareTISM(debug=True)
    
    test_q = NCLEXQuestion(
        id="test",
        stem="A client with rapid, irregular heartbeats is prescribed a Class II antidysrhythmic (beta-blocker). Which finding should the nurse report immediately to the provider?",
        options={
            'A': 'Heart rate of 52 beats per minute',
            'B': 'Respiratory rate of 18 breaths per minute',
            'C': 'Blood pressure of 130/80 mm Hg',
            'D': 'Reports of mild fatigue'
        },
        correct_answers={'A'},
        format='single',
        question_type='priority'
    )
    
    print(f"\nTest Question: {test_q.stem}")
    result = tism.predict(test_q)
    print(f"\nPredicted: {result}")
    print(f"Correct: {test_q.correct_answers}")
    print(f"Match: {result == test_q.correct_answers}")
    
    print("\nDecision Process:")
    for log in tism.decision_log:
        print(f"  {log}")