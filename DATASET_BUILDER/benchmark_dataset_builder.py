import os
import sys
import json
import csv
import time
import yaml
import asyncio
import argparse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to sys.path so we can import providers and router
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from providers import Openai_llm_provider, AnthropicProvider, GeminiProvider, OllamaProvider

# Default Task Categories representing diverse real-world workloads
DEFAULT_CATEGORIES = {
    "System Design": {
        "tier_hint": "HIGH",
        "description": "Architecting large scale distributed systems, microservices, database scaling, high availability, or trade-off analysis."
    },
    "Creative Thinking": {
        "tier_hint": "MEDIUM",
        "description": "Creative writing, story generation, brain-storming product ideas, metaphor creation, or roleplaying."
    },
    "Coding": {
        "tier_hint": "HIGH",
        "description": "Complex programming problems, debugging tricky code blocks, writing algorithms, or refactoring logic."
    },
    "Math & Logic": {
        "tier_hint": "HIGH",
        "description": "Mathematical proofs, multi-step logic puzzles, statistical analysis, or probability calculations."
    },
    "Summarization": {
        "tier_hint": "MEDIUM",
        "description": "Condensing long articles, extracting key takeaways, or formatting bullet point executive summaries."
    },
    "Translation": {
        "tier_hint": "LOW",
        "description": "Translating text between languages, idiom conversion, or grammatical tone adjustment."
    },
    "SQL & Databases": {
        "tier_hint": "MEDIUM",
        "description": "Writing complex SQL queries, index optimization, schema design, or query tuning."
    }
}

