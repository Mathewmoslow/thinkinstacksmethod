#!/usr/bin/env python3
"""
Extract case study questions from HTML and convert to TISM format
"""

import json
import re
from typing import Dict, List

def extract_cases_from_html():
    """Extract case study questions from the HTML JavaScript"""
    
    cases_data = {
        "cases": {
            "1": {
                "title": "The Kidney Stone Crisis",
                "patient_context": {
                    "name": "Robert Chen, 55-year-old male",
                    "history": "HTN x5 years, previous kidney stone 10 years ago",
                    "current": "Software engineer, high stress, minimal water intake"
                },
                "questions": [
                    {
                        "id": "case1_q1",
                        "scenario": "Initial Presentation - 3:00 AM: Robert arrives at the ED after being awakened from sleep with severe right flank pain. His wife Linda (a nurse) drove him in after he vomited from the pain intensity. He's pacing the triage area, unable to find a comfortable position. Recent History: Similar but milder pain 2 weeks ago that resolved with ibuprofen. Yesterday he worked a 14-hour day, drinking only coffee and one energy drink. Physical Exam: Diaphoretic, restless, right CVA tenderness. VS: BP 165/95, HR 108, RR 22, Temp 98.6°F, O2 sat 98% RA",
                        "stem": "What is your FIRST priority action?",
                        "options": {
                            "A": "Obtain stat KUB x-ray to confirm kidney stone",
                            "B": "Administer ketorolac 30mg IV for pain relief",
                            "C": "Insert 18G IV and send urine for urinalysis",
                            "D": "Give sublingual nitroglycerin for elevated BP"
                        },
                        "correct_answers": ["B"],
                        "rationale": "The patient is in severe pain (9/10). Pain management is the immediate priority.",
                        "format": "single",
                        "question_type": "priority"
                    },
                    {
                        "id": "case1_q2", 
                        "scenario": "30 minutes later: After ketorolac, Robert's pain is 6/10. His wife mentions he takes calcium supplements and high-dose vitamin C daily 'for health.' UA results: RBC >50/hpf, WBC 5-10/hpf, no bacteria, calcium oxalate crystals present. CT scan: 7mm stone at right ureteropelvic junction with moderate hydronephrosis. Current VS: BP 148/88, HR 96",
                        "stem": "What is the next priority?",
                        "options": {
                            "A": "Consult urology for immediate lithotripsy",
                            "B": "Start IV fluids at 200 mL/hr",
                            "C": "Give tamsulosin 0.4mg PO",
                            "D": "Insert Foley catheter for accurate I&O"
                        },
                        "correct_answers": ["B"],
                        "rationale": "IV fluids help flush the stone and prevent further kidney damage from obstruction.",
                        "format": "single",
                        "question_type": "priority"
                    },
                    {
                        "id": "case1_q3",
                        "scenario": "2 hours later - Deterioration: Robert suddenly develops severe nausea and vomits twice. He's now having chills and says the pain is 'unbearable' despite medication. His wife notes he looks 'gray.' New assessment: Rigors, appears toxic. VS: BP 92/58, HR 122, RR 26, Temp 102.8°F. Labs drawn: Pending",
                        "stem": "What is your immediate action?",
                        "options": {
                            "A": "Give ondansetron 4mg IV for nausea",
                            "B": "Increase IV fluid rate and call rapid response",
                            "C": "Administer morphine 4mg IV for pain",
                            "D": "Obtain blood and urine cultures"
                        },
                        "correct_answers": ["B"],
                        "rationale": "The patient is developing septic shock (hypotension, tachycardia, fever). This requires immediate fluid resuscitation and rapid response activation.",
                        "format": "single",
                        "question_type": "priority"
                    }
                ]
            },
            "2": {
                "title": "The GI Bleed Spiral",
                "patient_context": {
                    "name": "Margaret Williams, 68-year-old female",
                    "history": "RA x15 years, chronic NSAID use, GERD, previous H. pylori",
                    "current": "Retired teacher, lives alone"
                },
                "questions": [
                    {
                        "id": "case2_q1",
                        "scenario": "Emergency Department - 2:30 PM: Margaret was brought in by her daughter after vomiting 'coffee grounds' twice this morning. She's been having epigastric pain for 3 days, which she attributed to 'indigestion.' This morning she felt dizzy standing up. Physical Exam: Pale, cool skin, epigastric tenderness. VS: BP 88/52, HR 118, RR 24, Temp 98.2°F, O2 sat 97% RA. Orthostatic vitals: Standing BP 70/40, HR 145",
                        "stem": "What is your immediate priority?",
                        "options": {
                            "A": "Obtain CBC and type & screen",
                            "B": "Insert two large-bore IVs and start fluid resuscitation",
                            "C": "Give pantoprazole 80mg IV bolus",
                            "D": "Call GI for emergent endoscopy"
                        },
                        "correct_answers": ["B"],
                        "rationale": "The patient is in hypovolemic shock from GI bleeding. Immediate IV access and fluid resuscitation are critical.",
                        "format": "single",
                        "question_type": "priority"
                    },
                    {
                        "id": "case2_q2",
                        "scenario": "30 minutes later: Two 16G IVs placed, 1L NS infused. Margaret's BP improved to 102/64. Labs return: Hgb 6.8 (baseline 12.2), Hct 20.4%, Platelets 180K, INR 1.2. Type & Screen: A positive, no antibodies. She suddenly vomits bright red blood and becomes more confused. VS: BP 78/45, HR 134",
                        "stem": "What is the next critical action?",
                        "options": {
                            "A": "Continue aggressive fluid resuscitation",
                            "B": "Transfuse 2 units packed RBCs immediately",
                            "C": "Insert NG tube for gastric lavage",
                            "D": "Prepare for emergency intubation"
                        },
                        "correct_answers": ["B"],
                        "rationale": "With Hgb of 6.8 and active bleeding with hemodynamic instability, immediate blood transfusion is critical.",
                        "format": "single",
                        "question_type": "priority"
                    }
                ]
            },
            "3": {
                "title": "The Hip Fracture Cascade",
                "patient_context": {
                    "name": "Dorothy Thompson, 82-year-old female",
                    "history": "Osteoporosis, AFib on warfarin, HTN",
                    "current": "Lives independently with home aide"
                },
                "questions": [
                    {
                        "id": "case3_q1",
                        "scenario": "Post-Op Day 1 - ICU: Dorothy underwent successful hip pinning yesterday. Surgery was complicated by significant blood loss requiring 3 units pRBCs. She's been stable overnight but this morning the nurse notices increased drainage from the surgical site. Physical Exam: Surgical dressing saturated with blood. VS: BP 92/58, HR 105, RR 18, Temp 98.9°F. Labs: Hgb 8.2 (post-op was 9.8), INR 2.8",
                        "stem": "What is your immediate concern and action?",
                        "options": {
                            "A": "Normal post-operative bleeding - monitor closely",
                            "B": "Warfarin reversal and surgical exploration",
                            "C": "Increase compression dressing and elevate leg",
                            "D": "Transfuse 2 units pRBCs and continue observation"
                        },
                        "correct_answers": ["B"],
                        "rationale": "Significant post-operative bleeding with elevated INR requires immediate warfarin reversal and likely surgical exploration.",
                        "format": "single",
                        "question_type": "priority"
                    }
                ]
            },
            "4": {
                "title": "Bowel Obstruction Blues",
                "patient_context": {
                    "name": "James Martinez, 74-year-old male",
                    "history": "Colon CA s/p resection, DM2, chronic pain on opioids",
                    "current": "Limited mobility, recent pneumonia"
                },
                "questions": [
                    {
                        "id": "case4_q1",
                        "scenario": "Emergency Department: James presents with 5 days of no bowel movements, progressive abdominal distension, and vomiting. He stopped eating 2 days ago due to nausea. His wife reports he's been taking extra pain medication for worsening back pain. Physical Exam: Massively distended abdomen, high-pitched bowel sounds, mild tenderness. VS: BP 118/74, HR 98, RR 22, Temp 99.2°F. Recent intake: Minimal fluids, no solid food x48 hours",
                        "stem": "What is the most likely diagnosis and immediate priority?",
                        "options": {
                            "A": "Opioid-induced constipation - give laxatives",
                            "B": "Small bowel obstruction - NPO, NG tube, IV fluids",
                            "C": "Diabetic gastroparesis - check glucose and give metoclopramide",
                            "D": "Recurrent colon cancer - urgent CT scan"
                        },
                        "correct_answers": ["B"],
                        "rationale": "Clinical presentation is classic for small bowel obstruction in a patient with prior abdominal surgery. Immediate decompression with NG tube and fluid resuscitation are priorities.",
                        "format": "single",
                        "question_type": "priority"
                    }
                ]
            },
            "5": {
                "title": "UTI to Multi-Organ Failure",
                "patient_context": {
                    "name": "Helen Park, 79-year-old female",
                    "history": "CKD Stage 3, CHF, DM2, recurrent UTIs",
                    "current": "Assisted living, recent Foley removal"
                },
                "questions": [
                    {
                        "id": "case5_q1",
                        "scenario": "Emergency Department: Helen was brought in by her daughter for 3 days of dysuria, frequency, and general malaise. Today she became confused and had decreased urine output. The assisted living facility reports she's been drinking poorly and seems 'not herself.' Physical Exam: Confused, dry mucous membranes, suprapubic tenderness. VS: BP 98/58, HR 108, RR 24, Temp 101.8°F, O2 sat 94% RA. Quick labs: Glucose 385, Cr 3.2 (baseline 1.8)",
                        "stem": "What is your primary concern and immediate action?",
                        "options": {
                            "A": "Simple UTI - start ciprofloxacin and discharge",
                            "B": "Urosepsis with AKI - IV antibiotics, fluids, admit",
                            "C": "Diabetic ketoacidosis - insulin and fluid resuscitation",
                            "D": "CHF exacerbation - diuretics and cardiology consult"
                        },
                        "correct_answers": ["B"],
                        "rationale": "The combination of UTI symptoms, altered mental status, fever, hypotension, and acute kidney injury suggests urosepsis.",
                        "format": "single",
                        "question_type": "priority"
                    }
                ]
            },
            "6": {
                "title": "The Gallstone Nightmare",
                "patient_context": {
                    "name": "Barbara Johnson, 52-year-old female",
                    "history": "Obesity, DM2, HTN, previous gallbladder attacks",
                    "current": "High stress job, frequent fast food"
                },
                "questions": [
                    {
                        "id": "case6_q1",
                        "scenario": "Emergency Department - 8:45 PM: Barbara presents with severe RUQ pain that started 3 hours after eating a large, fatty meal at a restaurant. The pain is constant, radiates to her right shoulder, and is associated with nausea and vomiting. She's had similar but milder episodes before. Physical Exam: RUQ tenderness, positive Murphy's sign, no jaundice. VS: BP 145/88, HR 102, RR 20, Temp 100.9°F. Pain scale: 9/10",
                        "stem": "What is the most likely diagnosis and next step?",
                        "options": {
                            "A": "Biliary colic - pain control and discharge with follow-up",
                            "B": "Acute cholecystitis - NPO, IV antibiotics, surgery consult",
                            "C": "Peptic ulcer disease - PPI and H. pylori testing",
                            "D": "Myocardial infarction - EKG and cardiac enzymes"
                        },
                        "correct_answers": ["B"],
                        "rationale": "The combination of RUQ pain, positive Murphy's sign, fever, and leukocytosis suggests acute cholecystitis rather than simple biliary colic.",
                        "format": "single",
                        "question_type": "priority"
                    }
                ]
            }
        }
    }
    
    # Convert to list format for TISM testing
    all_questions = []
    for case_num, case_data in cases_data["cases"].items():
        for question in case_data["questions"]:
            # Combine scenario and stem for full context
            full_stem = f"{question['scenario']}\n\n{question['stem']}"
            
            q = {
                "id": question["id"],
                "case_title": case_data["title"],
                "patient_context": case_data["patient_context"],
                "stem": full_stem,
                "options": question["options"],
                "correct_answers": question["correct_answers"],
                "rationale": question["rationale"],
                "format": question["format"],
                "question_type": question["question_type"]
            }
            all_questions.append(q)
    
    return all_questions

def save_case_questions():
    """Save extracted questions to JSON file"""
    questions = extract_cases_from_html()
    
    output = {
        "source": "Clinical Case Studies",
        "total_questions": len(questions),
        "question_types": ["priority", "action"],
        "questions": questions
    }
    
    with open('case_study_questions.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Extracted {len(questions)} case study questions")
    
    # Show sample
    print("\nSample question:")
    print(f"Case: {questions[0]['case_title']}")
    print(f"Stem: {questions[0]['stem'][:200]}...")
    print(f"Correct: {questions[0]['correct_answers']}")

if __name__ == "__main__":
    save_case_questions()