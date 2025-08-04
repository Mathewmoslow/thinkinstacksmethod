#!/usr/bin/env python3
"""
Extract priority questions from all datasets and test TISM implementations
"""

import json
import re
from typing import Dict, List, Tuple, Set
from datetime import datetime
import os

# Import our components
from nclex_validation_framework import NCLEXQuestion
from tism_tree_final import TISMTreeFinal
from tism_context_aware import ContextAwareTISM
from tism_with_clinical_kb import TISMWithClinicalKB

class PriorityQuestionExtractor:
    """Extract questions that TISM is designed for"""
    
    def __init__(self):
        # Priority question patterns
        self.PRIORITY_PATTERNS = [
            r'\b(priority|first|immediate|initial)\s+(action|intervention|response)',
            r'\bwhich.*should.*nurse.*do\s+first',
            r'\bmost\s+important',
            r'\bhighest\s+priority',
            r'\bwhich.*assess\s+first',
            r'\bpriority\s+assessment',
            r'\bmost\s+concerning',
            r'\brequires\s+immediate',
            r'\blife-threatening',
            r'\bnurse\s+should.*first',
            r'\binitial\s+nursing',
            r'\bimmediate.*action',
            r'\bwhich.*finding.*report.*immediately',
            r'\bwhich.*client.*see\s+first'
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PRIORITY_PATTERNS]
        
        # Action option patterns
        self.action_patterns = [
            r'\b(assess|monitor|check|evaluate|observe)',
            r'\b(administer|give|provide|perform|apply)',
            r'\b(notify|call|contact|report|inform)',
            r'\b(position|place|move|turn|elevate)',
            r'\b(teach|instruct|educate|explain)',
            r'\b(ensure|maintain|keep|prevent)',
            r'\b(document|record|chart)',
            r'\b(begin|start|initiate|implement)'
        ]
        self.action_regex = [re.compile(p, re.IGNORECASE) for p in self.action_patterns]
    
    def is_priority_question(self, question: NCLEXQuestion) -> bool:
        """Check if question is a priority/action question"""
        # Check stem for priority indicators
        stem_match = any(pattern.search(question.stem) for pattern in self.compiled_patterns)
        
        # Check if options are actions
        action_count = 0
        for option in question.options.values():
            if any(pattern.search(option) for pattern in self.action_regex):
                action_count += 1
        
        # Consider it priority if:
        # 1. Stem has priority language AND most options are actions
        # 2. Question type is marked as priority/assessment/implementation
        has_action_options = action_count >= len(question.options) * 0.5
        
        return (stem_match and has_action_options) or question.question_type in ['priority', 'assessment', 'implementation']
    
    def extract_from_json(self, json_path: str) -> List[NCLEXQuestion]:
        """Extract priority questions from JSON file"""
        priority_questions = []
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            questions = data if isinstance(data, list) else data.get('questions', [])
            
            for q_data in questions:
                # Create NCLEXQuestion
                nclex_q = NCLEXQuestion(
                    id=q_data.get('id', ''),
                    stem=q_data.get('stem', ''),
                    options=q_data.get('options', {}),
                    correct_answers=set(q_data.get('correct_answers', [])),
                    format=q_data.get('format', 'single'),
                    question_type=q_data.get('question_type', 'general')
                )
                
                # Check if priority question
                if self.is_priority_question(nclex_q):
                    priority_questions.append(nclex_q)
                    
        except Exception as e:
            print(f"Error processing {json_path}: {e}")
        
        return priority_questions

def test_implementations_on_priority_questions(questions: List[NCLEXQuestion]):
    """Test all TISM implementations on priority questions"""
    
    implementations = {
        'Original TISM (Keywords)': TISMTreeFinal(use_ai_knowledge=False, debug=False),
        'Context-Aware TISM': ContextAwareTISM(debug=False),
        'TISM with Clinical KB': TISMWithClinicalKB(debug=False)
    }
    
    results = {impl_name: {'correct': 0, 'total': 0, 'by_format': {}} for impl_name in implementations}
    
    print(f"\nTesting {len(questions)} priority questions...")
    print("="*80)
    
    for i, question in enumerate(questions):
        if (i + 1) % 10 == 0:
            print(f"Progress: {i+1}/{len(questions)}...")
        
        for impl_name, implementation in implementations.items():
            try:
                # Get prediction
                prediction = implementation.predict(question)
                
                # Check if correct
                is_correct = False
                if question.format == 'single':
                    predicted = list(prediction)[0] if prediction else 'A'
                    is_correct = predicted in question.correct_answers
                elif question.format == 'sata':
                    is_correct = prediction == question.correct_answers
                
                # Update results
                results[impl_name]['total'] += 1
                if is_correct:
                    results[impl_name]['correct'] += 1
                
                # Track by format
                fmt = question.format
                if fmt not in results[impl_name]['by_format']:
                    results[impl_name]['by_format'][fmt] = {'correct': 0, 'total': 0}
                results[impl_name]['by_format'][fmt]['total'] += 1
                if is_correct:
                    results[impl_name]['by_format'][fmt]['correct'] += 1
                    
            except Exception as e:
                print(f"Error testing {impl_name} on question {question.id}: {e}")
    
    return results

