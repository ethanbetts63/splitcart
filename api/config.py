# api/config.py

"""
Central configuration for substitution generation and savings benchmark parameters.
"""

# --- Semantic Matching Parameters ---

# Threshold for semantic substitution matching.
# Used in: api/utils/substitution_utils/lvl3_substitution_generator.py
#          api/utils/substitution_utils/lvl4_substitution_generator.py
SEMANTIC_SIMILARITY_THRESHOLD = 0.75


# --- Savings Benchmark Parameters ---

# Max depth for the on-the-fly transitive substitution search.
# Used in: api/utils/analysis_utils/savings_benchmark.py
SUBSTITUTION_SEARCH_DEPTH = 3

# Max number of substitutes to include in the portfolio for each cart item.
# Used in: api/utils/analysis_utils/savings_benchmark.py
SUBSTITUTION_PORTFOLIO_CAP = 4

# Size tolerance (e.g., 0.3 for 30%) for finding compatible substitutes.
# Used in: api/utils/analysis_utils/savings_benchmark.py
SUBSTITUTION_SIZE_TOLERANCE = 0.3

# The number of substitutes in a group required to trigger the price culling step.
# Used in: api/utils/analysis_utils/savings_benchmark.py
PRICE_CULLING_THRESHOLD = 20
