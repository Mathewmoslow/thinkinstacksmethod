#!/usr/bin/env python3
"""
TISM with Integrated Clinical Knowledge Base
Combines context-aware TISM with comprehensive clinical knowledge
"""

import re
import logging
from typing import Dict, Set, Optional, Tuple, List
from nclex_validation_framework import NCLEXQuestion
from nclex_exceptions_handler import NCLEXExceptionHandler
from clinical_knowledge_base import get_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TISMWithClinicalKB:
    """TISM implementation with full clinical knowledge base integration"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.decision_log = []
        self.exception_handler = NCLEXExceptionHandler()
        self.knowledge_base = get_knowledge_base()
        
        # TISM Priority Framework remains the same
        self.TISM_PRIORITIES = {
            'life_threat': 1000,      # ABC + Disability
            'safety': 800,            # Falls, infection, violence
            'physical_urgent': 600,   # Glucose, pain (hours)
            'physical_routine': 400,  # Nutrition, fluids (days)
            'assessment': 500,        # Can override physical if no emergency
            'psychosocial': 200      # Last priority
        }
    
    def predict(self, question: NCLEXQuestion) -> Set[str]:
        """Predict answer using TISM framework with clinical knowledge"""
        self.decision_log = []
        
        if not question.options:
            return set()
        
        # Extract comprehensive context
        context = self._extract_comprehensive_context(question)
        self._log(f"Context extracted: {len(context['medications'])} meds, "
                 f"{len(context['conditions'])} conditions, "
                 f"{len(context['vital_signs'])} vitals")
        
        # Check for exceptions
        exceptions = self.exception_handler.detect_exceptions(question.stem, question.options)
        
        # Solve based on question format
        if question.format == 'single':
            prediction = self._solve_single_answer(question, context)
        elif question.format == 'sata':
            prediction = self._solve_sata(question, context)
        else:
            prediction = self._solve_ordered(question, context)
        
        # Apply exceptions
        if exceptions:
            prediction = self.exception_handler.apply_exception_rules(
                question.stem, question.options, prediction, exceptions
            )
        
        return prediction
    
    def _extract_comprehensive_context(self, question: NCLEXQuestion) -> Dict:
        """Extract all clinical context from question"""
        context = {
            'medications': [],
            'conditions': [],
            'symptoms': [],
            'vital_signs': {},
            'clinical_patterns': [],
            'is_emergency': False,
            'patient_info': {}
        }
        
        # Extract from stem
        stem_lower = question.stem.lower()
        
        # Extract vital signs from stem
        stem_vitals = self._extract_vital_signs(question.stem)
        context['vital_signs'].update(stem_vitals)
        
        # Extract medications
        # Add pattern matching for medication classes
        med_patterns = {
            'beta_blockers': r'beta[\s-]?blocker|class\s+II\s+antidysrhythmic',
            'ace_inhibitors': r'ace\s+inhibitor|pril\b',
            'diuretics': r'diuretic|furosemide|lasix',
            'anticoagulants': r'anticoagulant|warfarin|heparin',
            'insulin': r'insulin',
            'opioids': r'opioid|morphine|fentanyl'
        }
        
        for med_class, pattern in med_patterns.items():
            if re.search(pattern, stem_lower, re.IGNORECASE):
                context['medications'].append(med_class)
        
        # Also check for specific drug names
        for med_class, med_info in self.knowledge_base.MEDICATION_EFFECTS.items():
            if 'class_examples' in med_info:
                for drug in med_info['class_examples']:
                    if drug in stem_lower:
                        context['medications'].append(med_class)
                        break
        
        # Extract symptoms
        all_symptoms = []
        for pattern_data in self.knowledge_base.CLINICAL_PATTERNS.values():
            if 'symptoms' in pattern_data:
                all_symptoms.extend(pattern_data['symptoms'])
        
        for symptom in set(all_symptoms):
            if symptom.replace('_', ' ') in stem_lower:
                context['symptoms'].append(symptom)
        
        # Identify clinical patterns
        patterns = self.knowledge_base.identify_clinical_pattern(
            context['symptoms'], 
            context['vital_signs']
        )
        context['clinical_patterns'] = patterns
        
        # Check if emergency
        context['is_emergency'] = any(
            pattern[1].get('priority') == 'life_threat' 
            for pattern in patterns
        ) or 'immediately' in stem_lower or 'first' in stem_lower
        
        return context
    
    def _extract_vital_signs(self, text: str) -> Dict[str, float]:
        """Extract all vital signs and lab values from text"""
        vitals = {}
        
        # Use patterns from knowledge base
        patterns = {
            'heart_rate': r'(?:HR|heart rate)[:\s]*(\d+)|(\d+)\s*(?:bpm|beats per minute)',
            'respiratory_rate': r'(?:RR|respiratory rate)[:\s]*(\d+)|(\d+)\s*(?:breaths per minute)',
            'blood_pressure': r'(?:BP|blood pressure)[:\s]*(\d+)/(\d+)|(\d+)/(\d+)\s*mm\s*Hg',
            'temperature_celsius': r'(?:temp|temperature)[:\s]*(\d+\.?\d*)\s*°?C',
            'temperature_fahrenheit': r'(?:temp|temperature)[:\s]*(\d+\.?\d*)\s*°?F',
            'oxygen_saturation': r'(?:O2 sat|SpO2|oxygen saturation)[:\s]*(\d+)%?|(\d+)%?\s*O2',
            'blood_glucose': r'(?:glucose|blood sugar|BG)[:\s]*(\d+)|(\d+)\s*mg/dL'
        }
        
        for vital_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if vital_type == 'blood_pressure' and matches[0]:
                    # Handle BP specially
                    if matches[0][0] and matches[0][1]:
                        vitals['blood_pressure_systolic'] = float(matches[0][0])
                        vitals['blood_pressure_diastolic'] = float(matches[0][1])
                    elif matches[0][2] and matches[0][3]:
                        vitals['blood_pressure_systolic'] = float(matches[0][2])
                        vitals['blood_pressure_diastolic'] = float(matches[0][3])
                else:
                    # Get first non-empty group
                    value = next((float(g) for g in matches[0] if g), None)
                    if value:
                        vitals[vital_type] = value
        
        return vitals
    
    def _evaluate_option_clinically(self, option_text: str, context: Dict) -> Dict:
        """Evaluate an option using clinical knowledge base"""
        evaluation = {
            'tism_priority': None,
            'clinical_priority': 0,
            'is_appropriate': True,
            'is_contraindicated': False,
            'addresses_emergency': False,
            'reasoning': [],
            'vital_assessments': {}
        }
        
        option_lower = option_text.lower()
        
        # Extract vitals from option
        option_vitals = self._extract_vital_signs(option_text)
        
        # Evaluate each vital sign
        for vital_name, vital_value in option_vitals.items():
            is_normal, assessment = self.knowledge_base.is_value_normal(
                vital_name, vital_value, context
            )
            evaluation['vital_assessments'][vital_name] = {
                'value': vital_value,
                'is_normal': is_normal,
                'assessment': assessment
            }
            
            if is_normal is False and 'CRITICAL' in assessment:
                evaluation['clinical_priority'] = 1000
                evaluation['reasoning'].append(assessment)
        
        # Check if option addresses identified clinical patterns
        for pattern_name, pattern_data in context['clinical_patterns']:
            if pattern_data.get('immediate_intervention'):
                intervention = pattern_data['immediate_intervention']
                if intervention.replace('_', ' ') in option_lower:
                    evaluation['addresses_emergency'] = True
                    evaluation['clinical_priority'] = 1200  # Highest priority
                    evaluation['reasoning'].append(f"Addresses {pattern_name}: {intervention}")
        
        # Check medication considerations
        for med_class in context['medications']:
            med_info = self.knowledge_base.get_medication_considerations(med_class)
            
            # Check hold parameters
            if 'hold_parameters' in med_info:
                for param, threshold in med_info['hold_parameters'].items():
                    if param in option_vitals and option_vitals[param] < threshold:
                        evaluation['clinical_priority'] = 1000
                        evaluation['reasoning'].append(
                            f"Critical: {param} below hold parameter for {med_class}"
                        )
            
            # Check for side effects mentioned
            if 'side_effects' in med_info:
                for side_effect in med_info['side_effects']:
                    if side_effect.replace('_', ' ') in option_lower:
                        evaluation['reasoning'].append(
                            f"Mentions {side_effect} - known side effect of {med_class}"
                        )
        
        # Determine TISM priority category
        if evaluation['clinical_priority'] >= 1000 or evaluation['addresses_emergency']:
            evaluation['tism_priority'] = 'life_threat'
        elif 'safety' in option_lower or 'fall' in option_lower or 'infection' in option_lower:
            evaluation['tism_priority'] = 'safety'
        elif any(vital not in ['is_normal'] for vital in evaluation['vital_assessments'].values()):
            evaluation['tism_priority'] = 'physical_urgent'
        elif re.search(r'\b(assess|check|monitor|measure)\b', option_lower):
            evaluation['tism_priority'] = 'assessment'
        else:
            evaluation['tism_priority'] = 'physical_routine'
        
        # Check appropriateness
        is_appropriate, reasoning = self.knowledge_base.is_intervention_appropriate(
            option_text, context
        )
        evaluation['is_appropriate'] = is_appropriate
        if not is_appropriate:
            evaluation['is_contraindicated'] = True
            evaluation['reasoning'].append(reasoning)
            evaluation['clinical_priority'] = -1000  # Negative priority
        
        return evaluation
    
    def _solve_single_answer(self, question: NCLEXQuestion, context: Dict) -> Set[str]:
        """Solve single answer questions with clinical knowledge"""
        evaluations = {}
        
        for opt_key, opt_text in question.options.items():
            eval_result = self._evaluate_option_clinically(opt_text, context)
            evaluations[opt_key] = eval_result
            
            # Calculate final score
            tism_score = self.TISM_PRIORITIES.get(eval_result['tism_priority'], 0)
            clinical_score = eval_result['clinical_priority']
            final_score = tism_score + clinical_score
            
            self._log(f"Option {opt_key}: TISM={eval_result['tism_priority']} ({tism_score}), "
                     f"Clinical={clinical_score}, Final={final_score}")
            if eval_result['reasoning']:
                self._log(f"  Reasoning: {'; '.join(eval_result['reasoning'][:2])}")
        
        # Select best option
        best_option = max(
            evaluations.keys(),
            key=lambda k: (
                evaluations[k]['clinical_priority'] + 
                self.TISM_PRIORITIES.get(evaluations[k]['tism_priority'], 0),
                evaluations[k]['addresses_emergency'],
                not evaluations[k]['is_contraindicated']
            )
        )
        
        self._log(f"Selected: {best_option}")
        return {best_option}
    
    def _solve_sata(self, question: NCLEXQuestion, context: Dict) -> Set[str]:
        """Solve SATA with clinical knowledge"""
        selected = set()
        
        # Check if teaching question
        is_teaching = any(word in question.stem.lower() 
                         for word in ['teaching', 'understanding', 'indicates', 'reinforce'])
        
        for opt_key, opt_text in question.options.items():
            should_include = False
            reason = ""
            
            if is_teaching:
                # Use teaching knowledge from KB
                should_include = self._evaluate_teaching_statement(opt_text, context)
                reason = "correct teaching" if should_include else "incorrect teaching"
            else:
                # Clinical evaluation
                eval_result = self._evaluate_option_clinically(opt_text, context)
                
                # Include if:
                # 1. Not contraindicated
                # 2. Addresses a clinical need
                # 3. Is appropriate intervention/assessment
                if not eval_result['is_contraindicated'] and (
                    eval_result['clinical_priority'] > 0 or
                    eval_result['tism_priority'] in ['life_threat', 'safety', 'physical_urgent', 'assessment'] or
                    eval_result['is_appropriate']
                ):
                    should_include = True
                    reason = eval_result['reasoning'][0] if eval_result['reasoning'] else eval_result['tism_priority']
            
            if should_include:
                selected.add(opt_key)
                self._log(f"SATA included {opt_key}: {reason}")
            else:
                self._log(f"SATA excluded {opt_key}: {reason}")
        
        # Ensure reasonable number for SATA (typically 2-4)
        if len(selected) < 2:
            # Add most appropriate remaining options
            remaining = set(question.options.keys()) - selected
            for opt_key in list(remaining)[:2-len(selected)]:
                selected.add(opt_key)
                self._log(f"SATA added {opt_key}: minimum threshold")
        
        return selected
    
    def _solve_ordered(self, question: NCLEXQuestion, context: Dict) -> Set[str]:
        """Solve ordered response with clinical knowledge"""
        evaluations = {}
        
        for opt_key, opt_text in question.options.items():
            eval_result = self._evaluate_option_clinically(opt_text, context)
            priority_score = (
                self.TISM_PRIORITIES.get(eval_result['tism_priority'], 0) +
                eval_result['clinical_priority']
            )
            evaluations[opt_key] = priority_score
        
        # Sort by priority (highest first)
        ordered = sorted(evaluations.keys(), key=lambda k: evaluations[k], reverse=True)
        
        return {','.join(ordered)}
    
    def _evaluate_teaching_statement(self, statement: str, context: Dict) -> bool:
        """Evaluate if a teaching statement is correct using KB"""
        statement_lower = statement.lower()
        
        # Check against known incorrect teaching points
        for category in self.knowledge_base.PATIENT_TEACHING.values():
            if 'incorrect' in category:
                for incorrect in category['incorrect']:
                    if incorrect.replace('_', ' ') in statement_lower:
                        return False
        
        # Check for correct teaching points
        for category in self.knowledge_base.PATIENT_TEACHING.values():
            if 'correct' in category:
                for correct in category['correct']:
                    if correct.replace('_', ' ') in statement_lower:
                        return True
        
        # Check specific disease teaching
        for disease, teaching in self.knowledge_base.PATIENT_TEACHING.get('disease_management', {}).items():
            if disease in str(context.get('conditions', [])):
                if 'incorrect' in teaching:
                    for incorrect in teaching['incorrect']:
                        if incorrect.replace('_', ' ') in statement_lower:
                            return False
                if 'correct' in teaching:
                    for correct in teaching['correct']:
                        if correct.replace('_', ' ') in statement_lower:
                            return True
        
        # Default to false for safety
        return False
    
    def _log(self, message: str):
        """Log decision process"""
        if self.debug:
            self.decision_log.append(message)
            logger.debug(message)

if __name__ == "__main__":
    print("TISM with Clinical Knowledge Base")
    print("="*50)
    
    # Test on challenging questions
    tism = TISMWithClinicalKB(debug=True)
    kb = get_knowledge_base()
    
    # Test normal value checking
    print("\nKnowledge Base Capabilities:")
    print("- Normal ranges for", len(kb.NORMAL_RANGES), "parameters")
    print("- Medication effects for", len(kb.MEDICATION_EFFECTS), "drug classes")
    print("- Clinical patterns:", list(kb.CLINICAL_PATTERNS.keys()))
    
    # Test question
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
    for log in tism.decision_log[-10:]:
        print(f"  {log}")