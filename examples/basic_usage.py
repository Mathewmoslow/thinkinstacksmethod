#!/usr/bin/env python3
"""Basic usage example for TISM Framework"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tism_tree_final import TISMTreeFinal, StudentQuickReference
from core.nclex_validation_framework import NCLEXQuestion

def main():
    print("=== TISM Basic Usage Example ===\n")
    
    # Print the student reference card
    print("Student Quick Reference:")
    print("-" * 50)
    StudentQuickReference.print_card()
    print("-" * 50)
    
    # Create a TISM instance
    tism = TISMTreeFinal(debug=True)
    
    # Example 1: Clear emergency
    print("\n\nExample 1: Clear Emergency")
    print("=" * 50)
    
    question1 = NCLEXQuestion(
        id="example1",
        stem="A client is found unresponsive with no palpable pulse. What should the nurse do first?",
        options={
            'A': 'Check blood glucose',
            'B': 'Begin chest compressions',
            'C': 'Call for help',
            'D': 'Assess pupils'
        },
        correct_answers={'B'},
        format='single',
        question_type='priority'
    )
    
    prediction = tism.predict(question1)
    print(f"\nQuestion: {question1.stem}")
    print(f"TISM predicts: {prediction}")
    print(f"Correct answer: {question1.correct_answers}")
    print(f"Result: {'✓ Correct' if prediction == question1.correct_answers else '✗ Incorrect'}")
    
    # Example 2: Safety concern
    print("\n\nExample 2: Safety Concern")
    print("=" * 50)
    
    question2 = NCLEXQuestion(
        id="example2",
        stem="A confused elderly client is attempting to climb out of bed. Which action should the nurse take first?",
        options={
            'A': 'Apply physical restraints',
            'B': 'Administer sedative medication',
            'C': 'Lower the bed and ensure safety',
            'D': 'Call the physician'
        },
        correct_answers={'C'},
        format='single',
        question_type='priority'
    )
    
    prediction = tism.predict(question2)
    print(f"\nQuestion: {question2.stem}")
    print(f"TISM predicts: {prediction}")
    print(f"Correct answer: {question2.correct_answers}")
    print(f"Result: {'✓ Correct' if prediction == question2.correct_answers else '✗ Incorrect'}")
    
    # Example 3: SATA question
    print("\n\nExample 3: Select All That Apply (SATA)")
    print("=" * 50)
    
    question3 = NCLEXQuestion(
        id="example3",
        stem="Which of the following are signs of hypoglycemia? Select all that apply.",
        options={
            'A': 'Shakiness',
            'B': 'Confusion',
            'C': 'Polyuria',
            'D': 'Diaphoresis',
            'E': 'Fruity breath'
        },
        correct_answers={'A', 'B', 'D'},
        format='sata',
        question_type='assessment'
    )
    
    prediction = tism.predict(question3)
    print(f"\nQuestion: {question3.stem}")
    print(f"TISM predicts: {prediction}")
    print(f"Correct answers: {question3.correct_answers}")
    print(f"Result: {'✓ Correct' if prediction == question3.correct_answers else '✗ Incorrect'}")
    
    # Show decision log if in debug mode
    if tism.decision_log:
        print("\n\nDecision Process:")
        print("-" * 50)
        for entry in tism.decision_log[-5:]:  # Show last 5 entries
            print(f"  {entry}")

if __name__ == "__main__":
    main()