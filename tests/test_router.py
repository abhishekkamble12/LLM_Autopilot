import pytest
from router.rule_engine import RuleEngine

def test_rule_engine_low_complexity():
    engine = RuleEngine()
    prompt = "Translate 'hello' to Spanish."
    score = engine.calculate_score(prompt)
    label = engine.get_complexity_label(prompt)
    
    assert score < 4.0
    assert label == "LOW"

def test_rule_engine_high_complexity():
    engine = RuleEngine()
    prompt = "Architect a microservices system design with def main() and class Database return statement."
    score = engine.calculate_score(prompt)
    label = engine.get_complexity_label(prompt)
    
    assert score >= 4.0

def test_empty_prompt():
    engine = RuleEngine()
    assert engine.calculate_score("") == 1.0
    assert engine.get_complexity_label("") == "LOW"
