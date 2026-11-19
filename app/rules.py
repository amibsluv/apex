# Official olympiad rules (from the Ministry of Education regulations).
# Changing a rule means changing one number here.

ROUNDS = {
    1: "Institutional",
    2: "District (city)",
    3: "Regional",
    4: "Republican",
}

# Minimum score to pass a round: 50% for general schools, 60% for new-type schools
PASS_MARK = {
    "general": 50,
    "new_type": 60,
}

# From round 3, 8 students per subject go to the republican round:
# 4 from new-type schools and 4 from general schools
REPUBLICAN_QUOTA = {
    "general": 4,
    "new_type": 4,
}

MAX_STUDENTS_PER_SCHOOL_IN_SUBJECT = 3
MAX_SUBJECTS_PER_STUDENT = 2
APPEAL_HOURS = 24          # appeals are allowed within 24 hours of the results
MIN_SCORE_FOR_APPEAL = 41  # students with 40 points or less cannot appeal
