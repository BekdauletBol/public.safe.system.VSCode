import pandas as pd
import matplotlib.pyplot as plt
import glob, os

def plot():
    files = glob.glob("data/phase-1/*_metrics.csv")
    if not files: return
    
    df = pd.read_csv(files[0])
    
    fig, ax = plt.subplots(2, 1, figsize=(10, 10))
    
    ax[0].plot(df['fps'], color='blue', label='Current FPS')
    ax[0].axhline(y=30, color='red', linestyle='--', label='Target')
    ax[0].set_title("Streaming Stability (FPS)")
    ax[0].legend()
    
    # Формула: (FPS / Target) * 0.7 + (Stability) * 0.3
    health = (df['fps'] / 30 * 100).clip(0, 100)
    ax[1].fill_between(range(len(health)), health, color='green', alpha=0.3)
    ax[1].set_title("System Health Index (%)")
    ax[1].set_ylim(0, 110)
    
    plt.tight_layout()
    plt.savefig("analysis/system_health/v1_health.png")
    print("Графики сохранены в analysis/")

if __name__ == "__main__":
    plot()