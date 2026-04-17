import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

print("[*] Carregando os datasets separados por MAC...")
df_benign = pd.read_csv("../super_baseline_benign.csv")
df_attack = pd.read_csv("../super_baseline_attack.csv")

# Mapeamento dos MAC Addresses
MAC_PLC = "4c:e7:05:0d:e2:6c"
MAC_VFD = "68:3e:02:4b:9b:d4"

# Filtrando os dados válidos
plc_benign = df_benign[(df_benign['src_mac'] == MAC_PLC) & (df_benign['source_delta_ms'] > 0)]['source_delta_ms']
plc_attack = df_attack[(df_attack['src_mac'] == MAC_PLC) & (df_attack['source_delta_ms'] > 0)]['source_delta_ms']

vfd_benign = df_benign[(df_benign['src_mac'] == MAC_VFD) & (df_benign['source_delta_ms'] > 0)]['source_delta_ms']
vfd_attack = df_attack[(df_attack['src_mac'] == MAC_VFD) & (df_attack['source_delta_ms'] > 0)]['source_delta_ms']

# ==========================================
# 1. TESTES ESTATÍSTICOS (Separados por Equipamento)
# ==========================================
print("\n=======================================================")
print("  RESULTADOS DOS TESTES ESTATÍSTICOS (SUPER BASELINE)  ")
print("=======================================================")

def run_tests(benign, attack, name):
    print(f"\n--- Analisando {name} ---")
    print(f"Amostra Benigna: {len(benign)} | Amostra Ataque: {len(attack)}")
    
    # Welch's t-test (Média)
    t_stat, p_welch = stats.ttest_ind(benign, attack, equal_var=False)
    print(f"1. Welch's t-test (Mean)     -> Stat: {t_stat:12.4f} | P-Value: {p_welch:.4e}")
    
    # Mann-Whitney U test (Mediana/Ranks - Usando a população inteira)
    u_stat, p_mw = stats.mannwhitneyu(benign, attack, alternative='two-sided')
    print(f"2. Mann-Whitney U (Ranks)    -> Stat: {u_stat:12.4f} | P-Value: {p_mw:.4e}")
    
    # Kolmogorov-Smirnov test (Morfologia/Shape)
    ks_stat, p_ks = stats.ks_2samp(benign, attack)
    print(f"3. Kolmogorov-Smirnov (Shape)-> Stat: {ks_stat:12.4f} | P-Value: {p_ks:.4e}")

# Executa os testes
run_tests(plc_benign, plc_attack, "PLC (Controlador)")
run_tests(vfd_benign, vfd_attack, "VFD (Atuador)")
print("=======================================================\n")

# ==========================================
# 2. GERAÇÃO DA MATRIZ DE GRÁFICOS (2x3)
# ==========================================
print("[*] Desenhando a Matriz de Gráficos (2 linhas x 3 colunas)...")
sns.set_theme(style="whitegrid")
sns.set_context("paper", font_scale=1.5)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Morphological Impact of MitM Attack per Device (Target = 2.0 ms)', fontsize=18, fontweight='bold', y=1.02)

# --- LIMITES DINÂMICOS ---
lim_sup_plc = max(plc_benign.quantile(0.999), plc_attack.quantile(0.999))
lim_sup_vfd = max(vfd_benign.quantile(0.999), vfd_attack.quantile(0.999))

# --- LINHA 1: ANÁLISE DO PLC ---
# 1. KDE do PLC
sns.kdeplot(plc_benign, fill=True, label="Benign", color="#1f77b4", ax=axes[0, 0], clip=(0, lim_sup_plc))
sns.kdeplot(plc_attack, fill=True, label="Attacked", color="#d62728", alpha=0.6, ax=axes[0, 0], clip=(0, lim_sup_plc))
axes[0, 0].set_title("(a) PLC - Jitter Density", fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel("Inter-arrival Time (ms)")
axes[0, 0].set_ylabel("Density")
axes[0, 0].axvline(2.0, color='black', linestyle='--', alpha=0.5, label="Target (2.0 ms)")
axes[0, 0].legend()

# 2. Boxplot do PLC
df_plc_box = pd.DataFrame({'Condition': ['Benign']*len(plc_benign) + ['Attacked']*len(plc_attack),
                           'Jitter': np.concatenate([plc_benign, plc_attack])})
sns.boxplot(data=df_plc_box, x='Condition', y='Jitter', palette=["#1f77b4", "#d62728"], ax=axes[0, 1], showfliers=False)
axes[0, 1].set_title("(b) PLC - Variance Inflation", fontsize=12, fontweight='bold')
axes[0, 1].set_ylabel("Inter-arrival Time (ms)")

# 3. eCDF do PLC
sns.ecdfplot(plc_benign, color="#1f77b4", ax=axes[0, 2])
sns.ecdfplot(plc_attack, color="#d62728", ax=axes[0, 2])
axes[0, 2].set_title("(c) PLC - Cumulative Dist. (eCDF)", fontsize=12, fontweight='bold')
axes[0, 2].set_xlabel("Inter-arrival Time (ms)")
axes[0, 2].set_ylabel("Cumulative Probability")
axes[0, 2].set_xlim(0, lim_sup_plc)

# --- LINHA 2: ANÁLISE DO VFD ---
# 4. KDE do VFD
sns.kdeplot(vfd_benign, fill=True, label="Benign", color="#2ca02c", ax=axes[1, 0], clip=(0, lim_sup_vfd))
sns.kdeplot(vfd_attack, fill=True, label="Attacked", color="#ff7f0e", alpha=0.6, ax=axes[1, 0], clip=(0, lim_sup_vfd))
axes[1, 0].set_title("(d) VFD - Jitter Density", fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel("Inter-arrival Time (ms)")
axes[1, 0].set_ylabel("Density")
axes[1, 0].axvline(2.0, color='black', linestyle='--', alpha=0.5, label="Target (2.0 ms)")
axes[1, 0].legend()

# 5. Boxplot do VFD
df_vfd_box = pd.DataFrame({'Condition': ['Benign']*len(vfd_benign) + ['Attacked']*len(vfd_attack),
                           'Jitter': np.concatenate([vfd_benign, vfd_attack])})
sns.boxplot(data=df_vfd_box, x='Condition', y='Jitter', palette=["#2ca02c", "#ff7f0e"], ax=axes[1, 1], showfliers=False)
axes[1, 1].set_title("(e) VFD - Variance Inflation", fontsize=12, fontweight='bold')
axes[1, 1].set_ylabel("Inter-arrival Time (ms)")

# 6. eCDF do VFD
sns.ecdfplot(vfd_benign, color="#2ca02c", ax=axes[1, 2])
sns.ecdfplot(vfd_attack, color="#ff7f0e", ax=axes[1, 2])
axes[1, 2].set_title("(f) VFD - Cumulative Dist. (eCDF)", fontsize=12, fontweight='bold')
axes[1, 2].set_xlabel("Inter-arrival Time (ms)")
axes[1, 2].set_ylabel("Cumulative Probability")
axes[1, 2].set_xlim(0, lim_sup_vfd)

plt.tight_layout()

# Salva a imagem
nome_arquivo = "statistical_analysis_6_panels.png"
plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight')
print(f"[+] Gráfico salvo com sucesso: {nome_arquivo}")

plt.show()
