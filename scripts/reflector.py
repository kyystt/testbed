from scapy.all import sniff, sendp, Ether

# Interface e MAC do motor
INTERFACE = "enp0s31f6"
MAC_MOTOR = "4c:e7:05:2a:d8:90"

def tentar_salvar_pacote(pkt):
    # Filtra pacotes PROFINET destinados ao motor
    if pkt.haslayer(Ether) and pkt[Ether].dst.lower() == MAC_MOTOR:
        print("[!] Pacote capturado, tentando retransmitir...")
        # Reenvia exatamente como chegou
        sendp(pkt, iface=INTERFACE, verbose=False)

print("[*] Aguardando tráfego...")
sniff(iface=INTERFACE, prn=tentar_salvar_pacote, store=0)
