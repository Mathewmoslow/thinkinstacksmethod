#!/usr/bin/env python3
"""
AI Knowledge Helper for TISM Tree
Uses OpenAI API to provide nursing knowledge context
"""

import os
import logging
from typing import Optional, Dict, List
import json

# Try to import required packages
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Silently continue - will use system environment variables
    pass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    # Silently continue - will use fallback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIKnowledgeHelper:
    """Enhanced knowledge helper using OpenAI API"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and os.getenv('TISM_AI_KNOWLEDGE', 'true').lower() == 'true'
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.3'))
        
        # Validate setup
        if self.enabled and not self._validate_setup():
            logger.warning("AI Knowledge Helper disabled due to missing configuration")
            self.enabled = False
        
        # Cache to avoid repeated API calls
        self.cache = {}
        
        # System prompt for nursing knowledge
        self.system_prompt = """You are a nursing education assistant helping with NCLEX preparation.
Your role is to provide factual nursing knowledge about interventions and their clinical purposes.
Be concise and focus on the primary clinical purpose of each intervention.
Do not see the actual questions - only provide knowledge about nursing concepts."""
    
    def _validate_setup(self) -> bool:
        """Validate API configuration"""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI package not installed. Run: pip install openai")
            return False
        
        if not self.api_key or self.api_key == 'your-api-key-here':
            logger.error("OpenAI API key not configured. Run: python setup_api_key.py")
            return False
        
        # Configure OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to configure OpenAI client: {e}")
            return False
    
    def get_intervention_purpose(self, intervention: str) -> Optional[str]:
        """Get the clinical purpose of an intervention using AI"""
        if not self.enabled:
            return None
        
        # Check cache first
        cache_key = f"purpose_{intervention.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"What is the primary clinical purpose of: {intervention}? Answer in 10 words or less, focusing on physiological effect."}
                ],
                temperature=self.temperature,
                max_tokens=50
            )
            
            purpose = response.choices[0].message.content.strip()
            
            # Categorize the purpose
            if any(word in purpose.lower() for word in ['breathing', 'oxygen', 'respiratory', 'airway']):
                result = 'breathing_intervention'
            elif any(word in purpose.lower() for word in ['circulation', 'blood', 'cardiac', 'heart']):
                result = 'circulation_intervention'
            elif any(word in purpose.lower() for word in ['safety', 'fall', 'harm', 'protect']):
                result = 'safety_intervention'
            elif any(word in purpose.lower() for word in ['neuro', 'brain', 'consciousness']):
                result = 'disability_intervention'
            else:
                result = purpose.lower().replace(' ', '_')
            
            # Cache the result
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"AI API error: {e}")
            return None
    
    def analyze_nursing_action(self, action: str) -> Dict[str, any]:
        """Get detailed analysis of a nursing action"""
        if not self.enabled:
            return {}
        
        # Check cache
        cache_key = f"analysis_{action.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            prompt = f"""Analyze this nursing action: "{action}"
            
Provide a JSON response with:
1. primary_system: which body system it primarily affects (respiratory/cardiovascular/neurological/safety/other)
2. priority_level: how urgent (immediate/urgent/routine)
3. clinical_purpose: main purpose in 10 words or less
4. is_assessment: true if this gathers data, false if it's an intervention"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=150
            )
            
            # Parse JSON response
            try:
                result = json.loads(response.choices[0].message.content)
                self.cache[cache_key] = result
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "primary_system": "unknown",
                    "priority_level": "routine",
                    "clinical_purpose": action,
                    "is_assessment": 'assess' in action.lower()
                }
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {}
    
    def is_knowledge_question(self, stem: str, options: Dict[str, str]) -> bool:
        """Determine if this is a knowledge vs action question"""
        if not self.enabled:
            return False
        
        # Use pattern matching (faster than API call)
        knowledge_indicators = [
            r'\b(normal.*range|value|finding|level)',
            r'\b(indicates|suggests|consistent with|sign of)',
            r'\b(understands|teaching.*effective|need.*further)',
            r'\b(characteristic|symptom|manifestation)',
        ]
        
        import re
        if any(re.search(p, stem, re.IGNORECASE) for p in knowledge_indicators):
            # Verify options are facts not actions
            action_count = 0
            for opt in options.values():
                if re.search(r'\b(assess|do|perform|administer|notify)', opt, re.IGNORECASE):
                    action_count += 1
            
            return action_count < len(options) / 2
        
        return False
    
    def clear_cache(self):
        """Clear the cache to free memory"""
        self.cache.clear()
        logger.info("AI knowledge cache cleared")

