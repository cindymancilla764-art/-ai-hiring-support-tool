import random

def score_candidate(text):
    return {
        "conscientiousness": random.randint(1, 10),
        "learning_goal_orientation": random.randint(1, 10),
    }
