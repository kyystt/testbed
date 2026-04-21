import pandas as pd

# Carrega os globais para vermos o resumo
df_b = pd.read_csv("super_baseline_benign.csv")['global_delta_ms'].dropna()
df_a = pd.read_csv("super_baseline_attack.csv")['global_delta_ms'].dropna()

print("=== BENIGN STATS ===")
print(df_b.describe())
print(f"Variance: {df_b.var():.6f}")

print("\n=== ATTACK STATS ===")
print(df_a.describe())
print(f"Variance: {df_a.var():.6f}")
