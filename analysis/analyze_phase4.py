import pandas as pd
import matplotlib.pyplot as plt

def analyze():
    df = pd.read_csv("data/phase-4/e2e_latency.csv")
    
    fig, ax = plt.subplots(2, 1, figsize=(12, 10))
    
    # 1. End-to-End Latency
    ax[0].plot(df['e2e_latency_ms'], color='green')
    ax[0].axhline(y=100, color='r', linestyle='--', label='SLA Limit (100ms)')
    ax[0].set_title("End-to-End System Latency (ms)")
    ax[0].legend()
    
    # 2. Интегральный график System Health v4.0 (Performance vs Reliability)
    # Формула: Health = (1 - (Latency / 200)) * 100
    health = (1 - (df['e2e_latency_ms'] / 200)).clip(0, 1) * 100
    ax[1].fill_between(range(len(health)), health, color='lime', alpha=0.3)
    ax[1].set_title("System Health Index v4.0 (E2E Efficiency)")
    
    plt.tight_layout()
    plt.savefig("analysis/system_health/v4_health.png")

if __name__ == "__main__":
    analyze()