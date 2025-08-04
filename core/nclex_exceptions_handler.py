#!/usr/bin/env python3
"""
NCLEX Exception Handler Module
Handles the 5% of edge cases that require special processing
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExceptionContext:
    """Context for exception handling"""
    exception_type: str
    confidence: float
    override_prediction: Optional[Set[str]] = None
    reasoning: str = ""
    red_flags: List[str] = None

class NCLEXExceptionHandler:
    """Handles special cases that deviate from standard Stack of Four"""
    
    def __init__(self):
        # Exception detection patterns
        self.TIME_SEQUENCE_PATTERNS = [
            r'\b(after|following|has already|next|then|completed|established)\b',
            r'\b(post-|status post|s/p)\b',
            r'\b(which action.*next|what.*do next)\b',
        ]
        
        self.EXCLUSION_PATTERNS = [
            r'\b(except|avoid|not appropriate|contraindicated)\b',
            r'\b(all.*except|which.*not|inappropriate)\b',
            r'\b(should not|must not|never)\b',
        ]
        
        self.CHRONIC_VS_NEW_PATTERNS = {
            'chronic': [
                r'\b(usual|chronic|long-standing|baseline|controlled|stable)\b',
                r'\b(history of|diagnosed with|known)\b',
                r'\b(for \d+ years|months|weeks)\b',
            ],
            'new': [
                r'\b(new onset|sudden|acute|just|unexpected)\b',
                r'\b(change in|different from|never had)\b',
                r'\b(started|began|developed)\b',
            ]
        }
        
        self.CONTEXT_PATTERNS = {
            'psych': r'\b(psych|mental health|behavioral|psychiatric)\b',
            'pediatric': r'\b(infant|child|pediatric|newborn|adolescent)\b',
            'cultural': r'\b(cultural|religious|spiritual|belief)\b',
            'legal': r'\b(legal|ethical|consent|refuse|autonomy|rights)\b',
        }
        
        
        self.DISABILITY_PATTERNS = [
            r'\b(after.*neuro.*assessment|following.*Glasgow)',
            r'\b(established.*neurological.*baseline)',
            r'\b(completed.*pupil.*check)',
        ]
        
        self.RED_FLAG_PHRASES = [
            # Time
            r'\b(after.*completed|following.*established)\b',
            # Exclusion
            r'\b(all.*except|which.*avoid)\b',
            # Context
            r'\b(psych unit|cultural consideration|legal requirement)\b',
            # Stability
            r'\b(chronic.*stable|baseline.*normal)\b',
        ]
        
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns"""
        self.time_sequence_regex = [re.compile(p, re.IGNORECASE) for p in self.TIME_SEQUENCE_PATTERNS]
        self.exclusion_regex = [re.compile(p, re.IGNORECASE) for p in self.EXCLUSION_PATTERNS]
        self.chronic_regex = [re.compile(p, re.IGNORECASE) for p in self.CHRONIC_VS_NEW_PATTERNS['chronic']]
        self.new_regex = [re.compile(p, re.IGNORECASE) for p in self.CHRONIC_VS_NEW_PATTERNS['new']]
        self.context_regex = {k: re.compile(v, re.IGNORECASE) for k, v in self.CONTEXT_PATTERNS.items()}
        self.red_flag_regex = [re.compile(p, re.IGNORECASE) for p in self.RED_FLAG_PHRASES]
    
    def detect_exceptions(self, question_stem: str, options: Dict[str, str]) -> List[ExceptionContext]:
        """Detect if question contains exception patterns"""
        exceptions = []
        
        # Check for time sequence
        if self._has_time_sequence(question_stem):
            context = self._analyze_time_sequence(question_stem, options)
            if context:
                exceptions.append(context)
        
        # Check for exclusion
        if self._has_exclusion(question_stem):
            context = self._analyze_exclusion(question_stem, options)
            if context:
                exceptions.append(context)
        
        # Check for chronic vs new
        chronic_new = self._detect_chronic_vs_new(question_stem, options)
        if chronic_new:
            exceptions.append(chronic_new)
        
        # Check for special contexts
        context_exception = self._detect_special_context(question_stem, options)
        if context_exception:
            exceptions.append(context_exception)
        
        # Check for red flags
        red_flags = self._detect_red_flags(question_stem)
        if red_flags and not exceptions:
            # Create a general caution exception
            exceptions.append(ExceptionContext(
                exception_type='red_flag',
                confidence=0.7,
                reasoning="Red flag phrases detected - careful analysis needed",
                red_flags=red_flags
            ))
        
        return exceptions
    
    def _has_time_sequence(self, text: str) -> bool:
        """Check if text contains time sequence indicators"""
        return any(pattern.search(text) for pattern in self.time_sequence_regex)
    
    def _has_exclusion(self, text: str) -> bool:
        """Check if text contains exclusion indicators"""
        return any(pattern.search(text) for pattern in self.exclusion_regex)
    
    def _analyze_time_sequence(self, stem: str, options: Dict[str, str]) -> Optional[ExceptionContext]:
        """Analyze time sequence exception"""
        # Look for completed actions
        completed_actions = []
        
        # Common completed action patterns
        completed_patterns = [
            r'after (?:establishing|securing|checking) (?:the )?(airway|breathing|circulation)',
            r'has already (?:assessed|checked|completed|given)',
            r'following (?:initial|immediate) (assessment|intervention)',
        ]
        
        for pattern in completed_patterns:
            match = re.search(pattern, stem, re.IGNORECASE)
            if match:
                completed_actions.append(match.group(1) if match.lastindex else match.group(0))
        
        if completed_actions:
            return ExceptionContext(
                exception_type='time_sequence',
                confidence=0.9,
                reasoning=f"Actions already completed: {', '.join(completed_actions)}. Move to next priority.",
                red_flags=['time_sequence']
            )
        
        return None
    
    def _analyze_exclusion(self, stem: str, options: Dict[str, str]) -> Optional[ExceptionContext]:
        """Analyze exclusion exception - need to find WORST answer"""
        # This is a major deviation - we need to reverse our logic
        exclusion_match = any(pattern.search(stem) for pattern in self.exclusion_regex)
        
        if exclusion_match:
            # For exclusion questions, we typically want to find:
            # 1. The most aggressive/inappropriate intervention
            # 2. Something that could cause harm
            # 3. An action that violates safety
            
            return ExceptionContext(
                exception_type='exclusion',
                confidence=0.95,
                reasoning="EXCEPT question detected - looking for inappropriate/harmful option",
                red_flags=['exclusion', 'reverse_thinking']
            )
        
        return None
    
    def _detect_chronic_vs_new(self, stem: str, options: Dict[str, str]) -> Optional[ExceptionContext]:
        """Detect chronic vs new onset patterns"""
        chronic_matches = sum(1 for p in self.chronic_regex if p.search(stem))
        new_matches = sum(1 for p in self.new_regex if p.search(stem))
        
        # Also check options for chronic/new indicators
        for opt_text in options.values():
            chronic_matches += sum(1 for p in self.chronic_regex if p.search(opt_text))
            new_matches += sum(1 for p in self.new_regex if p.search(opt_text))
        
        if chronic_matches > 0 and new_matches > 0:
            return ExceptionContext(
                exception_type='chronic_vs_new',
                confidence=0.85,
                reasoning="Both chronic and new conditions present - prioritize NEW/ACUTE changes",
                red_flags=['chronic_vs_new', 'new_beats_chronic']
            )
        
        return None
    
    def _detect_special_context(self, stem: str, options: Dict[str, str]) -> Optional[ExceptionContext]:
        """Detect special contexts that change priority rules"""
        contexts_found = []
        
        for context_type, pattern in self.context_regex.items():
            if pattern.search(stem):
                contexts_found.append(context_type)
        
        if contexts_found:
            context_rules = {
                'psych': "Psychological safety may override physiological in psych settings",
                'pediatric': "Developmental and family considerations affect priorities",
                'cultural': "Cultural competence may override clinical protocols",
                'legal': "Legal/ethical requirements may supersede clinical judgment"
            }
            
            reasoning = "; ".join([context_rules.get(c, "") for c in contexts_found])
            
            return ExceptionContext(
                exception_type='context_specific',
                confidence=0.8,
                reasoning=reasoning,
                red_flags=contexts_found
            )
        
        return None
    
    def _detect_red_flags(self, stem: str) -> List[str]:
        """Detect red flag phrases that warrant careful consideration"""
        red_flags = []
        for pattern in self.red_flag_regex:
            if pattern.search(stem):
                red_flags.append(pattern.pattern)
        return red_flags
    
    def apply_exception_rules(self, question_stem: str, options: Dict[str, str], 
                            base_prediction: Set[str], exception_contexts: List[ExceptionContext]) -> Set[str]:
        """Apply exception rules to modify base prediction"""
        
        if not exception_contexts:
            return base_prediction
        
        # Sort by confidence to apply highest confidence exception
        exception_contexts.sort(key=lambda x: x.confidence, reverse=True)
        primary_exception = exception_contexts[0]
        
        logger.info(f"Applying exception: {primary_exception.exception_type}")
        
        if primary_exception.exception_type == 'exclusion':
            # For EXCEPT questions, we need custom logic
            return self._handle_exclusion_exception(question_stem, options, base_prediction)
        
        elif primary_exception.exception_type == 'time_sequence':
            # Skip completed actions and move to next priority
            return self._handle_time_sequence_exception(question_stem, options, base_prediction)
        
        elif primary_exception.exception_type == 'chronic_vs_new':
            # Prioritize new/acute findings
            return self._handle_chronic_new_exception(question_stem, options, base_prediction)
        
        elif primary_exception.exception_type == 'context_specific':
            # Apply context-specific modifications
            return self._handle_context_exception(question_stem, options, base_prediction, primary_exception)
        
        # Default: return base prediction with warning
        logger.warning(f"Exception detected but no specific handler: {primary_exception}")
        return base_prediction
    
    def _handle_exclusion_exception(self, stem: str, options: Dict[str, str], 
                                   base_prediction: Set[str]) -> Set[str]:
        """Handle EXCEPT questions - find the WORST/inappropriate option"""
        
        # Patterns that indicate harmful/inappropriate actions
        harmful_patterns = [
            r'\b(force|restrain|ignore|delay|withhold)\b',
            r'\b(increase.*dose|double.*medication)\b',
            r'\b(leave.*alone|do nothing|wait)\b',
            r'\b(tell.*not to worry|dismiss)\b',
        ]
        
        harmful_regex = [re.compile(p, re.IGNORECASE) for p in harmful_patterns]
        
        # Score each option for potential harm
        harm_scores = {}
        for opt_key, opt_text in options.items():
            score = 0
            
            # Check for harmful patterns
            for pattern in harmful_regex:
                if pattern.search(opt_text):
                    score += 10
            
            # Check if it's the "most aggressive" intervention
            if any(word in opt_text.lower() for word in ['immediately', 'stat', 'emergency']):
                score += 5  # Too aggressive might be inappropriate
            
            harm_scores[opt_key] = score
        
        # Return option with highest harm score
        if harm_scores:
            worst_option = max(harm_scores.keys(), key=lambda k: harm_scores[k])
            if harm_scores[worst_option] > 0:
                return {worst_option}
        
        # Fallback: return option that's NOT in base prediction (reverse logic)
        all_options = set(options.keys())
        excluded = all_options - base_prediction
        if excluded:
            return {list(excluded)[0]}
        
        return base_prediction
    
    def _handle_time_sequence_exception(self, stem: str, options: Dict[str, str], 
                                      base_prediction: Set[str]) -> Set[str]:
        """Handle time sequence - skip completed actions"""
        
        # Identify what's been done
        completed_keywords = {
            'airway': ['airway', 'intubat', 'oxygen mask'],
            'breathing': ['breathing', 'ventilat', 'oxygen', 'respiratory'],
            'circulation': ['iv', 'fluid', 'blood', 'circul'],
        }
        
        completed = []
        stem_lower = stem.lower()
        
        for priority, keywords in completed_keywords.items():
            if any(f"after {kw}" in stem_lower or f"established {kw}" in stem_lower 
                   for kw in keywords):
                completed.append(priority)
        
        # Now look for next appropriate action
        # This would integrate with main algorithm to skip completed steps
        
        return base_prediction  # Simplified for now
    
    def _handle_chronic_new_exception(self, stem: str, options: Dict[str, str], 
                                    base_prediction: Set[str]) -> Set[str]:
        """Prioritize new/acute findings over chronic conditions"""
        
        new_option_scores = {}
        
        for opt_key, opt_text in options.items():
            score = 0
            
            # Check for new/acute indicators in options
            if any(pattern.search(opt_text) for pattern in self.new_regex):
                score += 10
            
            # Check for assessment keywords (new conditions need assessment)
            if re.search(r'\b(assess|evaluat|check|investigat)\b', opt_text, re.IGNORECASE):
                score += 5
            
            new_option_scores[opt_key] = score
        
        # Return option with highest "new" score
        if new_option_scores:
            best_new = max(new_option_scores.keys(), key=lambda k: new_option_scores[k])
            if new_option_scores[best_new] > 5:
                return {best_new}
        
        return base_prediction
    
    def _handle_context_exception(self, stem: str, options: Dict[str, str], 
                                base_prediction: Set[str], context: ExceptionContext) -> Set[str]:
        """Handle context-specific exceptions"""
        
        if 'psych' in context.red_flags:
            # In psych context, safety includes psychological safety
            safety_patterns = [
                r'\b(suicid|self-harm|harm.*self|safety|one-to-one|constant observation)\b',
                r'\b(therapeutic|de-escalat|calm|rapport)\b',
            ]
            
            for opt_key, opt_text in options.items():
                if any(re.search(p, opt_text, re.IGNORECASE) for p in safety_patterns):
                    return {opt_key}
        
        elif 'legal' in context.red_flags:
            # Legal/ethical considerations
            legal_patterns = [
                r'\b(respect|autonomy|consent|right|ethic)\b',
                r'\b(document|inform|explain)\b',
            ]
            
            for opt_key, opt_text in options.items():
                if any(re.search(p, opt_text, re.IGNORECASE) for p in legal_patterns):
                    return {opt_key}
        
        return base_prediction