def main():
    """Main execution"""
    print("TISM COMPREHENSIVE TESTING ON PRIORITY QUESTIONS")
    print("="*80)
    
    extractor = PriorityQuestionExtractor()
    all_priority_questions = []
    
    # 1. Extract from clean test set
    if os.path.exists('clean_test_set.json'):
        print("\nExtracting from clean_test_set.json...")
        clean_questions = extractor.extract_from_json('clean_test_set.json')
        print(f"Found {len(clean_questions)} priority questions")
        all_priority_questions.extend(clean_questions)
    
    # 2. Extract from fullquestions
    if os.path.exists('fullquestions_tism_format.json'):
        print("\nExtracting from fullquestions_tism_format.json...")
        full_questions = extractor.extract_from_json('fullquestions_tism_format.json')
        print(f"Found {len(full_questions)} priority questions")
        all_priority_questions.extend(full_questions)
    
    # 3. Extract from question repository
    if os.path.exists('question_repository.json'):
        print("\nExtracting from question_repository.json...")
        repo_questions = extractor.extract_from_json('question_repository.json')
        print(f"Found {len(repo_questions)} priority questions")
        all_priority_questions.extend(repo_questions)
    
    # Remove duplicates based on stem
    unique_questions = {}
    for q in all_priority_questions:
        key = q.stem[:50]  # Use first 50 chars as key
        if key not in unique_questions:
            unique_questions[key] = q
    
    priority_questions = list(unique_questions.values())
    print(f"\nTotal unique priority questions: {len(priority_questions)}")
    
    # Save combined priority questions
    priority_data = []
    for q in priority_questions:
        priority_data.append({
            'id': q.id,
            'stem': q.stem,
            'options': q.options,
            'correct_answers': list(q.correct_answers),
            'format': q.format,
            'question_type': q.question_type
        })
    
    with open('combined_priority_questions.json', 'w') as f:
        json.dump(priority_data, f, indent=2)
    print(f"Saved {len(priority_questions)} priority questions to combined_priority_questions.json")
    
    # Test implementations
    results = test_implementations_on_priority_questions(priority_questions)
    
    # Display results
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    for impl_name, impl_results in results.items():
        if impl_results['total'] > 0:
            accuracy = impl_results['correct'] / impl_results['total'] * 100
            print(f"\n{impl_name}:")
            print(f"  Overall: {accuracy:.1f}% ({impl_results['correct']}/{impl_results['total']})")
            
            # By format
            for fmt, fmt_results in impl_results['by_format'].items():
                if fmt_results['total'] > 0:
                    fmt_acc = fmt_results['correct'] / fmt_results['total'] * 100
                    print(f"  {fmt}: {fmt_acc:.1f}% ({fmt_results['correct']}/{fmt_results['total']})")
    
    # Save detailed results
    with open('priority_questions_test_results.json', 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'total_questions': len(priority_questions),
            'results': results
        }, f, indent=2)
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # Calculate improvements
    if 'Original TISM (Keywords)' in results and results['Original TISM (Keywords)']['total'] > 0:
        baseline = results['Original TISM (Keywords)']['correct'] / results['Original TISM (Keywords)']['total'] * 100
        
        for impl_name, impl_results in results.items():
            if impl_name != 'Original TISM (Keywords)' and impl_results['total'] > 0:
                impl_acc = impl_results['correct'] / impl_results['total'] * 100
                improvement = impl_acc - baseline
                print(f"{impl_name} improvement over baseline: {improvement:+.1f}%")
    
    print("\nThese results show TISM performance on questions it was specifically designed for:")
    print("- Priority action questions")
    print("- Assessment priority questions")  
    print("- Safety/emergency questions")
    print("- Questions requiring clinical prioritization")

if __name__ == "__main__":
    main()