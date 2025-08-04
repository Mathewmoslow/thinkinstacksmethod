#!/usr/bin/env python3
"""
NCLEX Flowchart Validation Framework
A comprehensive system for validating NCLEX test-taking strategies
"""

import pandas as pd
import numpy as np
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from nclex_exceptions_handler import NCLEXExceptionHandler, enhance_flowchart_with_exceptions
import logging
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== DATA STRUCTURES ====================

@dataclass
class NCLEXQuestion:
    """Represents a single NCLEX question with all metadata"""
    id: str
    stem: str
    options: Dict[str, str]  # {'A': 'text', 'B': 'text', ...}
    correct_answers: Set[str]
    format: str  # 'single', 'sata', 'ordered'
    question_type: Optional[str] = None  # 'assessment', 'priority', etc.
    publisher: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'stem': self.stem,
            'options': json.dumps(self.options),
            'correct_answers': ','.join(sorted(self.correct_answers)),
            'format': self.format,
            'question_type': self.question_type,
            'publisher': self.publisher,
            'topic': self.topic,
            'difficulty': self.difficulty
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary/database row"""
        return cls(
            id=data['id'],
            stem=data['stem'],
            options=json.loads(data['options']) if isinstance(data['options'], str) else data['options'],
            correct_answers=set(data['correct_answers'].split(',')) if isinstance(data['correct_answers'], str) else data['correct_answers'],
            format=data['format'],
            question_type=data.get('question_type'),
            publisher=data.get('publisher'),
            topic=data.get('topic'),
            difficulty=data.get('difficulty')
        )

# ==================== KEYWORD PATTERNS ====================

class KeywordPatterns:
    """Centralized keyword patterns for rule-based classification"""
    
    # Stack of Four patterns
    AIRWAY_BREATHING = [
        r'\b(airway|breath|respirat|ventilat|oxygen|O2|sat|suction|trach|intubat|pneumo|dyspnea|hypox)',
        r'\b(cyanosis|apnea|stridor|wheez|gasp|chok)',
        r'\b(pulse ox|SpO2|ABG|arterial blood gas)',
    ]
    
    CIRCULATION = [
        r'\b(circulat|cardiac|heart|pulse|blood pressure|BP|hemorrhag|bleed)',
        r'\b(shock|hypotens|tachycard|bradycard|arrest|CPR)',
        r'\b(perfusion|pallor|diaphore|cold clam)',
    ]
    
    
    DISABILITY = [
        r'\b(neuro|neurolog|conscious|alert|orient|LOC|level of consciousness)',
        r'\b(pupil|reflex|motor|sensory|paralys|weakness|numb|ting)',
        r'\b(seizure|stroke|CVA|TIA|ICP|intracranial pressure)',
        r'\b(confus|disorient|unresponsive|lethargy|stupor|coma)',
        r'\b(Glasgow|GCS|decerebrate|decorticate)',
    ]
    
    
    SAFETY = [
        r'\b(fall|safety|restrain|bed rail|call bell|sitter)',
        r'\b(infect|isolat|precaution|PPE|hand hygien|sterile)',
        r'\b(suicid|self-harm|harm|violence|aggress|weapon)',
        r'\b(allerg|reaction|anaphyla)',
    ]
    
    MASLOW_PHYSIOLOGICAL = [
        r'\b(pain|comfort|analges|medicat)',
        r'\b(nutrit|food|diet|feed|NPO|TPN|tube feed)',
        r'\b(fluid|hydrat|I&O|intake output|IV)',
        r'\b(eliminat|urin|void|bowel|constipat|diarrhea)',
        r'\b(sleep|rest|fatigue|insomnia)',
    ]
    
    MASLOW_PSYCHOSOCIAL = [
        r'\b(anxiet|fear|stress|cop|depress|mood)',
        r'\b(family|support|social|isolat|loneli)',
        r'\b(spiritual|relig|cultur|belief)',
        r'\b(self-esteem|body image|identity)',
    ]
    
    # Nursing process patterns
    ASSESSMENT = [
        r'\b(assess|evaluat|monitor|check|observ|inspect|auscult|palpat)',
        r'\b(data|finding|sign|symptom|manifest)',
        r'\b(baseline|initial|admission)',
    ]
    
    PLANNING = [
        r'\b(plan|goal|outcome|objective|priorit)',
        r'\b(care plan|nursing diagnosis|intervention)',
    ]
    
    IMPLEMENTATION = [
        r'\b(implement|perform|administer|provide|teach|educat)',
        r'\b(procedure|technique|skill)',
    ]
    
    EVALUATION = [
        r'\b(evaluat|reassess|follow-up|response|effective)',
        r'\b(outcome|result|progress)',
    ]
    
    # Time-based patterns
    IMMEDIATE = [
        r'\b(immediate|emergenc|urgent|stat|now|first)',
        r'\b(life-threaten|critical|unstable)',
    ]
    
    @classmethod
    def compile_patterns(cls):
        """Compile all patterns for efficiency"""
        compiled = {}
        for attr_name in dir(cls):
            if attr_name.isupper() and not attr_name.startswith('_'):
                patterns = getattr(cls, attr_name)
                compiled[attr_name] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

# ==================== FLOWCHART ALGORITHM ====================

# NCLEXFlowchart replaced with TISM Tree Final
# Import moved to avoid circular dependency
NCLEXFlowchart = None  # Will be set by tism_tree_final.py


class NCLEXEvaluator:
    """Comprehensive evaluation metrics for NCLEX predictions"""
    
    def __init__(self):
        self.results = defaultdict(list)
    
    def evaluate_batch(self, questions: List[NCLEXQuestion], 
                      predictions: List[Set[str]]) -> Dict:
        """Evaluate a batch of predictions"""
        metrics = {
            'overall': {},
            'by_format': defaultdict(dict),
            'by_type': defaultdict(dict),
            'confusion_matrix': defaultdict(int)
        }
        
        # Group by format
        format_groups = defaultdict(list)
        for q, pred in zip(questions, predictions):
            format_groups[q.format].append((q, pred))
        
        # Calculate metrics by format
        for fmt, items in format_groups.items():
            if fmt == 'single':
                metrics['by_format'][fmt] = self._evaluate_single(items)
            elif fmt == 'sata':
                metrics['by_format'][fmt] = self._evaluate_sata(items)
            elif fmt == 'ordered':
                metrics['by_format'][fmt] = self._evaluate_ordered(items)
        
        # Overall metrics
        all_correct = sum(m.get('correct', 0) for m in metrics['by_format'].values())
        all_total = sum(m.get('total', 0) for m in metrics['by_format'].values())
        
        if all_total > 0:
            metrics['overall']['accuracy'] = all_correct / all_total
            metrics['overall']['total'] = all_total
            metrics['overall']['ci_lower'], metrics['overall']['ci_upper'] = \
                self._confidence_interval(all_correct, all_total)
        
        return metrics
    
    def _evaluate_single(self, items: List[Tuple[NCLEXQuestion, Set[str]]]) -> Dict:
        """Evaluate single-answer questions"""
        correct = 0
        total = len(items)
        
        for question, pred in items:
            if pred == question.correct_answers:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        ci_lower, ci_upper = self._confidence_interval(correct, total)
        
        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        }
    
    def _evaluate_sata(self, items: List[Tuple[NCLEXQuestion, Set[str]]]) -> Dict:
        """Evaluate SATA questions with multiple metrics"""
        exact_matches = 0
        total = len(items)
        
        all_true_positives = 0
        all_false_positives = 0
        all_false_negatives = 0
        
        for question, pred in items:
            correct = question.correct_answers
            
            # Exact match
            if pred == correct:
                exact_matches += 1
            
            # Calculate for F1
            true_positives = len(pred & correct)
            false_positives = len(pred - correct)
            false_negatives = len(correct - pred)
            
            all_true_positives += true_positives
            all_false_positives += false_positives
            all_false_negatives += false_negatives
        
        # Calculate metrics
        exact_match_acc = exact_matches / total if total > 0 else 0
        
        # F1 score
        precision = all_true_positives / (all_true_positives + all_false_positives) \
                   if (all_true_positives + all_false_positives) > 0 else 0
        recall = all_true_positives / (all_true_positives + all_false_negatives) \
                if (all_true_positives + all_false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) \
             if (precision + recall) > 0 else 0
        
        return {
            'exact_match_accuracy': exact_match_acc,
            'f1_score': f1,
            'precision': precision,
            'recall': recall,
            'correct': exact_matches,
            'total': total
        }
    
    def _evaluate_ordered(self, items: List[Tuple[NCLEXQuestion, Set[str]]]) -> Dict:
        """Evaluate ordered response questions"""
        perfect_sequences = 0
        total = len(items)
        kendall_scores = []
        
        for question, pred in items:
            # Convert sets to lists
            pred_seq = list(pred)[0].split(',') if pred else []
            correct_seq = list(question.correct_answers)[0].split(',')
            
            # Perfect sequence match
            if pred_seq == correct_seq:
                perfect_sequences += 1
            
            # Kendall's tau
            if len(pred_seq) == len(correct_seq):
                tau = self._kendall_tau(pred_seq, correct_seq)
                kendall_scores.append(tau)
        
        return {
            'perfect_sequence_accuracy': perfect_sequences / total if total > 0 else 0,
            'avg_kendall_tau': np.mean(kendall_scores) if kendall_scores else 0,
            'correct': perfect_sequences,
            'total': total
        }
    
    def _kendall_tau(self, seq1: List[str], seq2: List[str]) -> float:
        """Calculate Kendall's tau correlation coefficient"""
        n = len(seq1)
        if n != len(seq2) or n < 2:
            return 0
        
        # Create position mappings
        pos1 = {item: i for i, item in enumerate(seq1)}
        pos2 = {item: i for i, item in enumerate(seq2)}
        
        # Count concordant and discordant pairs
        concordant = 0
        discordant = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                item_i, item_j = seq1[i], seq1[j]
                if item_i in pos2 and item_j in pos2:
                    if (pos1[item_i] < pos1[item_j]) == (pos2[item_i] < pos2[item_j]):
                        concordant += 1
                    else:
                        discordant += 1
        
        total_pairs = n * (n - 1) / 2
        return (concordant - discordant) / total_pairs if total_pairs > 0 else 0
    
    def _confidence_interval(self, successes: int, trials: int, 
                           confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate Wilson confidence interval for proportion"""
        if trials == 0:
            return (0, 0)
        
        from scipy import stats
        
        p_hat = successes / trials
        z = stats.norm.ppf((1 + confidence) / 2)
        
        denominator = 1 + z**2 / trials
        center = (p_hat + z**2 / (2 * trials)) / denominator
        margin = z * np.sqrt(p_hat * (1 - p_hat) / trials + z**2 / (4 * trials**2)) / denominator
        
        return (max(0, center - margin), min(1, center + margin))

# ==================== DATA MANAGEMENT ====================

class NCLEXDataManager:
    """Manages question corpus with SQLite backend"""
    
    def __init__(self, db_path: str = "nclex_questions.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                stem TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answers TEXT NOT NULL,
                format TEXT NOT NULL,
                question_type TEXT,
                publisher TEXT,
                topic TEXT,
                difficulty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                run_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                algorithm_version TEXT,
                dataset_hash TEXT,
                metrics TEXT,
                config TEXT
            )
        ''')
        
        self.conn.commit()
    
    def add_question(self, question: NCLEXQuestion):
        """Add a question to the database"""
        data = question.to_dict()
        self.conn.execute('''
            INSERT OR REPLACE INTO questions 
            (id, stem, options, correct_answers, format, question_type, 
             publisher, topic, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['id'], data['stem'], data['options'], 
              data['correct_answers'], data['format'], data['question_type'],
              data['publisher'], data['topic'], data['difficulty']))
        self.conn.commit()
    
    def get_questions(self, format_type: Optional[str] = None,
                     publisher: Optional[str] = None,
                     limit: Optional[int] = None) -> List[NCLEXQuestion]:
        """Retrieve questions with optional filters"""
        query = "SELECT * FROM questions WHERE 1=1"
        params = []
        
        if format_type:
            query += " AND format = ?"
            params.append(format_type)
        
        if publisher:
            query += " AND publisher = ?"
            params.append(publisher)
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.conn.execute(query, params)
        questions = []
        
        for row in cursor:
            data = dict(zip([col[0] for col in cursor.description], row))
            questions.append(NCLEXQuestion.from_dict(data))
        
        return questions
    
    def create_train_test_split(self, test_ratio: float = 0.2, 
                              random_seed: int = 42) -> Tuple[List[str], List[str]]:
        """Create train/test split, returning question IDs"""
        np.random.seed(random_seed)
        
        all_ids = [row[0] for row in 
                  self.conn.execute("SELECT id FROM questions").fetchall()]
        
        np.random.shuffle(all_ids)
        split_point = int(len(all_ids) * (1 - test_ratio))
        
        train_ids = all_ids[:split_point]
        test_ids = all_ids[split_point:]
        
        return train_ids, test_ids
    
    def save_evaluation_run(self, metrics: Dict, config: Dict, 
                          algorithm_version: str = "1.0"):
        """Save evaluation results"""
        run_id = hashlib.sha256(
            f"{datetime.now().isoformat()}{algorithm_version}".encode()
        ).hexdigest()[:16]
        
        # Calculate dataset hash
        dataset_hash = hashlib.sha256(
            "".join([row[0] for row in 
                    self.conn.execute("SELECT id FROM questions ORDER BY id").fetchall()])
            .encode()
        ).hexdigest()[:16]
        
        self.conn.execute('''
            INSERT INTO evaluation_runs 
            (run_id, algorithm_version, dataset_hash, metrics, config)
            VALUES (?, ?, ?, ?, ?)
        ''', (run_id, algorithm_version, dataset_hash, 
              json.dumps(metrics), json.dumps(config)))
        self.conn.commit()
        
        return run_id

# ==================== MAIN PIPELINE ====================

def run_evaluation_pipeline(db_path: str = "nclex_questions.db",
                          debug: bool = False,
                          test_ratio: float = 0.2):
    """Run complete evaluation pipeline"""
    
    logger.info("Starting NCLEX evaluation pipeline")
    
    # Initialize components
    data_manager = NCLEXDataManager(db_path)
    flowchart = NCLEXFlowchart(debug=debug)
    # Exception handling already integrated in TISMTreeV2  # Add exception handling
    evaluator = NCLEXEvaluator()
    
    # Get train/test split
    train_ids, test_ids = data_manager.create_train_test_split(test_ratio)
    logger.info(f"Train set: {len(train_ids)} questions, Test set: {len(test_ids)} questions")
    
    # Load test questions
    test_questions = []
    for qid in test_ids:
        questions = data_manager.get_questions()
        test_questions.extend([q for q in questions if q.id == qid])
    
    # Generate predictions
    logger.info("Generating predictions...")
    predictions = []
    for question in test_questions:
        pred = flowchart.predict(question)
        predictions.append(pred)
    
    # Evaluate
    logger.info("Evaluating predictions...")
    metrics = evaluator.evaluate_batch(test_questions, predictions)
    
    # Print results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    
    print(f"\nOverall Performance:")
    print(f"  Accuracy: {metrics['overall'].get('accuracy', 0):.1%}")
    print(f"  95% CI: [{metrics['overall'].get('ci_lower', 0):.1%}, "
          f"{metrics['overall'].get('ci_upper', 0):.1%}]")
    print(f"  Total Questions: {metrics['overall'].get('total', 0)}")
    
    print(f"\nPerformance by Format:")
    for fmt, fmt_metrics in metrics['by_format'].items():
        print(f"\n  {fmt.upper()}:")
        if fmt == 'single':
            print(f"    Accuracy: {fmt_metrics.get('accuracy', 0):.1%}")
        elif fmt == 'sata':
            print(f"    Exact Match: {fmt_metrics.get('exact_match_accuracy', 0):.1%}")
            print(f"    F1 Score: {fmt_metrics.get('f1_score', 0):.3f}")
        elif fmt == 'ordered':
            print(f"    Perfect Sequence: {fmt_metrics.get('perfect_sequence_accuracy', 0):.1%}")
            print(f"    Avg Kendall Tau: {fmt_metrics.get('avg_kendall_tau', 0):.3f}")
    
    # Save results
    config = {
        'test_ratio': test_ratio,
        'debug': debug,
        'n_train': len(train_ids),
        'n_test': len(test_ids)
    }
    run_id = data_manager.save_evaluation_run(metrics, config)
    logger.info(f"Results saved with run_id: {run_id}")
    
    return metrics

# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Example: Load questions from CSV
    def load_questions_from_csv(csv_path: str, data_manager: NCLEXDataManager):
        """Load questions from CSV file"""
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            # Parse options
            options = {}
            for opt in ['A', 'B', 'C', 'D', 'E']:
                if opt in row and pd.notna(row[opt]):
                    options[opt] = row[opt]
            
            # Parse correct answers
            correct = set(row['correct'].split(',')) if ',' in str(row['correct']) else {row['correct']}
            
            question = NCLEXQuestion(
                id=str(row['id']),
                stem=row['stem'],
                options=options,
                correct_answers=correct,
                format=row['format'],
                question_type=row.get('question_type'),
                publisher=row.get('publisher'),
                topic=row.get('topic'),
                difficulty=row.get('difficulty')
            )
            
            data_manager.add_question(question)
    
    # Run evaluation
    metrics = run_evaluation_pipeline(debug=True)
