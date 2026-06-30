#!/bin/bash

# MACs corretos que validamos
MAC_PLC="4c:e7:05:0d:e2:6c"
MAC_VFD="68:3e:02:4b:9b:d4"

PASTA_ATAQUE="$HOME/testbed/capturas/attack/limpos"

echo "==================================================="
echo " INICIANDO CONTAGEM DO DATASET DE ATAQUE"
echo "==================================================="

contar_interface() {
    local prefixo=$1
    local total_agg=0
    local total_plc=0
    local total_vfd=0

    for pcap in "$PASTA_ATAQUE"/${prefixo}*.pcap; do
        [ -e "$pcap" ] || continue 

        AGG=$(tshark -r "$pcap" -Y "pn_rt" -T fields -e frame.number 2>/dev/null | wc -l)
        PLC=$(tshark -r "$pcap" -Y "pn_rt && eth.src==$MAC_PLC" -T fields -e frame.number 2>/dev/null | wc -l)
        VFD=$(tshark -r "$pcap" -Y "pn_rt && eth.src==$MAC_VFD" -T fields -e frame.number 2>/dev/null | wc -l)

        total_agg=$((total_agg + AGG))
        total_plc=$((total_plc + PLC))
        total_vfd=$((total_vfd + VFD))
    done

    echo "--- RESULTADO: $prefixo (ATAQUE) ---"
    echo "N Global (Aggregate) : $total_agg"
    echo "N PLC View (Source)  : $total_plc"
    echo "N VFD View (Source)  : $total_vfd"
    echo "Prova (PLC+VFD=TOT)  : $((total_plc + total_vfd)) == $total_agg"
    echo "-----------------------------------"
}

contar_interface "bridge_attack"
contar_interface "plc_attack"
contar_interface "vfd_attack"

echo "Contagem finalizada!"
