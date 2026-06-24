import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Visual Styling ---
sns.set_theme(style="whitegrid")
sns.set_context("paper", font_scale=1.4)
color_benign = "#1f77b4"
color_attack = "#d62728"

MAC_PLC = "4c:e7:05:0d:e2:6c"

# --- Create 4x3 Grid ---
# sharex=True ensures X-axis is normalized across all plots in a column
fig, axes = plt.subplots(4, 3, figsize=(20, 16), sharex='col')
fig.suptitle('Comprehensive Morphological Analysis: Aggregate vs. Physical Vantage Points', fontsize=20, fontweight='bold', y=1.02)

# Helper function to plot a row
def plot_row(row_idx, benign_data, attack_data, title, target_mean, add_arrows=False):
    if len(benign_data) == 0 or len(attack_data) == 0:
        return
    
    lim_sup = max(benign_data.quantile(0.999), attack_data.quantile(0.999))
    
    # 1. KDE
    sns.kdeplot(benign_data, fill=True, color=color_benign, ax=axes[row_idx, 0], clip=(0, lim_sup), label="Benign (Solid)")
    # Style update: dashed line, no fill for attack to easily distinguish
    sns.kdeplot(attack_data, fill=False, color=color_attack, linestyle='--', linewidth=2.5, ax=axes[row_idx, 0], clip=(0, lim_sup), label="Attacked (Dashed)")
    axes[row_idx, 0].set_title(f"{title} - Density", fontweight='bold')
    axes[row_idx, 0].axvline(target_mean, color='black', linestyle=':', alpha=0.7)
    
    if add_arrows:
        axes[row_idx, 0].annotate('Mean Evasion', xy=(target_mean, axes[row_idx, 0].get_ylim()[1]*0.8), 
                                  xytext=(target_mean+0.5, axes[row_idx, 0].get_ylim()[1]*0.9),
                                  arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

    # 2. Boxplot
    df_box = pd.DataFrame({'Condition': ['Benign']*len(benign_data) + ['Attacked']*len(attack_data),
                           'Jitter': np.concatenate([benign_data, attack_data])})
    sns.boxplot(data=df_box, y='Condition', x='Jitter', hue='Condition', palette=[color_benign, color_attack], ax=axes[row_idx, 1], showfliers=False, orient='h')
    axes[row_idx, 1].set_title(f"{title} - Dispersion", fontweight='bold')
    axes[row_idx, 1].set_ylabel("")
    
    if add_arrows:
        axes[row_idx, 1].annotate('Variance Inflation', xy=(target_mean+0.2, 1), 
                                  xytext=(target_mean+1.0, 1.2),
                                  arrowprops=dict(facecolor='red', shrink=0.05, width=1.5, headwidth=6))

    # 3. eCDF
    sns.ecdfplot(benign_data, color=color_benign, ax=axes[row_idx, 2])
    sns.ecdfplot(attack_data, color=color_attack, linestyle='--', linewidth=2.5, ax=axes[row_idx, 2])
    axes[row_idx, 2].set_title(f"{title} - eCDF", fontweight='bold')
    axes[row_idx, 2].set_xlim(0, lim_sup)
    
    if add_arrows:
        axes[row_idx, 2].annotate('Morphological Gap', xy=(target_mean+0.5, 0.5), 
                                  xytext=(target_mean+1.5, 0.3),
                                  arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

# --- ROW 1: Aggregate Flow ---
print("[*] Plotting Aggregate Flow...")
df_b_agg = pd.read_csv("../super_baseline_benign.csv")['global_delta_ms'].dropna()
df_a_agg = pd.read_csv("../super_baseline_attack.csv")['global_delta_ms'].dropna()
plot_row(0, df_b_agg, df_a_agg, "Line 1: Global Aggregate Flow", target_mean=1.0)

# --- ROWS 2, 3, 4: Vantage Points (Filtering ONLY for PLC Source to highlight the anomaly) ---
vantage_points = ["plc", "bridge", "vfd"]

for i, vp in enumerate(vantage_points):
    print(f"[*] Plotting Vantage Point: {vp.upper()}...")
    row_idx = i + 1
    
    try:
        df_b = pd.read_csv(f"../super_baseline_benign_{vp}.csv")
        df_a = pd.read_csv(f"../super_baseline_attack_{vp}.csv")
        
        # Filter for PLC Source
        plc_b = df_b[(df_b['src_mac'] == MAC_PLC) & (df_b['source_delta_ms'] > 0)]['source_delta_ms']
        plc_a = df_a[(df_a['src_mac'] == MAC_PLC) & (df_a['source_delta_ms'] > 0)]['source_delta_ms']
        
        # Add arrows only to the PLC view (Row 2) as it's the strongest anomaly
        add_arrows = True if vp == "plc" else False
        plot_row(row_idx, plc_b, plc_a, f"Line {row_idx+1}: {vp.upper()} Vantage Point (PLC Packets)", target_mean=2.0, add_arrows=add_arrows)
        
    except FileNotFoundError:
        print(f"[!] Warning: Missing files for {vp}. Skipping row.")

# Final Layout Adjustments
axes[0,0].legend(loc='upper right')
for ax in axes.flat:
    ax.set_xlabel("Inter-arrival Time (ms)")
plt.tight_layout()

filename = "master_4x3_analysis_panel.png"
plt.savefig(filename, dpi=300, bbox_inches='tight')
print(f"[+] Master Plot saved successfully as {filename}!")
