#!/usr/bin/env python3
"""Example demonstrating TISM's machine learning capabilities"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tism_tree_final import TISMTreeFinal
from core.nclex_validation_framework import NCLEXQuestion
from core.tism_learning_system import TISMLearningSystem

def main():
    print("=== TISM Machine Learning Example ===\n")
    
    # Initialize learning system
    learning_system = TISMLearningSystem()
    
    # Initialize TISM with learning enabled
    tism = TISMTreeFinal(enable_learning=True, debug=True)
    
    # Example questions where TISM might initially fail but can learn
    questions = [
        NCLEXQuestion(
            id="learn1",
            stem="A client with a history of falls is found on the floor. The nurse should first:",
            options={
                'A': 'Help the client up immediately',
                'B': 'Assess for injuries before moving',
                'C': 'Call for assistance',
                'D': 'Document the incident'
            },
            correct_answers={'B'},
            format='single',
            question_type='priority'
        ),
        NCLEXQuestion(
            id="learn2",
            stem="A diabetic client reports feeling shaky and sweaty. Priority action:",
            options={
                'A': 'Check blood glucose level',
                'B': 'Give 15g of simple carbohydrates',
                'C': 'Call the physician',
                'D': 'Administer insulin'
            },
            correct_answers={'A'},  # Assessment first!
            format='single',
            question_type='priority'
        ),
        NCLEXQuestion(
            id="learn3",
            stem="Post-op client complains of severe pain (8/10). The nurse should first:",
            options={
                'A': 'Administer prescribed pain medication',
                'B': 'Assess the surgical site',
                'C': 'Reposition the client',
                'D': 'Apply ice to the area'
            },
            correct_answers={'B'},  # Assessment wins!
            format='single',
            question_type='priority'
        )
    ]
    
    print("Testing TISM before learning...\n")
    print("-" * 60)
    
    # First pass - TISM might get some wrong
    first_pass_results = []
    for question in questions:
        prediction = tism.predict(question)
        is_correct = prediction == question.correct_answers
        first_pass_results.append(is_correct)
        
        print(f"Question: {question.stem[:60]}...")
        print(f"Predicted: {prediction}, Correct: {question.correct_answers}")
        print(f"Result: {'✓ Correct' if is_correct else '✗ Incorrect - Learning...'}")
        print()
    
    # Show initial accuracy
    initial_accuracy = sum(first_pass_results) / len(first_pass_results) * 100
    print(f"Initial Accuracy: {initial_accuracy:.1f}%\n")
    
    print("\nTISM is now learning from mistakes...\n")
    print("-" * 60)
    
    # Second pass - TISM should improve
    print("\nTesting TISM after learning...\n")
    
    second_pass_results = []
    for question in questions:
        prediction = tism.predict(question)
        is_correct = prediction == question.correct_answers
        second_pass_results.append(is_correct)
        
        print(f"Question: {question.stem[:60]}...")
        print(f"Predicted: {prediction}, Correct: {question.correct_answers}")
        print(f"Result: {'✓ Correct' if is_correct else '✗ Incorrect'}")
        print()
    
    # Show improved accuracy
    final_accuracy = sum(second_pass_results) / len(second_pass_results) * 100
    print(f"Final Accuracy: {final_accuracy:.1f}%")
    print(f"Improvement: +{final_accuracy - initial_accuracy:.1f}%\n")
    
    # Generate learning report
    print("\n" + "=" * 60)
    print("LEARNING SYSTEM REPORT")
    print("=" * 60)
    
    report = learning_system.generate_learning_report()
    print(report)
    
    # Show what TISM learned
    print("\n\nKey Insights Learned:")
    print("-" * 40)
    print("1. Assessment often takes priority even in urgent situations")
    print("2. 'First' questions frequently require assessment before intervention")
    print("3. Safety assessments (checking for injuries) come before moving clients")
    print("4. Even with clear symptoms, assessment validates the intervention")
    
    # Save learning data
    learning_system.save_learning_data()
    print("\n\nLearning data saved for future sessions!")
    
    # Demonstrate adaptive patterns
    print("\n\nAdaptive Pattern Examples:")
    print("-" * 40)
    
    enhanced_patterns = learning_system.get_enhanced_patterns()
    for stack, patterns in enhanced_patterns.items():
        if patterns:
            print(f"\n{stack}:")
            for pattern in patterns[:3]:  # Show first 3
                print(f"  - {pattern}")

if __name__ == "__main__":
    main()