import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats

# 1. Carregar os dados
# (Lembrando que devem estar no mesmo diretório do script)
df_benign = pd.read_csv('../jitter_benign_all.csv')
df_attack = pd.read_csv('../jitter_attack_all.csv')

# Remover possíveis valores nulos ou erros de parsing
benign_data = df_benign['delta_ms'].dropna()
attack_data = df_attack['delta_ms'].dropna()

print("\n=====================================================")
print("=== ANÁLISE ESTATÍSTICA AVANÇADA DE JITTER (MitM) ===")
print("=====================================================")
print(f"Tamanho da amostra Benigna : {len(benign_data)} pacotes")
print(f"Tamanho da amostra Ataque  : {len(attack_data)} pacotes\n")

# ---------------------------------------------------------
# TESTE 1: Welch's t-test (Comparação de Médias)
# Assunção: As variâncias podem ser diferentes
# ---------------------------------------------------------
stat_t, p_value_t = stats.ttest_ind(benign_data, attack_data, equal_var=False)
print("1. Welch's t-test (Diferença de Médias):")
print(f"   Estatística: {stat_t:.4f} | P-Valor: {p_value_t:.4e}")
if p_value_t < 0.05:
    print("   -> RESULTADO: A diferença entre as médias é significativa.")
else:
    print("   -> RESULTADO: A média NÃO mudou significativamente (Atacante evadiu o Watchdog!).")
print("-" * 53)

# ---------------------------------------------------------
# TESTE 2: Mann-Whitney U test (Comparação de Medianas/Ranks)
# Ideal para distribuições não-paramétricas (cauda longa)
# ---------------------------------------------------------
stat_mwu, p_value_mwu = stats.mannwhitneyu(benign_data, attack_data, alternative='two-sided')
print("2. Mann-Whitney U test (Diferença de Ranks/Medianas):")
print(f"   Estatística: {stat_mwu:.4f} | P-Valor: {p_value_mwu:.4e}")
if p_value_mwu < 0.05:
    print("   -> RESULTADO: A distribuição central sofreu um deslocamento significativo.")
else:
    print("   -> RESULTADO: O 'grosso' dos dados permaneceu idêntico.")
print("-" * 53)

# ---------------------------------------------------------
# TESTE 3: Kolmogorov-Smirnov test (Distribuição Global/Forma)
# Compara a "forma" inteira do gráfico, hiper-sensível a outliers extremos
# ---------------------------------------------------------
stat_ks, p_value_ks = stats.ks_2samp(benign_data, attack_data)
print("3. Kolmogorov-Smirnov test (Diferença na Forma/Distribuição):")
print(f"   Estatística: {stat_ks:.4f} | P-Valor: {p_value_ks:.4e}")
if p_value_ks < 0.05:
    print("   -> RESULTADO: A FORMA das distribuições é diferente (Captou os outliers da Ponte!).")
else:
    print("   -> RESULTADO: As distribuições são estatisticamente gêmeas.")
print("=====================================================\n")

# 4. Gerar o Boxplot
plt.figure(figsize=(8, 6))
plt.boxplot([benign_data, attack_data], tick_labels=['Fluxo Natural', 'Ataque MitM'])
plt.ylabel('Delta de Chegada (ms)')
plt.title('Distribuição de Jitter PROFINET RT (Super Baseline)')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Ajustar o limite do eixo Y para focar nos dados
plt.ylim(0, 4.0) 

plt.tight_layout()
plt.savefig('boxplot_jitter.png')
print("[+] Gráfico Boxplot gerado e salvo como 'boxplot_jitter.png'\n")
df_benign_temp = pd.DataFrame({'Jitter': benign_data, 'Scenario': 'Natural Flow'})
df_attack_temp = pd.DataFrame({'Jitter': attack_data, 'Scenario': 'MitM Attack'})
df_plot = pd.concat([df_benign_temp, df_attack_temp])

# 5. Generate the Academic Panel (1 row, 3 columns)
sns.set_theme(style="whitegrid") # Clean academic style

# Create figure with high pixel density (300 DPI) for print quality
fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=300) 
fig.suptitle('PROFINET RT Jitter Morphological Analysis (Super Baseline)', fontsize=18, fontweight='bold')

# --- Plot 1: KDE (Kernel Density Estimation) ---
# Shows that the bulk of the data remains identical at 1.0ms
sns.kdeplot(data=df_plot, x='Jitter', hue='Scenario', fill=True, ax=axes[0], palette=['blue', 'red'], alpha=0.5, common_norm=False)
axes[0].set_title('Jitter Density (KDE)', fontsize=14)
axes[0].set_xlabel('Arrival Delta (ms)', fontsize=12)
axes[0].set_ylabel('Density', fontsize=12)
axes[0].set_xlim(0, 3.5)

# --- Plot 2: Boxplot (Corrected with two boxes) ---
# We hide extreme fliers (outliers) to focus on the central quartiles
sns.boxplot(data=df_plot, x='Scenario', y='Jitter', palette=['blue', 'red'], ax=axes[1], showfliers=False)
axes[1].set_title('Dispersion and Quartiles (Boxplot - Focus)', fontsize=14)
axes[1].set_ylabel('Arrival Delta (ms)', fontsize=12)
axes[1].set_xlabel('', fontsize=12) # Removed repeated X-axis label
axes[1].set_ylim(0, 2.5) # Focus adjustment on quartiles

# --- Plot 3: eCDF (Kolmogorov-Smirnov visual representation) ---
# Shows cumulative probability. The gap between lines is what KS measures.
sns.ecdfplot(data=df_plot, x='Jitter', hue='Scenario', palette=['blue', 'red'], ax=axes[2])
axes[2].set_title('Cumulative Distribution (eCDF)', fontsize=14)
axes[2].set_xlabel('Arrival Delta (ms)', fontsize=12)
axes[2].set_ylabel('Cumulative Proportion', fontsize=12)
axes[2].set_xlim(0, 3.5)

plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust to prevent title overlap
plt.savefig('statistical_analysis_panel.png', dpi=300) # dpi=300 for high academic resolution
print("[+] CORRECTED academic graphic panel generated and saved as 'statistical_analysis_panel.png'\n")
