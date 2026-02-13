import pandas as pd
import matplotlib.pyplot as plt

def build_report():
    # Мы берем данные из логов (нужно добавить сохранение логов в ml_worker)
    # Для демонстрации создаем финальный интегральный график
    plt.figure(figsize=(12, 8), facecolor='#0b0c0e')
    ax = plt.gca()
    ax.set_facecolor('#0b0c0e')
    
    # Имитация данных для примера (в реальности берутся из CSV)
    time_points = range(100)
    fps = [28 + (np.random.rand()-0.5)*2 for _ in time_points]
    latency = [40 + (np.random.rand()-0.5)*10 for _ in time_points]
    
    plt.plot(time_points, fps, color='lime', label='System Stability (FPS)')
    plt.plot(time_points, latency, color='white', alpha=0.3, label='Response Time (ms)')
    
    plt.title("INTEGRAL SYSTEM HEALTH REPORT", color='white', fontsize=18)
    plt.legend()
    plt.grid(color='#222')
    plt.savefig("analysis/system_health/v7_health_integral.png")
    print("🏆 Integral Health Graph saved.")

if __name__ == "__main__":
    import numpy as np
    build_report()