import pandas as pd
import matplotlib.pyplot as plt

def analyze():
    df = pd.read_csv("data/phase-2/ml_metrics.csv")
    
    fig, ax = plt.subplots(2, 1, figsize=(12, 10))
    
    # 1. Инференс задержка
    ax[0].plot(df['inf_time_ms'], color='purple', label='YOLO MPS Latency')
    ax[0].axhline(y=33, color='r', linestyle='--', label='30 FPS Limit (33ms)')
    ax[0].set_title("ML Inference Latency on Apple Silicon (MPS)")
    ax[0].set_ylabel("Milliseconds")
    ax[0].legend()
    
    ml_health = (33 / df['inf_time_ms'] * 100).clip(0, 100)
    ax[1].fill_between(range(len(ml_health)), ml_health, color='cyan', alpha=0.4)
    ax[1].set_title("System Health Index v2.0 (Inference Performance)")
    ax[1].set_ylim(0, 110)
    
    plt.tight_layout()
    plt.savefig("analysis/system_health/v2_health.png")
    print("📈 График Фазы 2 сохранен.")

if __name__ == "__main__":
    analyze()