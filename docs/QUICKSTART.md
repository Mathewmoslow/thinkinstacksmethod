# TISM Quick Start Guide

## Installation

```bash
pip install -e .
```

## Basic Usage

```python
from tism_package import TISMTreeFinal, NCLEXQuestion

# Create TISM instance
tism = TISMTreeFinal()

# Create a question
question = NCLEXQuestion(
    id="q1",
    stem="Client found unresponsive with no pulse. First action?",
    options={
        'A': 'Check glucose',
        'B': 'Start compressions',
        'C': 'Call for help',
        'D': 'Check pupils'
    },
    correct_answers={'B'},
    format='single',
    question_type='priority'
)

# Get prediction
prediction = tism.predict(question)
print(f"TISM predicts: {prediction}")
```

## The 4-Stack Framework

1. **Life Threats (ABC+D)**
   - Airway
   - Breathing
   - Circulation
   - Disability (neuro)

2. **Safety**
   - Falls
   - Infection
   - Violence

3. **Physical Needs**
   - Glucose (minutes)
   - Elimination/Pain (hours)
   - Nutrition (days)

4. **Nursing Process**
   - Assessment wins ties!

## Tips

- Look for explicit priority keywords
- Remember ABC+D always comes first
- When in doubt, assess first
- Physical needs are time-based