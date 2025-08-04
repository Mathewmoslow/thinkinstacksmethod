"""Think In Stacks Method (TISM) Package

A validated framework for nursing clinical decision-making
"""

__version__ = "1.0.0"
__author__ = "Mathew Moslow"
__license__ = "MIT"

# Import main components for easy access
from .core.tism_tree_final import TISMTreeFinal, StudentQuickReference
from .core.nclex_validation_framework import NCLEXQuestion

__all__ = [
    'TISMTreeFinal',
    'StudentQuickReference',
    'NCLEXQuestion'
]