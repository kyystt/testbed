import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configurações visuais (com a fonte aumentada que o Sadoc pediu)
sns.set_theme(style="whitegrid")
sns.set_context("paper", font_scale=1.5)

MAC_PLC = "4c:e7:05:0d:e2:6c"
MAC_VFD = "68:3e:02:4b:9b:d4"

# Os 3 pontos de coleta físicos
pontos_de_coleta = ["vfd", "bridge", "plc"]

def run_tests(benign, attack, name):
    print(f"\n--- Analisando o Destino: {name} ---")
    print(f"Amostra Benigna: {len(benign)} | Amostra Ataque: {len(attack)}")
    
    if len(benign) == 0 or len(attack) == 0:
        print("[-] Dados insuficientes para este destino.")
        return

    t_stat, p_welch = stats.ttest_ind(benign, attack, equal_var=False)
    print(f"1. Welch's t-test (Mean)     -> Stat: {t_stat:12.4f} | P-Value: {p_welch:.4e}")
    
    u_stat, p_mw = stats.mannwhitneyu(benign, attack, alternative='two-sided')
    print(f"2. Mann-Whitney U (Ranks)    -> Stat: {u_stat:12.4f} | P-Value: {p_mw:.4e}")
    
    ks_stat, p_ks = stats.ks_2samp(benign, attack)
    print(f"3. Kolmogorov-Smirnov (Shape)-> Stat: {ks_stat:12.4f} | P-Value: {p_ks:.4e}")

# ==========================================
# O LOOP MASTER (Gera a análise para cada interface física)
# ==========================================
for ponto in pontos_de_coleta:
    file_benign = f"../super_baseline_benign_{ponto}.csv"
    file_attack = f"../super_baseline_attack_{ponto}.csv"
    
    # Pula se o Victor não tiver os arquivos desse ponto (ex: se o PLC estiver faltando)
    if not os.path.exists(file_benign) or not os.path.exists(file_attack):
        print(f"\n[!] CSVs do ponto de coleta '{ponto.upper()}' não encontrados. Pulando...")
        continue

    print("\n" + "="*70)
    print(f" RESULTADOS DA CAPTURA FÍSICA: INTERFACE {ponto.upper()} ")
    print("="*70)

    df_benign = pd.read_csv(file_benign)
    df_attack = pd.read_csv(file_attack)

    # Aplica o Filtro de MAC Address
    plc_benign = df_benign[(df_benign['src_mac'] == MAC_PLC) & (df_benign['source_delta_ms'] > 0)]['source_delta_ms']
    plc_attack = df_attack[(df_attack['src_mac'] == MAC_PLC) & (df_attack['source_delta_ms'] > 0)]['source_delta_ms']

    vfd_benign = df_benign[(df_benign['src_mac'] == MAC_VFD) & (df_benign['source_delta_ms'] > 0)]['source_delta_ms']
    vfd_attack = df_attack[(df_attack['src_mac'] == MAC_VFD) & (df_attack['source_delta_ms'] > 0)]['source_delta_ms']

    # Imprime a estatística no terminal
    run_tests(plc_benign, plc_attack, "PLC (Controlador)")
    run_tests(vfd_benign, vfd_attack, "VFD (Atuador)")

    # ==========================================
    # GERA A IMAGEM DESTE PONTO ESPECÍFICO
    # ==========================================
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'Morphological Impact of MitM Attack - Captured at {ponto.upper()} Interface', fontsize=18, fontweight='bold', y=1.02)

    try:
        lim_sup_plc = max(plc_benign.quantile(0.999), plc_attack.quantile(0.999))
        lim_sup_vfd = max(vfd_benign.quantile(0.999), vfd_attack.quantile(0.999))
    except ValueError:
        continue # Previne erro se a amostra for muito pequena

    # --- LINHA 1: PLC ---
    sns.kdeplot(plc_benign, fill=True, label="Benign", color="#1f77b4", ax=axes[0, 0], clip=(0, lim_sup_plc))
    sns.kdeplot(plc_attack, fill=True, label="Attacked", color="#d62728", alpha=0.6, ax=axes[0, 0], clip=(0, lim_sup_plc))
    axes[0, 0].set_title(f"(a) {ponto.upper()} view of PLC - Density", fontsize=14, fontweight='bold')
    axes[0, 0].axvline(2.0, color='black', linestyle='--', alpha=0.5, label="Target (2.0 ms)")
    axes[0, 0].legend()

    df_plc_box = pd.DataFrame({'Condition': ['Benign']*len(plc_benign) + ['Attacked']*len(plc_attack),
                               'Jitter': np.concatenate([plc_benign, plc_attack])})
    sns.boxplot(data=df_plc_box, x='Condition', y='Jitter', palette=["#1f77b4", "#d62728"], ax=axes[0, 1], showfliers=False)
    axes[0, 1].set_title(f"(b) {ponto.upper()} view of PLC - Boxplot", fontsize=14, fontweight='bold')

    sns.ecdfplot(plc_benign, color="#1f77b4", ax=axes[0, 2])
    sns.ecdfplot(plc_attack, color="#d62728", ax=axes[0, 2])
    axes[0, 2].set_title(f"(c) {ponto.upper()} view of PLC - eCDF", fontsize=14, fontweight='bold')
    axes[0, 2].set_xlim(0, lim_sup_plc)

    # --- LINHA 2: VFD ---
    sns.kdeplot(vfd_benign, fill=True, label="Benign", color="#2ca02c", ax=axes[1, 0], clip=(0, lim_sup_vfd))
    sns.kdeplot(vfd_attack, fill=True, label="Attacked", color="#ff7f0e", alpha=0.6, ax=axes[1, 0], clip=(0, lim_sup_vfd))
    axes[1, 0].set_title(f"(d) {ponto.upper()} view of VFD - Density", fontsize=14, fontweight='bold')
    axes[1, 0].axvline(2.0, color='black', linestyle='--', alpha=0.5, label="Target (2.0 ms)")
    axes[1, 0].legend()

    df_vfd_box = pd.DataFrame({'Condition': ['Benign']*len(vfd_benign) + ['Attacked']*len(vfd_attack),
                               'Jitter': np.concatenate([vfd_benign, vfd_attack])})
    sns.boxplot(data=df_vfd_box, x='Condition', y='Jitter', palette=["#2ca02c", "#ff7f0e"], ax=axes[1, 1], showfliers=False)
    axes[1, 1].set_title(f"(e) {ponto.upper()} view of VFD - Boxplot", fontsize=14, fontweight='bold')

    sns.ecdfplot(vfd_benign, color="#2ca02c", ax=axes[1, 2])
    sns.ecdfplot(vfd_attack, color="#ff7f0e", ax=axes[1, 2])
    axes[1, 2].set_title(f"(f) {ponto.upper()} view of VFD - eCDF", fontsize=14, fontweight='bold')
    axes[1, 2].set_xlim(0, lim_sup_vfd)

    plt.tight_layout()

    # Salva a imagem com o nome da interface
    nome_arquivo = f"statistical_analysis_6_panels_{ponto.upper()}.png"
    plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight')
    print(f"[+] Gráfico da interface {ponto.upper()} salvo como: {nome_arquivo}")

    # Não usar plt.show() no loop para ele não travar o script aguardando você fechar a janela
    plt.close() 

print("\n[!] Análise completa finalizada!")