class BenchmarkDatasetBuilder:
    def __init__(
        self, 
        models_config_path: str = "models.yaml",
        judge_provider_name: str = "openai",
        judge_model_name: str = "openai/gpt-4o-mini",
        quality_threshold: float = 7.0
    ):
        self.models_config_path = os.path.abspath(models_config_path)
        if not os.path.exists(self.models_config_path):
            raise FileNotFoundError(f"models.yaml not found at {self.models_config_path}")
            
        with open(self.models_config_path, "r") as f:
            self.model_registry = yaml.safe_load(f)

        self.quality_threshold = quality_threshold

        # Instantiate candidate providers
        self.providers = {
            "anthropic/claude-3.5-sonnet": Openai_llm_provider(name_model="anthropic/claude-3.5-sonnet", max_tokens=1000),
            "openai/gpt-4o": Openai_llm_provider(name_model="openai/gpt-4o", max_tokens=1000),
            "openai/o1-mini": Openai_llm_provider(name_model="openai/o1-mini", max_tokens=1000),
            "google/gemini-flash-1.5": Openai_llm_provider(name_model="google/gemini-flash-1.5", max_tokens=1000),
            "openrouter/auto": Openai_llm_provider(name_model="openrouter/auto", max_tokens=1000),
            "nvidia/nemotron-4-340b-instruct:free": Openai_llm_provider(name_model="nvidia/nemotron-4-340b-instruct:free", max_tokens=1000),
            "google/gemini-2.0-flash-exp:free": Openai_llm_provider(name_model="google/gemini-2.0-flash-exp:free", max_tokens=1000),
            "meta-llama/llama-3.1-8b-instruct": Openai_llm_provider(name_model="meta-llama/llama-3.1-8b-instruct", max_tokens=1000)
        }

        # Instantiate Judge Provider
        if judge_provider_name == "gemini":
            self.judge_provider = GeminiProvider(name_model=judge_model_name, max_tokens=1000)
        elif judge_provider_name == "anthropic":
            self.judge_provider = AnthropicProvider(name_model=judge_model_name, max_tokens=1000)
        else:
            self.judge_provider = Openai_llm_provider(name_model=judge_model_name, max_tokens=1000)

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return int(len(text.split()) * 1.33)

    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        model_meta = self.model_registry.get(model_name, {})
        input_cost = model_meta.get("input_cost_per_m", 0.0)
        output_cost = model_meta.get("output_cost_per_m", 0.0)
        return ((prompt_tokens * input_cost) + (completion_tokens * output_cost)) / 1000000.0

    async def generate_prompts_for_category(self, category: str, info: Dict[str, str], count: int) -> List[str]:
        print(f"Generating {count} prompts for category '{category}'...")
        prompt_message = (
            "Generate a JSON array of strings, and nothing else. Do not explain anything or write markdown code blocks.\n"
            f"The array should contain exactly {count} distinct real-world user prompts for the category '{category}'.\n"
            f"Description of category: {info['description']}\n\n"
            "Ensure the prompts vary in length, complexity, and specific sub-topics."
        )

        try:
            content = await self.judge_provider.chat(prompt_message)
            if not content:
                return []

            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            prompts = json.loads(content)
            if isinstance(prompts, list):
                return [str(p).strip() for p in prompts if p]
        except Exception as e:
            print(f"Failed to generate prompts for category '{category}': {e}")
        return []

    async def evaluate_single_model(self, model_name: str, provider_instance: Any, prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            response_text = await provider_instance.chat(prompt)
            latency = time.time() - start_time
            if not response_text:
                response_text = "[No response generated]"
        except Exception as e:
            latency = time.time() - start_time
            response_text = f"[Error: {str(e)}]"

        prompt_tokens = self._estimate_tokens(prompt)
        completion_tokens = self._estimate_tokens(response_text)
        cost = self._calculate_cost(model_name, prompt_tokens, completion_tokens)

        return {
            "model_name": model_name,
            "response": response_text,
            "latency": round(latency, 4),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": round(cost, 6)
        }

    async def judge_response_quality(self, prompt: str, response: str) -> float:
        """
        Uses LLM Judge to grade response on a scale of 1.0 to 10.0
        """
        judge_prompt = (
            "You are an objective AI Quality Evaluator. Grade the following AI response to the given user prompt.\n\n"
            f"USER PROMPT:\n{prompt}\n\n"
            f"AI RESPONSE:\n{response}\n\n"
            "Evaluate accuracy, depth, clarity, and instruction following.\n"
            "Respond ONLY with a JSON object in this exact format, no markdown:\n"
            "{\"quality_score\": <float from 1.0 to 10.0>, \"reasoning\": \"<short sentence>\"}"
        )

        try:
            content = await self.judge_provider.chat(judge_prompt)
            if not content:
                return 5.0

            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            parsed = json.loads(content)
            score = float(parsed.get("quality_score", 5.0))
            return max(1.0, min(10.0, score))
        except Exception as e:
            print(f"LLM Judge error: {e}. Defaulting score to 5.0")
            return 5.0

    async def process_prompt(self, prompt: str, category: str) -> Dict[str, Any]:
        # 1. Execute all candidate models
        tasks = []
        for model_name, provider_inst in self.providers.items():
            tasks.append(self.evaluate_single_model(model_name, provider_inst, prompt))

        model_results = await asyncio.gather(*tasks)
        
        # 2. Grade quality using LLM Judge for each candidate response
        for res in model_results:
            if res["response"].startswith("[Error") or res["response"] == "[No response generated]":
                res["quality"] = 1.0
            else:
                res["quality"] = await self.judge_response_quality(prompt, res["response"])

        # 3. Calculate max/min normalization factors for cost and latency
        costs = [r["cost"] for r in model_results]
        latencies = [r["latency"] for r in model_results]
        
        max_cost = max(costs) if max(costs) > 0 else 1.0
        max_latency = max(latencies) if max(latencies) > 0 else 1.0

        # 4. Calculate Composite Score for each model
        # Formula: Quality (60%) - Normalized Cost (25%) - Normalized Latency (15%)
        best_candidate = None
        highest_composite_score = -999.0

        for r in model_results:
            norm_cost = r["cost"] / max_cost if max_cost > 0 else 0.0
            norm_latency = r["latency"] / max_latency if max_latency > 0 else 0.0

            # Composite Score normalized out of 10
            composite = (r["quality"] * 0.70) - (norm_cost * 1.5) - (norm_latency * 1.0) + 3.0
            r["composite_score"] = round(composite, 4)

            # Check if model meets quality threshold
            passes_threshold = r["quality"] >= self.quality_threshold

            if passes_threshold:
                if composite > highest_composite_score:
                    highest_composite_score = composite
                    best_candidate = r
            
        # Fallback: if no model passed quality threshold, pick model with highest raw quality
        if not best_candidate:
            best_candidate = max(model_results, key=lambda x: (x["quality"], x["composite_score"]))

        # Build output row for CSV
        row = {
            "prompt": prompt,
            "category": category,
            "label": best_candidate["model_name"],      # ML Target Label
            "best_model": best_candidate["model_name"], # Optimal Model Identifier
            "best_provider": self.model_registry.get(best_candidate["model_name"], {}).get("provider", "unknown"),
            "best_score": best_candidate["composite_score"],
            "best_quality": best_candidate["quality"]
        }

        # Add detailed per-model features for model comparison
        for r in model_results:
            safe_name = r["model_name"].replace("/", "_").replace("-", "_")
            row[f"{safe_name}_quality"] = r["quality"]
            row[f"{safe_name}_latency"] = r["latency"]
            row[f"{safe_name}_cost"] = r["cost"]
            row[f"{safe_name}_composite"] = r["composite_score"]

        return row

async def main():
    parser = argparse.ArgumentParser(description="Generate ML-ready benchmark dataset for LLM Cost Autopilot router.")
    parser.add_argument("--prompts-file", "-f", type=str, default=None, help="Optional input CSV containing a 'prompt' column.")
    parser.add_argument("--count", "-c", type=int, default=5, help="Number of prompts to generate per category if no input file is given.")
    parser.add_argument("--judge-provider", type=str, default="openai", choices=["openai", "gemini", "anthropic"], help="LLM Judge provider.")
    parser.add_argument("--judge-model", type=str, default="openai/gpt-4o-mini", help="LLM Judge model identifier.")
    parser.add_argument("--quality-threshold", "-q", type=float, default=7.0, help="Minimum quality score (1-10) required for winning model candidate.")
    parser.add_argument("--output", "-o", type=str, default="data/model_benchmark_dataset.csv", help="Output CSV path.")
    
    args = parser.parse_args()

    builder = BenchmarkDatasetBuilder(
        judge_provider_name=args.judge_provider,
        judge_model_name=args.judge_model,
        quality_threshold=args.quality_threshold
    )

    prompts_to_process = [] # list of (prompt, category)

    if args.prompts_file and os.path.exists(args.prompts_file):
        print(f"Reading input prompts from {args.prompts_file}...")
        with open(args.prompts_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = row.get("prompt", "").strip()
                c = row.get("category", "General").strip()
                if p:
                    prompts_to_process.append((p, c))
    else:
        print("Generating benchmark prompts across categories...")
        for category, info in DEFAULT_CATEGORIES.items():
            cat_prompts = await builder.generate_prompts_for_category(category, info, args.count)
            for p in cat_prompts:
                prompts_to_process.append((p, category))

    if not prompts_to_process:
        print("No prompts found or generated. Exiting.")
        return

    print(f"\nProcessing total {len(prompts_to_process)} benchmark prompts across candidates...")
    results = []

    for idx, (prompt, category) in enumerate(prompts_to_process, 1):
        print(f"\n[{idx}/{len(prompts_to_process)}] Benchmarking Prompt: '{prompt[:60]}...' (Category: {category})")
        row = await builder.process_prompt(prompt, category)
        results.append(row)
        print(f" -> Best Model: {row['best_model']} (Quality: {row['best_quality']}/10.0, Score: {row['best_score']})")

    # Export to CSV
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    if results:
        fieldnames = list(results[0].keys())
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nSUCCESS! Benchmark dataset generated with {len(results)} records and saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
