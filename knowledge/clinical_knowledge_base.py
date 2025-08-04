#!/usr/bin/env python3
"""
Clinical Knowledge Base for TISM
Comprehensive nursing knowledge including normal values, medication effects, 
clinical patterns, and decision rules
"""

from typing import Dict, List, Tuple, Optional, Set
import re

class ClinicalKnowledgeBase:
    """
    Comprehensive clinical knowledge base for nursing decision support
    Based on standard nursing references and NCLEX content
    """
    
    def __init__(self):
        # Normal ranges for vital signs and lab values
        self.NORMAL_RANGES = {
            # Vital Signs
            'heart_rate': {
                'adult': (60, 100),
                'pediatric': (80, 120),
                'infant': (100, 160),
                'unit': 'bpm',
                'critical_low': 50,
                'critical_high': 150
            },
            'respiratory_rate': {
                'adult': (12, 20),
                'pediatric': (20, 30),
                'infant': (30, 60),
                'unit': 'breaths/min',
                'critical_low': 10,
                'critical_high': 30
            },
            'blood_pressure_systolic': {
                'adult': (90, 140),
                'unit': 'mmHg',
                'critical_low': 80,
                'critical_high': 180
            },
            'blood_pressure_diastolic': {
                'adult': (60, 90),
                'unit': 'mmHg',
                'critical_low': 50,
                'critical_high': 120
            },
            'temperature_celsius': {
                'all': (36.5, 37.5),
                'unit': '°C',
                'fever': 38.0,
                'hypothermia': 35.0
            },
            'oxygen_saturation': {
                'all': (95, 100),
                'copd': (88, 92),  # Different for COPD patients
                'unit': '%',
                'critical_low': 90
            },
            
            # Lab Values
            'blood_glucose': {
                'all': (70, 110),  # General range
                'fasting': (70, 110),
                'random': (70, 140),
                'unit': 'mg/dL',
                'hypoglycemia': 70,
                'severe_hypoglycemia': 54,
                'hyperglycemia': 180,
                'critical_low': 54,
                'critical_high': 400
            },
            'hemoglobin': {
                'male': (13.5, 17.5),
                'female': (12.0, 16.0),
                'unit': 'g/dL',
                'critical_low': 7.0
            },
            'white_blood_cells': {
                'all': (4500, 11000),
                'unit': 'cells/μL',
                'neutropenia': 1500,
                'leukocytosis': 11000
            },
            'platelets': {
                'all': (150000, 400000),
                'unit': 'cells/μL',
                'critical_low': 50000
            },
            'potassium': {
                'all': (3.5, 5.0),
                'unit': 'mEq/L',
                'critical_low': 2.5,
                'critical_high': 6.5
            },
            'sodium': {
                'all': (135, 145),
                'unit': 'mEq/L',
                'critical_low': 120,
                'critical_high': 160
            },
            'creatinine': {
                'male': (0.7, 1.3),
                'female': (0.6, 1.1),
                'unit': 'mg/dL'
            },
            'inr': {
                'normal': (0.8, 1.2),
                'therapeutic': (2.0, 3.0),  # For anticoagulation
                'unit': 'ratio',
                'critical_high': 5.0
            }
        }
        
        # Medication effects and considerations
        self.MEDICATION_EFFECTS = {
            'beta_blockers': {
                'class_examples': ['metoprolol', 'atenolol', 'propranolol', 'carvedilol'],
                'primary_effects': ['decreased_heart_rate', 'decreased_blood_pressure'],
                'monitor': ['heart_rate', 'blood_pressure'],
                'hold_parameters': {
                    'heart_rate': 60,  # Hold if HR < 60
                    'systolic_bp': 90   # Hold if SBP < 90
                },
                'side_effects': ['bradycardia', 'hypotension', 'fatigue', 'bronchospasm'],
                'contraindications': ['heart_block', 'severe_bradycardia', 'asthma']
            },
            'ace_inhibitors': {
                'class_examples': ['lisinopril', 'enalapril', 'captopril'],
                'primary_effects': ['decreased_blood_pressure', 'cardioprotective'],
                'monitor': ['blood_pressure', 'potassium', 'creatinine'],
                'side_effects': ['dry_cough', 'hyperkalemia', 'angioedema'],
                'teaching': ['report_persistent_cough', 'avoid_salt_substitutes']
            },
            'diuretics': {
                'loop': {
                    'examples': ['furosemide', 'bumetanide'],
                    'effects': ['potassium_loss', 'volume_depletion'],
                    'monitor': ['potassium', 'blood_pressure', 'urine_output']
                },
                'potassium_sparing': {
                    'examples': ['spironolactone'],
                    'effects': ['potassium_retention'],
                    'monitor': ['potassium', 'renal_function']
                }
            },
            'anticoagulants': {
                'warfarin': {
                    'monitor': ['inr', 'bleeding_signs'],
                    'therapeutic_inr': (2.0, 3.0),
                    'antidote': 'vitamin_k',
                    'interactions': ['many_foods', 'many_drugs']
                },
                'heparin': {
                    'monitor': ['ptt', 'platelets'],
                    'antidote': 'protamine_sulfate',
                    'complications': ['hit', 'bleeding']
                }
            },
            'insulin': {
                'rapid_acting': {
                    'examples': ['lispro', 'aspart'],
                    'onset': '15_minutes',
                    'peak': '1_hour',
                    'duration': '4_hours'
                },
                'regular': {
                    'onset': '30_minutes',
                    'peak': '2_3_hours',
                    'duration': '6_hours'
                },
                'monitor': ['blood_glucose', 'hypoglycemia_signs'],
                'hypoglycemia_treatment': '15_grams_carbs'
            },
            'opioids': {
                'examples': ['morphine', 'fentanyl', 'hydrocodone'],
                'primary_effects': ['pain_relief', 'respiratory_depression'],
                'monitor': ['respiratory_rate', 'sedation_level', 'pain_score'],
                'hold_parameters': {
                    'respiratory_rate': 12  # Hold if RR < 12
                },
                'antidote': 'naloxone',
                'side_effects': ['constipation', 'sedation', 'respiratory_depression']
            }
        }
        
        # Clinical patterns and decision rules
        self.CLINICAL_PATTERNS = {
            'hypoglycemia': {
                'symptoms': ['shaky', 'sweaty', 'confused', 'hungry', 'irritable'],
                'glucose_level': '<70',
                'severe_level': '<54',
                'immediate_intervention': 'give_15g_carbs',
                'recheck_time': '15_minutes',
                'priority': 'life_threat'
            },
            'hyperglycemia': {
                'symptoms': ['polyuria', 'polydipsia', 'polyphagia', 'fatigue'],
                'glucose_level': '>180',
                'dka_signs': ['fruity_breath', 'kussmaul_respirations', 'dehydration'],
                'intervention': 'insulin_per_protocol',
                'priority': 'urgent'
            },
            'myocardial_infarction': {
                'symptoms': ['chest_pain', 'radiation_to_arm', 'diaphoresis', 'nausea'],
                'interventions': ['oxygen', 'aspirin', 'nitroglycerin', 'morphine'],
                'mnemonic': 'MONA',
                'priority': 'life_threat'
            },
            'stroke': {
                'assessment': 'fast',
                'symptoms': ['facial_droop', 'arm_weakness', 'speech_difficulty'],
                'time_critical': 'true',
                'intervention_window': '3_hours_tpa',
                'priority': 'life_threat'
            },
            'sepsis': {
                'sirs_criteria': ['temp_abnormal', 'hr_>90', 'rr_>20', 'wbc_abnormal'],
                'signs': ['hypotension', 'altered_mental_status', 'decreased_urine_output'],
                'interventions': ['fluids', 'antibiotics', 'cultures'],
                'priority': 'life_threat'
            },
            'gi_bleed': {
                'upper_gi': {
                    'signs': ['hematemesis', 'coffee_ground_emesis', 'melena'],
                    'interventions': ['iv_access_large_bore', 'type_crossmatch', 'npo']
                },
                'lower_gi': {
                    'signs': ['hematochezia', 'bright_red_blood'],
                    'interventions': ['monitor_vitals', 'iv_fluids']
                },
                'priority': 'life_threat'
            }
        }
        
        # Nursing priorities and interventions
        self.NURSING_PRIORITIES = {
            'abc_emergencies': {
                'airway': ['stridor', 'choking', 'anaphylaxis', 'obstruction'],
                'breathing': ['respiratory_distress', 'hypoxia', 'pneumothorax'],
                'circulation': ['hemorrhage', 'shock', 'cardiac_arrest']
            },
            'safety_concerns': {
                'fall_risk': ['confusion', 'weakness', 'medications', 'age'],
                'infection_risk': ['immunosuppression', 'invasive_devices', 'wounds'],
                'violence_risk': ['agitation', 'psychosis', 'substance_abuse']
            },
            'maslow_physical': {
                'oxygenation': 'immediate',
                'fluid_balance': 'hours',
                'nutrition': 'days',
                'elimination': 'hours',
                'pain': 'hours_to_days',
                'sleep': 'days'
            }
        }
        
        # Teaching points and patient education
        self.PATIENT_TEACHING = {
            'medication_compliance': {
                'correct': [
                    'take_as_prescribed',
                    'dont_skip_doses',
                    'report_side_effects',
                    'keep_appointments'
                ],
                'incorrect': [
                    'skip_when_feeling_better',
                    'double_dose_if_missed',
                    'share_medications',
                    'stop_without_telling_provider'
                ]
            },
            'disease_management': {
                'diabetes': {
                    'correct': [
                        'monitor_blood_glucose_regularly',
                        'rotate_injection_sites',
                        'carry_quick_sugar',
                        'check_feet_daily'
                    ],
                    'incorrect': [
                        'skip_insulin_when_not_eating',
                        'soak_feet_in_hot_water',
                        'ignore_minor_wounds'
                    ]
                },
                'heart_failure': {
                    'correct': [
                        'weigh_daily_same_time',
                        'limit_sodium_2g',
                        'report_weight_gain_3lb',
                        'take_medications_as_prescribed'
                    ],
                    'incorrect': [
                        'increase_salt_for_taste',
                        'skip_diuretic_when_going_out',
                        'ignore_swelling'
                    ]
                }
            }
        }
    
    def is_value_normal(self, parameter: str, value: float, 
                       context: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Check if a value is within normal range
        Returns (is_normal, explanation)
        """
        if parameter not in self.NORMAL_RANGES:
            return (None, f"Unknown parameter: {parameter}")
        
        ranges = self.NORMAL_RANGES[parameter]
        
        # Determine which range to use based on context
        if context:
            age_group = context.get('age_group', 'adult')
            gender = context.get('gender', 'all')
            conditions = context.get('conditions', [])
            
            # Special case for COPD and O2 sat
            if parameter == 'oxygen_saturation' and 'copd' in conditions:
                range_key = 'copd'
            elif age_group in ranges:
                range_key = age_group
            elif gender in ranges:
                range_key = gender
            else:
                range_key = 'all' if 'all' in ranges else 'adult'
        else:
            range_key = 'all' if 'all' in ranges else 'adult'
        
        if range_key not in ranges:
            return (None, f"No range defined for {range_key}")
        
        normal_range = ranges[range_key]
        if isinstance(normal_range, tuple):
            is_normal = normal_range[0] <= value <= normal_range[1]
            
            # Check if critical
            if 'critical_low' in ranges and value < ranges['critical_low']:
                return (False, f"CRITICAL LOW: {value} {ranges.get('unit', '')} (normal: {normal_range[0]}-{normal_range[1]})")
            elif 'critical_high' in ranges and value > ranges['critical_high']:
                return (False, f"CRITICAL HIGH: {value} {ranges.get('unit', '')} (normal: {normal_range[0]}-{normal_range[1]})")
            elif not is_normal:
                if value < normal_range[0]:
                    return (False, f"Low: {value} {ranges.get('unit', '')} (normal: {normal_range[0]}-{normal_range[1]})")
                else:
                    return (False, f"High: {value} {ranges.get('unit', '')} (normal: {normal_range[0]}-{normal_range[1]})")
            else:
                return (True, f"Normal: {value} {ranges.get('unit', '')} (range: {normal_range[0]}-{normal_range[1]})")
    
    def get_medication_considerations(self, medication_class: str) -> Dict:
        """Get important considerations for a medication class"""
        return self.MEDICATION_EFFECTS.get(medication_class, {})
    
    def identify_clinical_pattern(self, symptoms: List[str], 
                                 vital_signs: Dict[str, float]) -> List[Tuple[str, Dict]]:
        """Identify potential clinical patterns based on symptoms and vitals"""
        matches = []
        
        for pattern_name, pattern_data in self.CLINICAL_PATTERNS.items():
            # Check symptom matches
            pattern_symptoms = pattern_data.get('symptoms', [])
            symptom_matches = sum(1 for s in symptoms 
                                if any(ps in s.lower() for ps in pattern_symptoms))
            
            # Check vital sign criteria
            if pattern_name == 'hypoglycemia' and 'blood_glucose' in vital_signs:
                if vital_signs['blood_glucose'] < 70:
                    matches.append((pattern_name, pattern_data))
            elif pattern_name == 'sepsis':
                # Check SIRS criteria
                sirs_count = 0
                if 'temperature_celsius' in vital_signs:
                    if vital_signs['temperature_celsius'] < 36 or vital_signs['temperature_celsius'] > 38:
                        sirs_count += 1
                if 'heart_rate' in vital_signs and vital_signs['heart_rate'] > 90:
                    sirs_count += 1
                if 'respiratory_rate' in vital_signs and vital_signs['respiratory_rate'] > 20:
                    sirs_count += 1
                if sirs_count >= 2:
                    matches.append((pattern_name, pattern_data))
            elif symptom_matches >= len(pattern_symptoms) * 0.5:  # At least 50% match
                matches.append((pattern_name, pattern_data))
        
        return sorted(matches, key=lambda x: x[1].get('priority') == 'life_threat', reverse=True)
    
    def is_intervention_appropriate(self, intervention: str, 
                                  clinical_context: Dict) -> Tuple[bool, str]:
        """
        Determine if an intervention is appropriate given the clinical context
        Returns (is_appropriate, reasoning)
        """
        # This would be expanded with more complex logic
        medications = clinical_context.get('medications', [])
        conditions = clinical_context.get('conditions', [])
        vital_signs = clinical_context.get('vital_signs', {})
        
        intervention_lower = intervention.lower()
        
        # Check for contraindications
        if 'high flow oxygen' in intervention_lower and 'copd' in conditions:
            return (False, "High flow oxygen contraindicated in COPD - can suppress respiratory drive")
        
        if 'beta blocker' in intervention_lower:
            hr = vital_signs.get('heart_rate')
            if hr and hr < 60:
                return (False, f"Hold beta blocker - HR {hr} < 60")
        
        # More rules would be added here
        
        return (True, "No contraindications identified")

# Singleton instance
_knowledge_base = None

def get_knowledge_base() -> ClinicalKnowledgeBase:
    """Get or create the clinical knowledge base singleton"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = ClinicalKnowledgeBase()
    return _knowledge_base

if __name__ == "__main__":
    # Test the knowledge base
    kb = get_knowledge_base()
    
    print("Clinical Knowledge Base Test")
    print("="*50)
    
    # Test normal values
    print("\nTesting Normal Values:")
    test_values = [
        ('heart_rate', 52),
        ('heart_rate', 75),
        ('blood_glucose', 52),
        ('blood_glucose', 85),
        ('respiratory_rate', 18),
        ('oxygen_saturation', 92)
    ]
    
    for param, value in test_values:
        is_normal, explanation = kb.is_value_normal(param, value)
        print(f"{param} = {value}: {explanation}")
    
    # Test clinical pattern recognition
    print("\nTesting Clinical Pattern Recognition:")
    symptoms = ['shaky', 'sweaty', 'confused']
    vitals = {'blood_glucose': 52}
    patterns = kb.identify_clinical_pattern(symptoms, vitals)
    for pattern_name, pattern_data in patterns:
        print(f"Identified: {pattern_name} (Priority: {pattern_data.get('priority')})")
        print(f"  Intervention: {pattern_data.get('immediate_intervention')}")