import os
import sys
import joblib
from typing import Optional, Dict

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from router.rule_engine import RuleEngine
from router.semantic_cache import SemanticCache

class ClassifierEngine:
    """
    ML-based complexity classifier that uses trained Logistic Regression
    on top of prompt embeddings. Falls back to RuleEngine if model is not trained.
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "classifier_model.joblib")
        )
        self.model_loaded = False
        self.model_data = None
        self.classifier = None
        
        # Instantiate fallback rule engine
        self.rule_fallback = RuleEngine()
        
        # Initialize semantic cache as helper for generating embeddings
        self.cache_helper = SemanticCache()

        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model_data = joblib.load(self.model_path)
                self.classifier = self.model_data["classifier"]
                self.model_loaded = True
                print(f"Successfully loaded ML classifier model from {self.model_path}")
            except Exception as e:
                print(f"Failed to load ML model from {self.model_path}: {e}. Falling back to Rule Engine.")
                self.model_loaded = False
        else:
            print(f"ML model file not found at {self.model_path}. Rule Engine will be used as fallback.")

    def get_complexity_label(self, prompt: str) -> str:
        """
        Predicts complexity (LOW, MEDIUM, HIGH) using the trained Logistic Regression model.
        Falls back to the Rule Engine if the ML model is not available.
        """
        if not self.model_loaded or not self.classifier:
            return self.rule_fallback.get_complexity_label(prompt)
            
        try:
            # 1. Generate prompt embedding
            embedding = self.cache_helper.get_embedding(prompt)
            
            # 2. Predict using the classifier
            prediction = self.classifier.predict([embedding])[0]
            return str(prediction)
        except Exception as e:
            print(f"ML prediction error: {e}. Falling back to Rule Engine.")
            return self.rule_fallback.get_complexity_label(prompt)

    def get_complexity_score(self, prompt: str) -> float:
        """
        Estimated score based on ML model decision function margin or fallback to rules.
        """
        if not self.model_loaded or not self.classifier:
            return self.rule_fallback.calculate_score(prompt)
            
        try:
            # We can use decision_function or predict_proba to map to a 1.0 - 10.0 score
            embedding = self.cache_helper.get_embedding(prompt)
            probs = self.classifier.predict_proba([embedding])[0] # probability of [HIGH, LOW, MEDIUM] (alphabetical)
            
            # Map probabilities to a 1.0 to 10.0 score range
            # Classes are likely ['HIGH', 'LOW', 'MEDIUM']
            class_probs = dict(zip(self.classifier.classes_, probs))
            
            # Weighted average mapping:
            # LOW = 2.0, MEDIUM = 5.5, HIGH = 8.5
            score = (
                class_probs.get("LOW", 0.0) * 2.0 +
                class_probs.get("MEDIUM", 0.0) * 5.5 +
                class_probs.get("HIGH", 0.0) * 8.5
            )
            return float(score)
        except Exception:
            return self.rule_fallback.calculate_score(prompt)

    def get_explanation(self, prompt: str) -> Dict[str, float]:
        """
        Returns the rule-based features explanation for debugging or user display.
        """
        return self.rule_fallback.explain_complexity(prompt)["explanation"]
