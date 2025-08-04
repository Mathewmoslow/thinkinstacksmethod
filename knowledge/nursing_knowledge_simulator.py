#!/usr/bin/env python3
"""
Comprehensive Nursing Knowledge Simulator
Simulates the knowledge a well-prepared nursing student would have
"""

import re
import json
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClinicalKnowledge:
    """Represents clinical knowledge about a topic"""
    topic: str
    category: str
    facts: Dict[str, any]
    priority_implications: Dict[str, int]
    contraindications: List[str]
    urgent_findings: List[str]

class NursingKnowledgeSimulator:
    """Simulates comprehensive nursing knowledge"""
    
    def __init__(self):
        # Initialize all knowledge domains
        self._init_vital_signs_knowledge()
        self._init_medication_knowledge()
        self._init_disease_knowledge()
        self._init_assessment_knowledge()
        self._init_intervention_knowledge()
        self._init_priority_rules()
    
    def _init_vital_signs_knowledge(self):
        """Initialize vital signs knowledge"""
        self.vital_signs = {
            'heart_rate': {
                'normal_adult': (60, 100),
                'bradycardia': lambda x: x < 60,
                'tachycardia': lambda x: x > 100,
                'critical_low': 40,
                'critical_high': 150,
                'concerning_patterns': {
                    'with_beta_blocker': lambda x: x < 60,  # Hold medication
                    'with_digoxin': lambda x: x < 60,  # Hold medication
                    'post_op': lambda x: x > 120,  # Possible hemorrhage
                    'with_symptoms': lambda x: x > 130,  # Symptomatic tachycardia
                }
            },
            'blood_pressure': {
                'normal_adult': (90, 140, 60, 90),  # SBP min/max, DBP min/max
                'hypotension': lambda s, d: s < 90,
                'hypertension': lambda s, d: s > 140 or d > 90,
                'hypertensive_crisis': lambda s, d: s > 180 or d > 120,
                'concerning_patterns': {
                    'post_op': lambda s, d: s < 90,  # Possible hemorrhage
                    'with_ace_inhibitor': lambda s, d: s < 90,  # Hold medication
                    'orthostatic': lambda drop: drop > 20,  # Significant drop
                }
            },
            'respiratory_rate': {
                'normal_adult': (12, 20),
                'bradypnea': lambda x: x < 12,
                'tachypnea': lambda x: x > 20,
                'critical': lambda x: x < 10 or x > 30,
                'concerning_patterns': {
                    'with_opioids': lambda x: x < 12,  # Respiratory depression
                    'with_copd': lambda x: x > 24,  # Possible exacerbation
                }
            },
            'oxygen_saturation': {
                'normal': (95, 100),
                'copd_target': (88, 92),
                'hypoxemia': lambda x: x < 90,
                'severe_hypoxemia': lambda x: x < 85,
                'concerning_patterns': {
                    'room_air': lambda x: x < 92,
                    'on_oxygen': lambda x: x < 90,
                    'copd': lambda x: x < 88 or x > 92,
                }
            },
            'temperature': {
                'normal_f': (97.0, 99.5),
                'fever': lambda x: x > 100.4,
                'hypothermia': lambda x: x < 96.0,
                'concerning_patterns': {
                    'post_op': lambda x: x > 101.0,  # Possible infection
                    'neutropenic': lambda x: x > 100.4,  # Medical emergency
                    'with_antibiotics': lambda x: x > 102.0,  # Treatment failure
                }
            },
            'blood_glucose': {
                'normal_fasting': (70, 110),
                'hypoglycemia': lambda x: x < 70,
                'severe_hypoglycemia': lambda x: x < 54,
                'hyperglycemia': lambda x: x > 180,
                'critical_values': {
                    'unconscious_risk': lambda x: x < 40,
                    'dka_risk': lambda x: x > 250,
                    'hhs_risk': lambda x: x > 600,
                }
            }
        }
    
    def _init_medication_knowledge(self):
        """Initialize medication knowledge"""
        self.medications = {
            'beta_blockers': {
                'examples': ['metoprolol', 'atenolol', 'propranolol'],
                'class': 'cardiovascular',
                'effects': {
                    'desired': ['decreased_hr', 'decreased_bp', 'reduced_workload'],
                    'adverse': ['bradycardia', 'hypotension', 'bronchospasm', 'fatigue']
                },
                'monitoring': ['heart_rate', 'blood_pressure'],
                'hold_if': {
                    'hr': lambda x: x < 60,
                    'sbp': lambda x: x < 90
                },
                'contraindications': ['asthma', 'heart_block', 'severe_bradycardia'],
                'priority_level': {
                    'bradycardia': 1000,  # Life threat
                    'mild_fatigue': 200   # Low priority
                }
            },
            'ace_inhibitors': {
                'examples': ['lisinopril', 'enalapril', 'captopril'],
                'suffix': 'pril',
                'effects': {
                    'desired': ['decreased_bp', 'cardioprotective', 'renoprotective'],
                    'adverse': ['cough', 'hyperkalemia', 'angioedema', 'hypotension']
                },
                'monitoring': ['blood_pressure', 'potassium', 'creatinine'],
                'priority_level': {
                    'angioedema': 1200,  # Emergency
                    'dry_cough': 300,    # Annoying but not urgent
                    'hyperkalemia': 900  # Urgent
                }
            },
            'opioids': {
                'examples': ['morphine', 'fentanyl', 'oxycodone'],
                'effects': {
                    'desired': ['pain_relief', 'sedation'],
                    'adverse': ['respiratory_depression', 'constipation', 'sedation', 'addiction']
                },
                'monitoring': ['respiratory_rate', 'pain_level', 'sedation_scale'],
                'hold_if': {
                    'rr': lambda x: x < 12,
                    'sedation': lambda x: x > 3  # On sedation scale
                },
                'antidote': 'naloxone',
                'priority_level': {
                    'respiratory_depression': 1100,  # Life threat
                    'constipation': 400             # Important but not urgent
                }
            },
            'anticoagulants': {
                'warfarin': {
                    'monitoring': 'INR',
                    'therapeutic_range': (2.0, 3.0),
                    'antidote': 'vitamin_k',
                    'bleeding_risk': lambda inr: inr > 4.0,
                    'priority_level': {
                        'active_bleeding': 1200,
                        'inr_>5': 1000,
                        'bruising': 600
                    }
                },
                'heparin': {
                    'monitoring': ['PTT', 'platelets'],
                    'antidote': 'protamine_sulfate',
                    'complications': ['HIT', 'bleeding'],
                    'priority_level': {
                        'thrombocytopenia': 1000,  # Possible HIT
                        'active_bleeding': 1200
                    }
                }
            },
            'insulin': {
                'types': {
                    'rapid': {'onset': 15, 'peak': 60, 'duration': 240},
                    'regular': {'onset': 30, 'peak': 150, 'duration': 360},
                    'nph': {'onset': 120, 'peak': 480, 'duration': 720},
                    'long': {'onset': 120, 'peak': None, 'duration': 1440}
                },
                'hypoglycemia_risk': 'highest_at_peak',
                'mixing_rules': ['clear_before_cloudy', 'regular_before_nph'],
                'priority_level': {
                    'hypoglycemia_symptoms': 1100,
                    'injection_site_rotation': 300
                }
            },
            'diuretics': {
                'loop': {
                    'examples': ['furosemide', 'bumetanide'],
                    'effects': ['potassium_loss', 'volume_depletion'],
                    'monitoring': ['potassium', 'blood_pressure', 'weight'],
                    'priority_level': {
                        'hypokalemia': 900,
                        'dehydration': 800,
                        'mild_dizziness': 500
                    }
                },
                'potassium_sparing': {
                    'examples': ['spironolactone'],
                    'effects': ['potassium_retention'],
                    'monitoring': ['potassium', 'renal_function'],
                    'priority_level': {
                        'hyperkalemia': 1000
                    }
                }
            },
            'antipsychotics': {
                'typical': ['haloperidol', 'chlorpromazine'],
                'atypical': ['olanzapine', 'risperidone', 'quetiapine'],
                'side_effects': {
                    'extrapyramidal': ['dystonia', 'akathisia', 'tardive_dyskinesia'],
                    'metabolic': ['weight_gain', 'diabetes', 'dyslipidemia'],
                    'other': ['sedation', 'orthostatic_hypotension']
                },
                'priority_level': {
                    'acute_dystonia': 1000,  # Emergency
                    'neuroleptic_malignant': 1200,  # Life threat
                    'weight_gain': 300  # Long-term concern
                }
            }
        }
    
    def _init_disease_knowledge(self):
        """Initialize disease/condition knowledge"""
        self.diseases = {
            'diabetes': {
                'types': ['type_1', 'type_2', 'gestational'],
                'complications': {
                    'acute': ['DKA', 'HHS', 'hypoglycemia'],
                    'chronic': ['neuropathy', 'retinopathy', 'nephropathy']
                },
                'emergency_signs': {
                    'hypoglycemia': ['shaky', 'sweaty', 'confused', 'unconscious'],
                    'DKA': ['fruity_breath', 'kussmaul_respirations', 'altered_mental'],
                    'HHS': ['extreme_hyperglycemia', 'dehydration', 'altered_mental']
                },
                'priority_levels': {
                    'blood_sugar_<54': 1100,
                    'blood_sugar_>400': 900,
                    'ketones_present': 1000
                }
            },
            'heart_failure': {
                'types': ['left_sided', 'right_sided', 'biventricular'],
                'signs': {
                    'left': ['dyspnea', 'orthopnea', 'crackles', 'S3_gallop'],
                    'right': ['edema', 'JVD', 'hepatomegaly', 'weight_gain']
                },
                'monitoring': ['daily_weight', 'I&O', 'lung_sounds', 'edema'],
                'critical_findings': {
                    'weight_gain_3lb': 800,
                    'increasing_dyspnea': 900,
                    'pink_frothy_sputum': 1100  # Pulmonary edema
                }
            },
            'COPD': {
                'types': ['emphysema', 'chronic_bronchitis'],
                'oxygen_rules': {
                    'target_spo2': (88, 92),
                    'max_flow': 2,  # L/min to avoid CO2 retention
                    'warning': 'high_flow_suppresses_drive'
                },
                'exacerbation_signs': ['increased_dyspnea', 'change_sputum', 'increased_cough'],
                'priority_levels': {
                    'accessory_muscle_use': 1000,
                    'cyanosis': 1100,
                    'altered_mental': 1100
                }
            },
            'stroke': {
                'types': ['ischemic', 'hemorrhagic'],
                'FAST_assessment': {
                    'F': 'facial_droop',
                    'A': 'arm_drift',
                    'S': 'speech_difficulty',
                    'T': 'time_critical'
                },
                'tPA_window': 180,  # minutes
                'contraindications_tPA': ['recent_surgery', 'bleeding', 'hemorrhagic_stroke'],
                'priority_levels': {
                    'within_tPA_window': 1200,
                    'increasing_deficits': 1100,
                    'stable_deficits': 700
                }
            },
            'MI': {
                'types': ['STEMI', 'NSTEMI'],
                'classic_symptoms': ['chest_pain', 'radiation', 'diaphoresis', 'nausea'],
                'atypical_symptoms': ['jaw_pain', 'back_pain', 'fatigue', 'indigestion'],
                'interventions': {
                    'MONA': ['morphine', 'oxygen', 'nitroglycerin', 'aspirin'],
                    'time_critical': ['door_to_balloon_90min', 'thrombolytics']
                },
                'priority_levels': {
                    'active_chest_pain': 1100,
                    'ST_elevation': 1200,
                    'resolved_pain': 800
                }
            },
            'psychiatric_emergencies': {
                'suicide_risk': {
                    'low': ['passive_ideation', 'no_plan'],
                    'moderate': ['active_ideation', 'vague_plan'],
                    'high': ['specific_plan', 'means_available', 'intent'],
                    'imminent': ['attempt_in_progress', 'stated_intent_now']
                },
                'violence_risk': {
                    'predictors': ['past_violence', 'command_hallucinations', 'substance_use'],
                    'de_escalation': ['calm_voice', 'personal_space', 'active_listening']
                },
                'priority_levels': {
                    'active_suicide_plan': 1100,
                    'command_hallucinations': 1000,
                    'aggressive_behavior': 1000,
                    'passive_thoughts': 600
                }
            }
        }
    
    def _init_assessment_knowledge(self):
        """Initialize assessment knowledge"""
        self.assessments = {
            'neurological': {
                'pupil_assessment': {
                    'normal': 'PERRLA',
                    'abnormal': {
                        'fixed_dilated': 1100,  # Brain death/herniation
                        'pinpoint': 900,  # Opioid OD or pontine lesion
                        'unequal': 1000,  # Increased ICP
                        'sluggish': 800
                    }
                },
                'LOC_changes': {
                    'alert': 0,
                    'lethargic': 600,
                    'obtunded': 800,
                    'stuporous': 900,
                    'comatose': 1100
                },
                'motor_assessment': {
                    'normal_strength': '5/5',
                    'weakness_levels': {
                        '0/5': 1000,  # Paralysis
                        '1/5': 900,
                        '2/5': 800,
                        '3/5': 700,
                        '4/5': 600
                    }
                }
            },
            'respiratory': {
                'breath_sounds': {
                    'normal': ['clear', 'vesicular'],
                    'abnormal': {
                        'crackles': 800,  # Fluid
                        'wheezes': 800,  # Narrowing
                        'stridor': 1100,  # Upper airway obstruction
                        'absent': 1100,  # Pneumothorax
                        'diminished': 700
                    }
                },
                'breathing_patterns': {
                    'eupnea': 0,
                    'tachypnea': 700,
                    'bradypnea': 900,
                    'apnea': 1200,
                    'cheyne_stokes': 1000,
                    'kussmaul': 900  # DKA
                }
            },
            'cardiovascular': {
                'heart_sounds': {
                    'normal': ['S1_S2_regular'],
                    'abnormal': {
                        'S3_gallop': 800,  # Heart failure
                        'S4_gallop': 700,  # Hypertension
                        'murmur': 600,
                        'rub': 800,  # Pericarditis
                        'irregular': 800
                    }
                },
                'peripheral_assessment': {
                    'pulses': {
                        'absent': 1100,  # Emergency
                        'weak': 800,
                        'bounding': 700
                    },
                    'capillary_refill': {
                        '>3_seconds': 800,
                        '>5_seconds': 1000
                    }
                }
            },
            'pain': {
                'scale': {
                    '0-3': 400,  # Mild
                    '4-6': 600,  # Moderate
                    '7-10': 800,  # Severe
                    '10_with_vitals_changes': 900  # Severe with physiologic response
                },
                'red_flags': {
                    'chest_pain': 1100,
                    'sudden_severe_headache': 1000,
                    'abdominal_rigid': 900
                }
            }
        }
    
    def _init_intervention_knowledge(self):
        """Initialize intervention knowledge"""
        self.interventions = {
            'emergency': {
                'CPR': {
                    'indications': ['no_pulse', 'unresponsive'],
                    'priority': 1200,
                    'sequence': ['compressions', 'airway', 'breathing']
                },
                'rapid_response': {
                    'criteria': ['significant_vital_changes', 'nurse_concern', 'acute_mental_change'],
                    'priority': 1000
                },
                'code_blue': {
                    'indications': ['cardiac_arrest', 'respiratory_arrest'],
                    'priority': 1200
                }
            },
            'medication_administration': {
                'rights': ['patient', 'drug', 'dose', 'route', 'time', 'documentation'],
                'high_alert': {
                    'insulin': {'double_check': True, 'priority': 900},
                    'heparin': {'double_check': True, 'priority': 900},
                    'chemotherapy': {'double_check': True, 'priority': 1000}
                }
            },
            'safety': {
                'fall_prevention': {
                    'interventions': ['bed_low', 'call_bell', 'non_slip', 'assist_ambulation'],
                    'priority_if_high_risk': 800
                },
                'infection_control': {
                    'standard_precautions': 600,
                    'isolation_types': {
                        'airborne': 900,
                        'droplet': 800,
                        'contact': 700
                    }
                },
                'suicide_precautions': {
                    'one_to_one': 1100,
                    'q15_checks': 900,
                    'remove_sharps': 1000
                }
            }
        }
    
    def _init_priority_rules(self):
        """Initialize priority determination rules"""
        self.priority_rules = {
            'life_threats': {
                'airway_obstruction': 1200,
                'respiratory_failure': 1150,
                'cardiac_arrest': 1200,
                'severe_bleeding': 1100,
                'anaphylaxis': 1200,
                'status_epilepticus': 1100
            },
            'time_critical': {
                'stroke_tPA_window': 1150,
                'MI_door_to_balloon': 1150,
                'hypoglycemia_unconscious': 1100,
                'sepsis_golden_hour': 1100
            },
            'unstable_conditions': {
                'vital_sign_changes': 900,
                'acute_pain_severe': 800,
                'new_onset_symptoms': 800,
                'deteriorating_status': 1000
            },
            'stable_chronic': {
                'controlled_diabetes': 400,
                'stable_COPD': 400,
                'chronic_pain_managed': 500
            }
        }
    
    def assess_clinical_situation(self, description: str) -> Dict[str, any]:
        """
        Assess a clinical situation and return priority information
        This simulates what a knowledgeable nurse would recognize
        """
        assessment = {
            'identified_conditions': [],
            'vital_sign_concerns': [],
            'medication_concerns': [],
            'priority_score': 0,
            'recommended_actions': [],
            'rationale': []
        }
        
        description_lower = description.lower()
        
        # Check for vital sign abnormalities
        vital_patterns = {
            'hr': r'(?:hr|heart rate)[:\s]*(\d+)',
            'bp': r'(?:bp|blood pressure)[:\s]*(\d+)/(\d+)',
            'rr': r'(?:rr|respiratory rate)[:\s]*(\d+)',
            'o2': r'(?:o2 sat|spo2|oxygen saturation)[:\s]*(\d+)',
            'temp': r'(?:temp|temperature)[:\s]*(\d+\.?\d*)',
            'glucose': r'(?:glucose|blood sugar)[:\s]*(\d+)'
        }
        
        for vital_type, pattern in vital_patterns.items():
            match = re.search(pattern, description_lower)
            if match:
                if vital_type == 'hr':
                    hr = int(match.group(1))
                    if hr < 60:
                        assessment['vital_sign_concerns'].append(f'Bradycardia: HR {hr}')
                        assessment['priority_score'] = max(assessment['priority_score'], 900)
                    elif hr > 120:
                        assessment['vital_sign_concerns'].append(f'Tachycardia: HR {hr}')
                        assessment['priority_score'] = max(assessment['priority_score'], 800)
                        if hr > 150:
                            assessment['priority_score'] = 1000
                
                elif vital_type == 'bp':
                    sbp, dbp = int(match.group(1)), int(match.group(2))
                    if sbp < 90:
                        assessment['vital_sign_concerns'].append(f'Hypotension: BP {sbp}/{dbp}')
                        assessment['priority_score'] = max(assessment['priority_score'], 1000)
                    elif sbp > 180 or dbp > 120:
                        assessment['vital_sign_concerns'].append(f'Hypertensive crisis: BP {sbp}/{dbp}')
                        assessment['priority_score'] = max(assessment['priority_score'], 1100)
                
                elif vital_type == 'glucose':
                    glucose = int(match.group(1))
                    if glucose < 70:
                        assessment['vital_sign_concerns'].append(f'Hypoglycemia: glucose {glucose}')
                        assessment['priority_score'] = max(assessment['priority_score'], 1100)
                        assessment['recommended_actions'].append('Give 15g quick carbohydrates')
                    elif glucose > 400:
                        assessment['vital_sign_concerns'].append(f'Severe hyperglycemia: glucose {glucose}')
                        assessment['priority_score'] = max(assessment['priority_score'], 900)
        
        # Check for medication-related concerns
        for med_class, med_info in self.medications.items():
            if any(med in description_lower for med in med_info.get('examples', [])) or med_class in description_lower:
                assessment['identified_conditions'].append(f'On {med_class}')
                
                # Check for concerning side effects
                if 'priority_level' in med_info:
                    for effect, priority in med_info['priority_level'].items():
                        if effect.replace('_', ' ') in description_lower:
                            assessment['medication_concerns'].append(f'{med_class}: {effect}')
                            assessment['priority_score'] = max(assessment['priority_score'], priority)
        
        # Check for disease-specific emergencies
        for disease, disease_info in self.diseases.items():
            if disease in description_lower:
                if 'priority_levels' in disease_info:
                    for finding, priority in disease_info['priority_levels'].items():
                        if finding.replace('_', ' ') in description_lower:
                            assessment['identified_conditions'].append(f'{disease}: {finding}')
                            assessment['priority_score'] = max(assessment['priority_score'], priority)
        
        # Generate rationale
        if assessment['priority_score'] >= 1000:
            assessment['rationale'].append('Life-threatening condition requiring immediate intervention')
        elif assessment['priority_score'] >= 800:
            assessment['rationale'].append('Urgent condition requiring prompt intervention')
        elif assessment['priority_score'] >= 600:
            assessment['rationale'].append('Important finding requiring timely intervention')
        else:
            assessment['rationale'].append('Stable condition requiring routine care')
        
        return assessment
    
    def evaluate_intervention(self, intervention: str, clinical_context: Dict) -> Dict[str, any]:
        """
        Evaluate if an intervention is appropriate given the clinical context
        """
        evaluation = {
            'is_appropriate': True,
            'priority_score': 0,
            'addresses_primary_concern': False,
            'contraindications': [],
            'rationale': []
        }
        
        intervention_lower = intervention.lower()
        
        # Check if intervention addresses identified concerns
        if 'hypoglycemia' in str(clinical_context.get('vital_sign_concerns', [])):
            if any(term in intervention_lower for term in ['carbohydrate', 'glucose', 'sugar', 'juice']):
                evaluation['addresses_primary_concern'] = True
                evaluation['priority_score'] = 1100
                evaluation['rationale'].append('Correctly treats hypoglycemia')
            elif 'assess' in intervention_lower or 'check' in intervention_lower:
                evaluation['priority_score'] = 600
                evaluation['rationale'].append('Assessment when intervention needed')
        
        # Check for contraindications
        if 'COPD' in str(clinical_context.get('identified_conditions', [])):
            if 'high flow oxygen' in intervention_lower or 'high-flow oxygen' in intervention_lower:
                evaluation['is_appropriate'] = False
                evaluation['contraindications'].append('High flow O2 contraindicated in COPD')
                evaluation['priority_score'] = -1000
        
        # Evaluate based on intervention type
        if any(term in intervention_lower for term in ['cpr', 'compressions', 'code']):
            if 'no pulse' in str(clinical_context) or 'cardiac arrest' in str(clinical_context):
                evaluation['priority_score'] = 1200
                evaluation['rationale'].append('Life-saving intervention')
        
        return evaluation

