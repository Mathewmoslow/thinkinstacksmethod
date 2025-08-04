#!/usr/bin/env python3
"""Example of validating TISM on a question set"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tism_tree_final import TISMTreeFinal
from core.nclex_validation_framework import NCLEXQuestion
from validation.extract_and_test_priority_questions import PriorityQuestionExtractor

def main():
    print("=== TISM Validation Example ===\n")
    
    # Load test questions
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'clean_test_set.json')
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        print("Creating sample questions...")
        
        # Create sample questions for demonstration
        sample_questions = [
            {
                "id": "sample1",
                "stem": "A nurse finds a client lying on the floor. What should the nurse do first?",
                "options": {
                    "A": "Call for help",
                    "B": "Check for responsiveness",
                    "C": "Move the client to bed",
                    "D": "Document the incident"
                },
                "correct_answers": ["B"],
                "format": "single",
                "question_type": "priority"
            },
            {
                "id": "sample2",
                "stem": "A client with COPD is experiencing severe dyspnea. The nurse should first:",
                "options": {
                    "A": "Administer oxygen",
                    "B": "Call the physician",
                    "C": "Position in high Fowler's",
                    "D": "Obtain ABG results"
                },
                "correct_answers": ["C"],
                "format": "single",
                "question_type": "priority"
            }
        ]
        
        questions = sample_questions
    else:
        with open(test_file, 'r') as f:
            questions = json.load(f)
    
    # Initialize TISM
    tism = TISMTreeFinal(use_ai_knowledge=False, enable_learning=True, debug=False)
    
    # Test each question
    correct = 0
    total = 0
    results = []
    
    print(f"Testing {len(questions)} questions...\n")
    
    for q_data in questions[:10]:  # Test first 10 questions
        # Create NCLEXQuestion object
        question = NCLEXQuestion(
            id=q_data.get('id', f'q{total}'),
            stem=q_data['stem'],
            options=q_data['options'],
            correct_answers=set(q_data['correct_answers']),
            format=q_data.get('format', 'single'),
            question_type=q_data.get('question_type', 'priority')
        )
        
        # Get prediction
        prediction = tism.predict(question)
        
        # Check if correct
        is_correct = prediction == question.correct_answers
        if is_correct:
            correct += 1
        total += 1
        
        # Store result
        results.append({
            'question_id': question.id,
            'stem': question.stem[:50] + '...' if len(question.stem) > 50 else question.stem,
            'predicted': list(prediction),
            'correct': list(question.correct_answers),
            'is_correct': is_correct
        })
        
        # Print progress
        if total % 5 == 0:
            print(f"Progress: {total} questions tested...")
    
    # Calculate accuracy
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Print results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"Total Questions: {total}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {total - correct}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Show some examples
    print("\nSample Results:")
    print("-" * 60)
    
    for i, result in enumerate(results[:5]):
        status = "✓" if result['is_correct'] else "✗"
        print(f"\n{status} Question {i+1}: {result['stem']}")
        print(f"   Predicted: {result['predicted']}")
        print(f"   Correct: {result['correct']}")
    
    # Performance by question type (if available)
    if any('question_type' in q for q in questions):
        print("\n\nPerformance by Question Type:")
        print("-" * 40)
        
        type_stats = {}
        for i, result in enumerate(results):
            q_type = questions[i].get('question_type', 'unknown')
            if q_type not in type_stats:
                type_stats[q_type] = {'correct': 0, 'total': 0}
            
            type_stats[q_type]['total'] += 1
            if result['is_correct']:
                type_stats[q_type]['correct'] += 1
        
        for q_type, stats in type_stats.items():
            acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{q_type}: {acc:.1f}% ({stats['correct']}/{stats['total']})")
    
    # Save detailed results
    output_file = 'validation_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total': total,
                'correct': correct,
                'accuracy': accuracy
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()