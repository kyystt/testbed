#!/bin/bash

# Define os diretórios onde estão os PCAPs
BENIGN_DIR="capturas/benign/limpos"
ATTACK_DIR="capturas/attack/limpos"

# Nomes dos 3 pontos de coleta (como o Victor escreveu nos arquivos)
PONTOS=("vfd" "bridge" "plc")

for PONTO in "${PONTOS[@]}"; do
    echo "=========================================="
    echo " PROCESSANDO PONTO DE CAPTURA FISICA: $PONTO"
    echo "=========================================="

    # Define os arquivos Master para este ponto de coleta específico
    BENIGN_MASTER="super_baseline_benign_${PONTO}.csv"
    ATTACK_MASTER="super_baseline_attack_${PONTO}.csv"

    # Injeta o cabeçalho
    echo "packet_number,interface_id,src_mac,global_delta_ms,source_delta_ms" > "$BENIGN_MASTER"
    echo "packet_number,interface_id,src_mac,global_delta_ms,source_delta_ms" > "$ATTACK_MASTER"

    echo "[*] Extraindo PCAPs Benignos da interface $PONTO..."
    for file in "$BENIGN_DIR"/*${PONTO}*.pcap; do
        if [ -f "$file" ]; then
            echo "  -> Processing: $file"
            tshark -r "$file" -q -X lua_script:scripts/jitter_filter.lua 
            tail -n +2 jitter_output_filtered.csv >> "$BENIGN_MASTER"
        fi
    done

    echo "[*] Extraindo PCAPs de Ataque da interface $PONTO..."
    for file in "$ATTACK_DIR"/*${PONTO}*.pcap; do
        if [ -f "$file" ]; then
            echo "  -> Processing: $file"
            tshark -r "$file" -q -X lua_script:scripts/jitter_filter.lua 
            tail -n +2 jitter_output_filtered.csv >> "$ATTACK_MASTER"
        fi
    done
done

# Limpa o lixo
if [ -f "jitter_output_filtered.csv" ]; then
    rm jitter_output_filtered.csv
fi

echo "[+] Extração Multi-Ponto Concluída com Sucesso!"
