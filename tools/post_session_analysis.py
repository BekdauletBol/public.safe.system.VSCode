import pandas as pd
import matplotlib.pyplot as plt
import os

def run_analysis():
    path = "data/final/system_stats.csv"
    if not os.path.exists(path):
        print("Error: No data found for analysis.")
        return

    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    plt.figure(figsize=(12, 8))

    # 1. CPU & Latency Correlation
    plt.subplot(2, 1, 1)
    plt.plot(df['timestamp'], df['cpu_usage'], label='CPU Load (%)', color='orange')
    plt.ylabel('CPU %')
    plt.twinx()
    plt.plot(df['timestamp'], df['latency_ms'], label='E2E Latency (ms)', color='blue')
    plt.ylabel('Latency (ms)')
    plt.title('System Resources & Performance Correlation')
    plt.legend()

    # 2. Violations Timeline
    plt.subplot(2, 1, 2)
    plt.fill_between(df['timestamp'], df['violations'], color='red', alpha=0.3)
    plt.ylabel('Person Count in Zone')
    plt.title('Security Breach Timeline')

    plt.tight_layout()
    plt.savefig("analysis/final_session_report.png")
    print("✅ Post-session analysis saved to analysis/final_session_report.png")

if __name__ == "__main__":
    run_analysis()