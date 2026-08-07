import os
import yaml
from typing import Dict, Any, Optional

from router.classifier import ClassifierEngine
from providers import Openai_llm_provider, AnthropicProvider, GeminiProvider, OllamaProvider
import time 
import random
import asyncio
import numpy as np

from api.telemetry import (
    llm_cost_total, llm_savings_total, llm_request_latency_seconds,
    llm_token_usage_total, llm_provider_errors_total,
    llm_escalations_total, llm_cache_hits_total
)

class ProviderTracker:
    """Tracks rate limit cooldowns and health status for providers."""
    def __init__(self):
        self.cooldowns = {}  # { provider_name: cooldown_until_timestamp }

    def is_on_cooldown(self, provider_name: str) -> bool:
        cooldown_until = self.cooldowns.get(provider_name, 0)
        return time.time() < cooldown_until

    def set_cooldown(self, provider_name: str, seconds: int = 60):
        self.cooldowns[provider_name] = time.time() + seconds
        print(f"⚠️ Rate limit / error on '{provider_name}'. Cooldown set for {seconds}s.")

class IntelligentRouter:
    """
    Intelligent Router that loads models registry, predicts prompt complexity,
    selects the optimal provider/model to route to, and computes cost savings.
    """

    def __init__(self, models_config_path: str = "models.yaml"):
        # Load registry configuration
        if not os.path.exists(models_config_path):
            raise FileNotFoundError(f"Model registry file not found at {models_config_path}")
            
        with open(models_config_path, "r") as f:
            self.model_registry = yaml.safe_load(f)

        # Instantiate complexity engine (ML-based, falls back to rules)
        self.complexity_engine = ClassifierEngine()

        # Instantiate providers
        # We pass default parameters, models are overridden dynamically if needed
        self.providers = {
            "openai": Openai_llm_provider(name_model="openai/gpt-4o-mini"),
            "anthropic": AnthropicProvider(name_model="anthropic/claude-3.5-sonnet"),
            "gemini": GeminiProvider(name_model="google/gemini-flash-1.5"),
            "ollama": OllamaProvider(name_model="llama3")
        }

        # Instantiate semantic cache
        try:
            from router.semantic_cache import SemanticCache
            self.cache = SemanticCache()
        except Exception as e:
            print(f"Failed to initialize semantic cache: {e}. Caching disabled.")
            self.cache = None
        # Instantiate provider tracker for rate limit cooldowns
        self.tracker = ProviderTracker()  

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count based on standard English word-to-token ratio (1 word ~= 1.33 tokens)
        """
        if not text:
            return 0
        return int(len(text.split()) * 1.33)

    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost of a call using rates from models.yaml
        """
        model_meta = self.model_registry.get(model_name)
        if not model_meta:
            return 0.0
        
        input_cost = model_meta.get("input_cost_per_m", 0.0)
        output_cost = model_meta.get("output_cost_per_m", 0.0)
        
        cost = ((prompt_tokens * input_cost) + (completion_tokens * output_cost)) / 1000000.0
        return cost

    def select_model(self, complexity: str) -> str:
        """
        Map complexity label (LOW, MEDIUM, HIGH) to a model name in models.yaml
        """
        if complexity == "LOW":
            # Route to cheap Gemini Flash
            return "google/gemini-flash-1.5"
        elif complexity == "MEDIUM":
            # Route to cheap GPT-4o-mini
            return "openai/gpt-4o-mini"
        else:
            # Route to premium Claude 3.5 Sonnet
            return "anthropic/claude-3.5-sonnet"
    async def get_fallback_chain(self, complexity: str) -> list:
        if complexity == "LOW":
            return ["google/gemini-flash-1.5", "openai/gpt-4o-mini", "llama3", "anthropic/claude-3.5-sonnet"]
        elif complexity == "MEDIUM":
            return ["openai/gpt-4o-mini", "google/gemini-flash-1.5", "anthropic/claude-3.5-sonnet", "llama3"]
        else:
            return ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini", "google/gemini-flash-1.5", "llama3"]
    async def route(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Routes the prompt to the correct model based on rule-based complexity,
        calls the provider, and estimates costs and savings. Includes semantic caching.
        """
        # 0. Check Semantic Cache
        if self.cache:
            cache_result = await self.cache.lookup(prompt)
            if cache_result:
                llm_cache_hits_total.labels(status="hit").inc()
                return {
                    "log_id": cache_result["id"],
                    "response": cache_result["response"],
                    "complexity_label": "CACHED",
                    "complexity_score": 0.0,
                    "model_used": cache_result["model_used"] + " (Cached)",
                    "provider": "cache",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost": 0.0,
                    "savings": cache_result["savings"],
                    "explanation": {"semantic_cache_hit": 1.0}
                }
            else:
                llm_cache_hits_total.labels(status="miss").inc()

        # 1. Determine complexity
        complexity = self.complexity_engine.get_complexity_label(prompt)
        score = self.complexity_engine.get_complexity_score(prompt)

        # 2. Select optimal model
        selected_model = self.select_model(complexity)
        
        # 3. Retrieve model meta and provider instance
        model_meta = self.model_registry.get(selected_model)
        if not model_meta:
            raise ValueError(f"Selected model {selected_model} is missing from models.yaml")
        
        provider_name = model_meta.get("provider")
        provider_instance = self.providers.get(provider_name)
        if not provider_instance:
            raise ValueError(f"No provider instantiated for {provider_name}")

        # 4. Formulate message (combine system prompt and user prompt)
        message = prompt
        if system_prompt:
            message = f"System: {system_prompt}\nUser: {prompt}"

        # 5. Call LLM with Telemetry and Fallback
        start_time = time.time()
        response_text = None
        
        fallback_chain = await self.get_fallback_chain(complexity)
        if selected_model in fallback_chain:
            fallback_chain.remove(selected_model)
        fallback_chain.insert(0, selected_model)
        
        actual_model_used = selected_model
        actual_provider_name = provider_name
        
        for idx, model_to_try in enumerate(fallback_chain):
            try:
                meta = self.model_registry.get(model_to_try)
                if not meta: continue
                p_name = meta.get("provider")
                p_instance = self.providers.get(p_name)
                
                response_text = await p_instance.chat(message)
                if response_text:
                    actual_model_used = model_to_try
                    actual_provider_name = p_name
                    if idx > 0:
                        llm_escalations_total.labels(original_model=selected_model).inc()
                    break
            except Exception as e:
                llm_provider_errors_total.labels(provider=p_name, model=model_to_try, error_type=type(e).__name__).inc()
                continue
                
        latency = time.time() - start_time
        llm_request_latency_seconds.labels(provider=actual_provider_name, model=actual_model_used).observe(latency)

        if not response_text:
            response_text = "[Error: No response generated from provider or fallbacks]"
            
        selected_model = actual_model_used
        provider_name = actual_provider_name

        # 6. Estimate token counts and costs
        prompt_tokens = self._estimate_tokens(prompt)
        completion_tokens = self._estimate_tokens(response_text)
        
        actual_cost = self._calculate_cost(selected_model, prompt_tokens, completion_tokens)
        
        # Telemetry: Record usage and cost
        llm_token_usage_total.labels(provider=provider_name, model=selected_model, token_type="prompt").inc(prompt_tokens)
        llm_token_usage_total.labels(provider=provider_name, model=selected_model, token_type="completion").inc(completion_tokens)
        llm_cost_total.labels(provider=provider_name, model=selected_model).inc(actual_cost)
        
        # 7. Calculate Baseline Cost (if we always routed to Claude 3.5 Sonnet)
        baseline_model = "anthropic/claude-3.5-sonnet"
        baseline_cost = self._calculate_cost(baseline_model, prompt_tokens, completion_tokens)
        
        # 8. Calculate Savings
        savings = max(0.0, baseline_cost - actual_cost)
        llm_savings_total.labels(provider=provider_name, model=selected_model).inc(savings)

        # 9. Save to Semantic Cache
        log_id = None
        if self.cache:
            log_id = self.cache.insert(
                prompt=prompt,
                response=response_text,
                model_used=selected_model,
                cost=actual_cost,
                savings=savings
            )
            
        # 10. Asynchronously trigger Shadow Evaluation 5% of the time
        if selected_model != "anthropic/claude-3.5-sonnet" and random.random() < 0.05:
            asyncio.create_task(
                self.run_shadow_evaluation(prompt, selected_model, response_text)
            )

        return {
            "log_id": log_id,
            "response": response_text,
            "complexity_label": complexity,
            "complexity_score": score,
            "model_used": selected_model,
            "provider": provider_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": actual_cost,
            "savings": savings,
            "explanation": self.complexity_engine.get_explanation(prompt)
        }

    async def run_shadow_evaluation(self, prompt: str, cheap_model: str, cheap_response: str):
        """Runs asynchronously in the background so the user doesn't wait."""
        if not self.cache or not self.cache.db_connected:
            return
            
        try:
            # 1. Call Premium Model (Claude 3.5 Sonnet)
            premium_provider = self.providers.get("anthropic")
            premium_response = await premium_provider.chat(prompt)

            # 2. Compare embeddings of Cheap vs Premium response
            emb_cheap = self.cache.get_embedding(cheap_response)
            emb_premium = self.cache.get_embedding(premium_response)

            # Calculate cosine similarity score (0.0 to 1.0)
            similarity = float(np.dot(emb_cheap, emb_premium) / (np.linalg.norm(emb_cheap) * np.linalg.norm(emb_premium)))

            print(f"🕵️ Shadow Evaluation complete for prompt! Cheap vs Premium Similarity: {similarity:.2%}")
            
            # 3. Log to DB
            with self.cache.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO shadow_evaluations 
                    (prompt, cheap_model, cheap_response, premium_model, premium_response, similarity_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (prompt, cheap_model, cheap_response, "anthropic/claude-3.5-sonnet", premium_response, similarity)
                )
        except Exception as e:
            print(f"Shadow evaluation failed: {e}")