# Create singleton instance
_knowledge_simulator = None

def get_knowledge_simulator() -> NursingKnowledgeSimulator:
    """Get or create the nursing knowledge simulator"""
    global _knowledge_simulator
    if _knowledge_simulator is None:
        _knowledge_simulator = NursingKnowledgeSimulator()
    return _knowledge_simulator

if __name__ == "__main__":
    # Test the knowledge simulator
    simulator = get_knowledge_simulator()
    
    print("Nursing Knowledge Simulator Test")
    print("="*60)
    
    # Test scenarios
    test_scenarios = [
        "Patient on metoprolol with HR 52 and feeling dizzy",
        "Client with blood glucose 45 mg/dL, shaky and sweaty",
        "Post-op patient with BP 85/50 and increased drainage",
        "COPD patient with O2 sat 86% on room air",
        "Patient stating 'I have pills saved and plan to take them tonight'"
    ]
    
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario}")
        assessment = simulator.assess_clinical_situation(scenario)
        print(f"Priority Score: {assessment['priority_score']}")
        print(f"Concerns: {assessment['vital_sign_concerns'] + assessment['medication_concerns']}")
        print(f"Rationale: {assessment['rationale']}")
        if assessment['recommended_actions']:
            print(f"Recommended: {assessment['recommended_actions']}")