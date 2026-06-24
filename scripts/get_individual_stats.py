import pandas as pd

pontos = ["plc", "bridge", "vfd"]

for ponto in pontos:
    print(f"\n=== ESTATÍSTICAS: INTERFACE {ponto.upper()} ===")
    try:
        # Puxamos o 'source_delta_ms' pois queremos o tempo isolado de 2.0ms
        df_b = pd.read_csv(f"../super_baseline_benign_{ponto}.csv")['source_delta_ms'].dropna()
        df_a = pd.read_csv(f"../super_baseline_attack_{ponto}.csv")['source_delta_ms'].dropna()
        
        print(f"BENIGN -> Min: {df_b.min():.4f} | Max: {df_b.max():.4f} | Variance: {df_b.var():.6f}")
        print(f"ATTACK -> Min: {df_a.min():.4f} | Max: {df_a.max():.4f} | Variance: {df_a.var():.6f}")
    except FileNotFoundError:
        print(f"[!] Arquivos da interface {ponto} não encontrados.")
