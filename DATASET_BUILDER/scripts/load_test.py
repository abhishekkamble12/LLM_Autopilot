import os
import sys
import time
import asyncio
import random
import numpy as np
import argparse

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from router.intelligent_router import IntelligentRouter

# Workload Pool simulating realistic production prompts
MIXED_WORKLOAD_PROMPTS = [
    # Simple / Low Complexity
    "What is the capital of France?",
    "How do you say hello in Spanish?",
    "What is 15 multiplied by 8?",
    "Name three primary colors.",
    "What is the boiling point of water in Celsius?",
    
    # Medium Complexity / SQL & Formatting
    "Write a SQL query to select all users who registered in the last 30 days and ordered over $100.",
    "Format this JSON data into a clean HTML table structure.",
    "Write a Python function to check if a string is a palindrome.",
    "Summarize the key differences between REST APIs and GraphQL in bullet points.",
    "Explain how Docker containers differ from Virtual Machines in 3 paragraphs.",
    
    # High Complexity / System Architecture & Coding
    "Design a scalable, fault-tolerant real-time chat application architecture using WebSockets, Kafka, Redis, and Cassandra. Explain partition strategies.",
    "Write a complete Rust implementation of a thread pool with worker threads, job channels, and shutdown signal handling.",
    "Analyze the security vulnerabilities of JWT tokens stored in localStorage vs httpOnly cookies and detail mitigation strategies for XSS and CSRF.",
    "Create a Kubernetes Deployment manifest with readiness probes, liveness probes, resource limits, and ingress routing rules for a Node.js microservice.",
    "Derive the time and space complexity of Dijkstra's algorithm using a Min-Heap priority queue versus an Adjacency Matrix."
]

class MockProvider:
    """Mock provider for high-speed load testing without API credit limitations."""
    def __init__(self, latency_ms: float = 20.0):
        self.latency_ms = latency_ms

    async def chat(self, prompt: str) -> str:
        # Simulate realistic provider inference delay (15-50ms)
        await asyncio.sleep(random.uniform(0.015, 0.050))
        return f"Simulated high-performance LLM response for: {prompt[:30]}..."

async def run_worker(router: IntelligentRouter, prompt_queue: asyncio.Queue, results: list):
    while not prompt_queue.empty():
        try:
            prompt = await prompt_queue.get()
            start_time = time.time()
            
            # Execute router
            res = await router.route(prompt)
            
            latency = (time.time() - start_time) * 1000.0  # convert to ms
            
            results.append({
                "latency_ms": latency,
                "cost": res.get("cost", 0.0),
                "savings": res.get("savings", 0.0),
                "complexity": res.get("complexity_label", "UNKNOWN"),
                "model": res.get("model_used", "UNKNOWN")
            })
        except Exception as e:
            results.append({"error": str(e)})
        finally:
            prompt_queue.task_done()

async def run_load_test(num_requests: int = 1000, concurrency: int = 50):
    print(f"\n=======================================================")
    print(f"🚀 STARTING LOAD TEST: {num_requests:,} REQUESTS (Concurrency: {concurrency})")
    print(f"=======================================================\n")

    # Initialize Router
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models.yaml'))
    router = IntelligentRouter(models_config_path=config_path)

    # Patch providers with fast mock providers for pure router throughput testing
    for key in router.providers:
        router.providers[key] = MockProvider()

    # Build queue with mixed workload distribution
    queue = asyncio.Queue()
    for _ in range(num_requests):
        # 30% chance of repeating a recent prompt to test Semantic Cache lookups
        if random.random() < 0.30 and queue.qsize() > 5:
            prompt = random.choice(MIXED_WORKLOAD_PROMPTS[:5])
        else:
            prompt = random.choice(MIXED_WORKLOAD_PROMPTS)
        await queue.put(prompt)

    results = []
    start_test_time = time.time()

    # Launch concurrent worker tasks
    workers = [
        asyncio.create_task(run_worker(router, queue, results))
        for _ in range(concurrency)
    ]

    await queue.join()
    for w in workers:
        w.cancel()

    total_test_duration = time.time() - start_test_time

    # Calculate Benchmark Metrics
    successful_results = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    latencies = [r["latency_ms"] for r in successful_results]
    costs = [r["cost"] for r in successful_results]
    savings = [r["savings"] for r in successful_results]

    p50 = np.percentile(latencies, 50) if latencies else 0
    p90 = np.percentile(latencies, 90) if latencies else 0
    p95 = np.percentile(latencies, 95) if latencies else 0
    p99 = np.percentile(latencies, 99) if latencies else 0
    avg_latency = np.mean(latencies) if latencies else 0

    total_cost = sum(costs)
    total_savings = sum(savings)
    avg_cost_per_req = total_cost / len(successful_results) if successful_results else 0
    avg_savings_per_req = total_savings / len(successful_results) if successful_results else 0
    rps = len(results) / total_test_duration

    # Category distributions
    complexities = {}
    for r in successful_results:
        c = r["complexity"]
        complexities[c] = complexities.get(c, 0) + 1

    # Print Final Benchmark Report
    print(f"📊 LOAD TESTING RESULTS SUMMARY")
    print(f"-------------------------------------------------------")
    print(f"Total Requests Completed: {len(results):,}")
    print(f"Successful Requests:      {len(successful_results):,}")
    print(f"Failed Requests:          {len(errors):,}")
    print(f"Test Duration:            {total_test_duration:.2f} seconds")
    print(f"Throughput (RPS):         {rps:.2f} requests/sec")
    print(f"-------------------------------------------------------")
    print(f"⏱️ LATENCY METRICS (ms)")
    print(f"  - Average Latency:      {avg_latency:.2f} ms")
    print(f"  - P50 Latency (Median): {p50:.2f} ms")
    print(f"  - P90 Latency:          {p90:.2f} ms")
    print(f"  - P95 Latency:          {p95:.2f} ms ⭐")
    print(f"  - P99 Latency:          {p99:.2f} ms")
    print(f"-------------------------------------------------------")
    print(f"💰 FINANCIAL COST METRICS")
    print(f"  - Total Spent:          ${total_cost:.5f}")
    print(f"  - Total Savings Generated: +${total_savings:.5f}")
    print(f"  - Average Cost / Request: ${avg_cost_per_req:.6f}")
    print(f"  - Average Savings / Req:  +${avg_savings_per_req:.6f}")
    print(f"-------------------------------------------------------")
    print(f"🏷️ ROUTING COMPLEXITY DISTRIBUTION")
    for comp, count in complexities.items():
        pct = (count / len(successful_results)) * 100
        print(f"  - {comp}: {count:,} ({pct:.1f}%)")
    print(f"=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Load testing script for LLM Autopilot Router.")
    parser.add_argument("--requests", "-r", type=int, default=1000, help="Number of total requests (default: 1000)")
    parser.add_argument("--concurrency", "-c", type=int, default=50, help="Number of concurrent workers (default: 50)")
    args = parser.parse_args()

    asyncio.run(run_load_test(num_requests=args.requests, concurrency=args.concurrency))

if __name__ == "__main__":
    main()
