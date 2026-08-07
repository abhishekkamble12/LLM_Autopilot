from prometheus_client import Counter, Histogram, Gauge

# Business Metrics
llm_cost_total = Counter(
    "llm_cost_total", 
    "Total estimated cost of LLM calls in USD",
    ["provider", "model"]
)

llm_savings_total = Counter(
    "llm_savings_total",
    "Total estimated savings (vs baseline Claude 3.5 Sonnet) in USD",
    ["provider", "model"]
)

# Operational Metrics
llm_request_latency_seconds = Histogram(
    "llm_request_latency_seconds",
    "Latency of LLM requests in seconds",
    ["provider", "model"]
)

llm_token_usage_total = Counter(
    "llm_token_usage_total",
    "Total tokens processed (prompt + completion)",
    ["provider", "model", "token_type"] # token_type: prompt or completion
)

llm_provider_errors_total = Counter(
    "llm_provider_errors_total",
    "Total errors encountered from LLM providers",
    ["provider", "model", "error_type"]
)

llm_escalations_total = Counter(
    "llm_escalations_total",
    "Total number of times a prompt was escalated/retried to another model due to error",
    ["original_model"]
)

# Caching Metrics
llm_cache_hits_total = Counter(
    "llm_cache_hits_total",
    "Total cache lookups",
    ["status"] # hit or miss
)