# Fallback to original knowledge helper if AI not available
class FallbackKnowledgeHelper:
    """Fallback knowledge helper using hardcoded rules"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        
        # Pre-loaded nursing knowledge
        self.nursing_facts = {
            'high_fowlers': 'breathing_intervention',
            'trendelenburg': 'circulation_intervention',
            'left_side_lying': 'circulation_intervention',
            'incentive_spirometry': 'breathing_intervention',
            'sequential_compression': 'circulation_intervention',
            'raise.*bed': 'breathing_intervention',
            'cold_application': 'circulation_intervention',
            'heat_application': 'circulation_intervention',
        }
    
    def get_intervention_purpose(self, intervention: str) -> Optional[str]:
        """Get intervention purpose using pattern matching"""
        if not self.enabled:
            return None
        
        intervention_lower = intervention.lower()
        
        # Check patterns
        import re
        for pattern, purpose in self.nursing_facts.items():
            if re.search(pattern, intervention_lower):
                return purpose
        
        # Basic categorization
        if any(word in intervention_lower for word in ['fowler', 'position', 'breathing', 'oxygen']):
            return 'breathing_intervention'
        elif any(word in intervention_lower for word in ['pressure', 'bleeding', 'circulation']):
            return 'circulation_intervention'
        elif any(word in intervention_lower for word in ['safety', 'alarm', 'fall']):
            return 'safety_intervention'
        
        return None
    
    def analyze_nursing_action(self, action: str) -> Dict[str, any]:
        """Basic analysis without AI"""
        return {
            "primary_system": "unknown",
            "priority_level": "routine",
            "clinical_purpose": action,
            "is_assessment": 'assess' in action.lower()
        }
    
    def is_knowledge_question(self, stem: str, options: Dict[str, str]) -> bool:
        """Pattern-based detection"""
        import re
        knowledge_patterns = [
            r'\b(normal|range|value|indicates|suggests)',
            r'\b(understands|teaching|characteristic)',
        ]
        return any(re.search(p, stem, re.IGNORECASE) for p in knowledge_patterns)
    
    def clear_cache(self):
        """No cache to clear"""
        pass

# Factory function to get appropriate helper
def get_knowledge_helper(use_ai: bool = True) -> object:
    """Get the best available knowledge helper"""
    if use_ai and OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
        helper = AIKnowledgeHelper(enabled=True)
        if helper.enabled:
            logger.info("Using AI Knowledge Helper with OpenAI")
            return helper
    
    logger.info("Using Fallback Knowledge Helper (no API)")
    return FallbackKnowledgeHelper(enabled=True)

if __name__ == "__main__":
    # Test the helper
    helper = get_knowledge_helper()
    
    test_interventions = [
        "Raise the head of bed to high-Fowler's position",
        "Apply direct pressure to bleeding site",
        "Administer oxygen via nasal cannula",
        "Check blood glucose level"
    ]
    
    print("Testing Knowledge Helper:\n")
    for intervention in test_interventions:
        purpose = helper.get_intervention_purpose(intervention)
        print(f"Intervention: {intervention}")
        print(f"Purpose: {purpose}")
        
        if hasattr(helper, 'analyze_nursing_action'):
            analysis = helper.analyze_nursing_action(intervention)
            print(f"Analysis: {analysis}")
        print()