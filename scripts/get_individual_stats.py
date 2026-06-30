import pandas as pd
from scipy.stats import ks_2samp

pontos = ["plc", "bridge", "vfd"]

for ponto in pontos:
    print(f"\n=======================================================")
    print(f"=== ESTATÍSTICAS: INTERFACE {ponto.upper()} ===")
    print(f"=======================================================")
    try:
        # Puxamos o 'source_delta_ms' pois queremos o tempo isolado de 2.0ms
        df_b = pd.read_csv(f"../super_baseline_benign_{ponto}.csv")['source_delta_ms'].dropna()
        df_a = pd.read_csv(f"../super_baseline_attack_{ponto}.csv")['source_delta_ms'].dropna()
        
        # 1. Estatísticas Originais (Min, Max, Variance)
        print(f"BENIGN -> Min: {df_b.min():.4f} | Max: {df_b.max():.4f} | Variance: {df_b.var():.6f}")
        print(f"ATTACK -> Min: {df_a.min():.4f} | Max: {df_a.max():.4f} | Variance: {df_a.var():.6f}")
        print("-" * 55)
        
        # 2. Novas métricas exigidas pelo Sadoc (Tamanho do Efeito)
        var_ratio = df_a.var() / df_b.var() if df_b.var() != 0 else 0
        ks_stat, _ = ks_2samp(df_b, df_a)
        
        q999_b = df_b.quantile(0.999)
        q999_a = df_a.quantile(0.999)
        
        pr_burst_b = (df_b < 0.1).mean()
        pr_burst_a = (df_a < 0.1).mean()
        
        pr_delay_b = (df_b > 3.0).mean()
        pr_delay_a = (df_a > 3.0).mean()
        
        print(f"[*] Variance Ratio (Atk/Ben) : {var_ratio:.2f}x")
        print(f"[*] KS Statistic (D)         : {ks_stat:.4f}")
        print(f"[*] Quantil 99.9% (Atk)      : {q999_a:.4f} ms  (Benign: {q999_b:.4f} ms)")
        print(f"[*] Pr(Δt < 0.1ms) [Burst]   : Atk = {pr_burst_a:.6f} | Benign = {pr_burst_b:.6f}")
        print(f"[*] Pr(Δt > 3.0ms) [Atraso]  : Atk = {pr_delay_a:.6f} | Benign = {pr_delay_b:.6f}")
        
    except FileNotFoundError:
        print(f"[!] Arquivos da interface {ponto} não encontrados.")
