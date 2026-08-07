import re
from typing import Dict, Any

class RuleEngine:
    """
    Explainable, heuristics-based complexity engine that extracts features
    from a prompt, scores complexity from 1.0 to 10.0, and maps it to
    LOW, MEDIUM, or HIGH tiers. Returns explanations for why scores are assigned.
    """

    def __init__(self):
        # Feature 2: Constraints regex
        self.constraint_words = re.compile(
            r'\b(must|should|include|without|except|using|avoid|limit|restrict|prevent|constraint|strictly)\b', 
            re.IGNORECASE
        )
        
        # Feature 3: Task transitions
        self.task_words = re.compile(
            r'\b(and|then|also|after|finally|next|subsequently|first|second|third)\b', 
            re.IGNORECASE
        )
        
        # Feature 4: Output formats
        self.output_formats = re.compile(
            r'\b(json|xml|yaml|csv|mermaid|markdown table|table|graph|diagram|format as|output format)\b', 
            re.IGNORECASE
        )
        
        # Feature 5: Structured languages
        self.structured_langs = re.compile(
            r'\b(sql|html|css|json|xml|csv|yaml|ini|toml)\b', 
            re.IGNORECASE
        )
        
        # Feature 6: Reasoning verbs
        self.high_reasoning_verbs = re.compile(
            r'\b(analyze|critique|design|optimize|debug|refactor|architect|benchmark|diagnose|audit|troubleshoot|evaluate)\b', 
            re.IGNORECASE
        )
        self.med_reasoning_verbs = re.compile(
            r'\b(compare|contrast|calculate|convert|assess|estimate|summarize|explain)\b', 
            re.IGNORECASE
        )
        
        # Feature 7: Input comparison indicators
        self.comparison_indicators = re.compile(
            r'\b(difference|comparison|compare|versus|vs|between|list of|multiple|resumes|options|alternatives)\b', 
            re.IGNORECASE
        )
        
        # Feature 8: Code detection regex
        self.code_keywords = re.compile(
            r'\b(class|def|function|fn|import|const|let|var|return|public|private|void|int|str|float|list|dict)\b'
        )
        self.code_symbols = re.compile(
            r'([{}[\];]{2,}|->|=>|::|==|!=|\+=|-=|\*=|\/=|//|/\*|\*/)'
        )

        # Feature 9: Question indicators
        self.question_words = re.compile(
            r'\b(how|why|what|explain how|how do i|how can)\b', 
            re.IGNORECASE
        )
        self.complex_domain_words = re.compile(
            r'\b(concurrency|scale|throughput|performance|bottleneck|security|asynchronous|distributed|latency|deadlock)\b', 
            re.IGNORECASE
        )

    def explain_complexity(self, prompt: str) -> Dict[str, Any]:
        """
        Extracts features from the prompt and calculates the complexity score,
        returning a breakdown of why the score was assigned.
        """
        if not prompt or not prompt.strip():
            return {
                "score": 1.0,
                "tier": "LOW",
                "explanation": {"empty_prompt": 0.0}
            }

        explanation = {}
        base_score = 1.0
        
        # --- Feature 1: Prompt Length & Token Count ---
        words = prompt.split()
        word_count = len(words)
        length_score = 0.0
        if word_count > 150:
            length_score = 2.0
            explanation["long_prompt_large"] = length_score
        elif word_count > 75:
            length_score = 1.2
            explanation["long_prompt_medium"] = length_score
        elif word_count > 25:
            length_score = 0.5
            explanation["long_prompt_small"] = length_score
        elif word_count < 10:
            length_score = -0.5
            explanation["short_prompt"] = length_score

        # --- Feature 2: Constraints & Instruction Density ---
        constraint_word_matches = len(self.constraint_words.findall(prompt))
        # Lines starting with bullet or numbered list indicators
        list_indicators = len(re.findall(r'(?m)^(\s*[-*+]\s+|\s*\d+\.\s+)', prompt))
        total_constraints = constraint_word_matches + list_indicators
        if total_constraints > 0:
            constraint_score = min(2.5, total_constraints * 0.4)
            explanation["multiple_constraints"] = round(constraint_score, 2)
        else:
            constraint_score = 0.0

        # --- Feature 3: Tasks and Transitions (Multi-stage reasoning) ---
        task_matches = len(self.task_words.findall(prompt))
        if task_matches > 0:
            task_score = min(1.5, task_matches * 0.3)
            explanation["multiple_tasks"] = round(task_score, 2)
        else:
            task_score = 0.0

        # --- Feature 4: Output Format Complexity ---
        output_matches = len(self.output_formats.findall(prompt))
        if output_matches > 0:
            output_score = 1.0
            explanation["complex_output_format"] = output_score
        else:
            output_score = 0.0

        # --- Feature 5: Structured Data Languages ---
        struct_matches = len(self.structured_langs.findall(prompt))
        if struct_matches > 0:
            struct_score = 0.8
            explanation["structured_language_use"] = struct_score
        else:
            struct_score = 0.0

        # --- Feature 6: Cognitive Reasoning Depth ---
        high_verbs = len(self.high_reasoning_verbs.findall(prompt))
        med_verbs = len(self.med_reasoning_verbs.findall(prompt))
        reasoning_score = 0.0
        if high_verbs > 0:
            reasoning_score = 1.5
            explanation["high_cognitive_reasoning"] = reasoning_score
        elif med_verbs > 0:
            reasoning_score = 0.7
            explanation["medium_cognitive_reasoning"] = reasoning_score

        # --- Feature 7: Input Comparison / Multiple Entites ---
        comparison_matches = len(self.comparison_indicators.findall(prompt))
        if comparison_matches > 0:
            comp_score = 0.8
            explanation["requires_comparison"] = comp_score
        else:
            comp_score = 0.0

        # --- Feature 8: Code Structure Detection ---
        code_kw_matches = len(self.code_keywords.findall(prompt))
        code_sym_matches = len(self.code_symbols.findall(prompt))
        code_score = 0.0
        if code_kw_matches > 0 or code_sym_matches > 0:
            code_score = 1.5
            explanation["contains_code_patterns"] = code_score

        # --- Feature 9: Question Complexity & Domain Context ---
        is_question = len(self.question_words.findall(prompt)) > 0
        domain_complexity = len(self.complex_domain_words.findall(prompt))
        question_score = 0.0
        if is_question and domain_complexity > 0:
            question_score = 1.2
            explanation["complex_domain_question"] = question_score
        elif domain_complexity > 0:
            question_score = 0.6
            explanation["complex_domain_context"] = question_score

        # Calculate final raw score
        total_score = (
            base_score +
            length_score +
            constraint_score +
            task_score +
            output_score +
            struct_score +
            reasoning_score +
            comp_score +
            code_score +
            question_score
        )

        # Clip final score between 1.0 and 10.0
        final_score = round(max(1.0, min(10.0, total_score)), 2)

        # Assign tier
        if final_score < 4.0:
            tier = "LOW"
        elif final_score <= 7.0:
            tier = "MEDIUM"
        else:
            tier = "HIGH"

        return {
            "score": final_score,
            "tier": tier,
            "explanation": explanation
        }

    def calculate_score(self, prompt: str) -> float:
        return self.explain_complexity(prompt)["score"]

    def get_complexity_label(self, prompt: str) -> str:
        return self.explain_complexity(prompt)["tier"]
