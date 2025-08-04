#!/usr/bin/env python3
"""Comprehensive TISM analysis with statistical calculations."""

import json
import math
from datetime import datetime
from typing import Dict, List, Tuple
from tism_tree_final import TISMTreeFinal, StudentQuickReference
from nclex_validation_framework import NCLEXQuestion
import numpy as np
from scipy import stats

def wilson_score_ci(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score confidence interval."""
    if total == 0:
        return (0.0, 0.0)
    
    p_hat = successes / total
    z = stats.norm.ppf((1 + confidence) / 2)
    
    denominator = 1 + z**2 / total
    center_adjusted_probability = (p_hat + z**2 / (2 * total)) / denominator
    adjusted_standard_deviation = math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denominator
    
    lower = max(0.0, center_adjusted_probability - z * adjusted_standard_deviation)
    upper = min(1.0, center_adjusted_probability + z * adjusted_standard_deviation)
    
    return (lower * 100, upper * 100)

def chi_square_test(clean_correct: int, clean_total: int, messy_correct: int, messy_total: int) -> Tuple[float, float]:
    """Perform chi-square test for independence."""
    # Create contingency table
    observed = np.array([[clean_correct, clean_total - clean_correct],
                        [messy_correct, messy_total - messy_correct]])
    
    # Chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(observed)
    
    return chi2, p_value

def run_comprehensive_analysis():
    """Run comprehensive TISM analysis on all datasets."""
    
    print("=" * 80)
    print("COMPREHENSIVE TISM ANALYSIS")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Load datasets
    print("Loading datasets...")
    
    # Original clean dataset
    with open('clean_test_set.json', 'r') as f:
        clean_questions = json.load(f)
    
    # New processed dataset
    with open('processed_478_questions.json', 'r') as f:
        new_questions = json.load(f)
    
    print(f"✓ Loaded {len(clean_questions)} clean questions")
    print(f"✓ Loaded {len(new_questions)} new processed questions")
    print()
    
    # Test configurations
    configs = [
        ("Clean Dataset - No AI", clean_questions, False),
        ("Clean Dataset - With AI", clean_questions, True),
        ("New Dataset - No AI", new_questions, False),
        ("New Dataset - With AI", new_questions, True)
    ]
    
    all_results = {}
    
    for config_name, questions, use_ai in configs:
        print(f"\n{'='*60}")
        print(f"Testing: {config_name}")
        print(f"{'='*60}")
        
        # Initialize TISM
        tism = TISMTreeFinal(use_ai_knowledge=use_ai, enable_learning=False)
        
        results = {
            'total': 0,
            'correct': 0,
            'by_type': {},
            'by_format': {'single': {'total': 0, 'correct': 0}, 
                          'sata': {'total': 0, 'correct': 0}},
            'errors': []
        }
        
        # Test each question
        for q in questions:
            results['total'] += 1
            
            # Convert to NCLEXQuestion
            nclex_q = NCLEXQuestion(
                id=q['id'],
                stem=q['stem'],
                options=q['options'],
                correct_answers=q['correct_answers'],
                format=q['format'],
                question_type=q['question_type']
            )
            
            # Make prediction
            try:
                predicted = tism.predict(nclex_q)
                correct = q['correct_answers']
                
                # Check correctness
                if q['format'] == 'sata':
                    predicted_set = predicted if isinstance(predicted, set) else set(predicted)
                    correct_set = set(correct)
                    is_correct = predicted_set == correct_set
                else:
                    predicted_answer = list(predicted)[0] if isinstance(predicted, set) else predicted
                    is_correct = predicted_answer == correct[0]
                
                # Update results
                if is_correct:
                    results['correct'] += 1
                else:
                    results['errors'].append({
                        'id': q['id'],
                        'type': q['question_type'],
                        'predicted': list(predicted) if isinstance(predicted, set) else predicted,
                        'correct': correct
                    })
                
                # By type
                qtype = q['question_type']
                if qtype not in results['by_type']:
                    results['by_type'][qtype] = {'total': 0, 'correct': 0}
                results['by_type'][qtype]['total'] += 1
                if is_correct:
                    results['by_type'][qtype]['correct'] += 1
                
                # By format
                results['by_format'][q['format']]['total'] += 1
                if is_correct:
                    results['by_format'][q['format']]['correct'] += 1
                    
            except Exception as e:
                print(f"Error processing question {q['id']}: {e}")
                continue
        
        # Calculate statistics
        accuracy = (results['correct'] / results['total'] * 100) if results['total'] > 0 else 0
        ci_lower, ci_upper = wilson_score_ci(results['correct'], results['total'])
        
        # Print summary
        print(f"\nOverall Results:")
        print(f"  Accuracy: {accuracy:.1f}% ({results['correct']}/{results['total']})")
        print(f"  95% CI: [{ci_lower:.1f}%, {ci_upper:.1f}%]")
        
        print(f"\nBy Format:")
        for fmt, data in results['by_format'].items():
            if data['total'] > 0:
                acc = data['correct'] / data['total'] * 100
                print(f"  {fmt}: {acc:.1f}% ({data['correct']}/{data['total']})")
        
        print(f"\nBy Question Type:")
        for qtype, data in sorted(results['by_type'].items()):
            if data['total'] > 0:
                acc = data['correct'] / data['total'] * 100
                print(f"  {qtype}: {acc:.1f}% ({data['correct']}/{data['total']})")
        
        all_results[config_name] = results
    
    # Comparative Analysis
    print("\n" + "="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)
    
    # Compare AI vs No AI
    print("\n### AI Enhancement Impact:")
    for dataset in ["Clean Dataset", "New Dataset"]:
        no_ai = all_results[f"{dataset} - No AI"]
        with_ai = all_results[f"{dataset} - With AI"]
        
        no_ai_acc = (no_ai['correct'] / no_ai['total'] * 100) if no_ai['total'] > 0 else 0
        ai_acc = (with_ai['correct'] / with_ai['total'] * 100) if with_ai['total'] > 0 else 0
        
        print(f"\n{dataset}:")
        print(f"  No AI: {no_ai_acc:.1f}%")
        print(f"  With AI: {ai_acc:.1f}%")
        print(f"  Difference: {ai_acc - no_ai_acc:+.1f}%")
    
    # Compare datasets
    print("\n### Dataset Comparison (No AI):")
    clean_results = all_results["Clean Dataset - No AI"]
    new_results = all_results["New Dataset - No AI"]
    
    clean_acc = (clean_results['correct'] / clean_results['total'] * 100)
    new_acc = (new_results['correct'] / new_results['total'] * 100)
    
    print(f"Clean Dataset: {clean_acc:.1f}% ({clean_results['correct']}/{clean_results['total']})")
    print(f"New Dataset: {new_acc:.1f}% ({new_results['correct']}/{new_results['total']})")
    print(f"Performance Ratio: {clean_acc/new_acc:.1f}x")
    
    # Chi-square test
    chi2, p_value = chi_square_test(
        clean_results['correct'], clean_results['total'],
        new_results['correct'], new_results['total']
    )
    print(f"\nChi-square test:")
    print(f"  χ² = {chi2:.2f}")
    print(f"  p-value = {p_value:.4f}")
    print(f"  Significant difference: {'Yes' if p_value < 0.05 else 'No'}")
    
    # Error Analysis
    print("\n### Common Error Patterns:")
    error_types = {}
    for config_name, results in all_results.items():
        for error in results['errors'][:5]:  # Show first 5 errors
            etype = error['type']
            if etype not in error_types:
                error_types[etype] = 0
            error_types[etype] += 1
    
    for etype, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {etype}: {count} errors")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'clean_dataset_size': len(clean_questions),
            'new_dataset_size': len(new_questions),
            'configurations_tested': len(configs)
        },
        'results': all_results,
        'statistical_tests': {
            'chi_square': {
                'value': chi2,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        }
    }
    
    with open('tism_comprehensive_analysis_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Detailed results saved to tism_comprehensive_analysis_results.json")
    
    # Print Quick Reference
    print("\n" + "="*80)
    print("TISM QUICK REFERENCE CARD")
    print("="*80)
    StudentQuickReference.print_card()

if __name__ == "__main__":
    # Install scipy if needed
    try:
        import scipy
    except ImportError:
        print("Installing scipy for statistical tests...")
        import subprocess
        subprocess.check_call(["pip3", "install", "scipy", "numpy"])
    
    run_comprehensive_analysis()