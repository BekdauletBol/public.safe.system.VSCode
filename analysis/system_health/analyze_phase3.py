import pandas as pd
import matplotlib.pyplot as plt

def analyze():
    df = pd.read_csv("data/phase-3/violations.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig, ax = plt.subplots(2, 1, figsize=(12, 10))
    
    # 1. Интенсивность нарушений
    df.set_index('timestamp').resample('1S').count()['in_zone'].plot(ax=ax[0], color='red')
    ax[0].set_title("Violation Frequency (Alarms per Second)")
    
    # 2. Интегральный график System Health v3.0
    # Формула: Health = 100 - (Violations_Trend * Коэффициент_риска)
    health = 100 - (df['in_zone'].rolling(window=20).sum().fillna(0) * 5)
    ax[1].fill_between(range(len(health)), health.clip(0, 100), color='orange', alpha=0.4)
    ax[1].set_title("System Security Health Index (Risk Level)")
    
    plt.tight_layout()
    plt.savefig("analysis/system_health/v3_health.png")

if __name__ == "__main__":
    analyze()