# Integration function to add to main framework
def enhance_flowchart_with_exceptions(flowchart_instance):
    """Enhance existing flowchart with exception handling"""
    
    # Add exception handler
    flowchart_instance.exception_handler = NCLEXExceptionHandler()
    
    # Override predict method
    original_predict = flowchart_instance.predict
    
    def enhanced_predict(question):
        # Detect exceptions first
        exceptions = flowchart_instance.exception_handler.detect_exceptions(
            question.stem, question.options
        )
        
        # Get base prediction
        base_prediction = original_predict(question)
        
        # Log exceptions if found
        if exceptions:
            flowchart_instance._log(f"Exceptions detected: {[e.exception_type for e in exceptions]}")
            for exc in exceptions:
                flowchart_instance._log(f"  - {exc.exception_type}: {exc.reasoning}")
        
        # Apply exception rules if needed
        if exceptions:
            modified_prediction = flowchart_instance.exception_handler.apply_exception_rules(
                question.stem, question.options, base_prediction, exceptions
            )
            
            if modified_prediction != base_prediction:
                flowchart_instance._log(f"Prediction modified: {base_prediction} -> {modified_prediction}")
            
            return modified_prediction
        
        return base_prediction
    
    # Replace method
    flowchart_instance.predict = enhanced_predict
    
    return flowchart_instance
