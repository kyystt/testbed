# 19/06/2026

## 1. ARP Spoofing (Camada 3)
* **Objetivo:** Tentar interceptar o tráfego de controle entre o PLC (192.168.0.5) e o Inversor (192.168.0.2) via envenenamento de cache ARP
* **Log da tentativa de manipulação de tabela ARP entre o PLC (192.168.0.5) e a HMI/Drive (192.168.0.2):**

```bash
$ sudo ettercap -T -q -i enp0s31f6 -M arp:remote /192.168.0.5// /192.168.0.2//
...
ARP poisoning victims:

 GROUP 1 : 192.168.0.5 4C:E7:05:0D:E2:6C

 GROUP 2 : 192.168.0.2 4C:E7:05:2A:D8:90
Starting Unified sniffing...
...
DHCP: [98:BA:5F:C1:96:27] DISCOVER 
DHCP: [98:BA:5F:C1:96:27] DISCOVER 
DHCP: [98:BA:5F:C1:96:27] DISCOVER 
DHCP: [98:BA:5F:C1:96:27] DISCOVER 
...
```

* **Conclusão L3:** O ARP Spoofing redireciona o tráfego IP (TI), mas o tráfego de controle industrial (EtherType `0x8892`) permanece invisível ao atacante. Isso ocorre porque o PROFINET RT utiliza endereçamento L2 direto, ignorando a pilha de resolução ARP.

#### Análise Técnica: Por que o ARP Spoofing falhou em manipular o motor?

O log acima prova que a ferramenta capturou o tráfego de Camada 3 (IP), mas a automação permaneceu intacta. A explicação reside na diferença estrutural entre as camadas:

Segregação de Camadas (L3 vs L2): O envenenamento ARP afeta apenas a resolução de endereços IP. Protocolos como DHCP, HTTP ou S7Comm (via TCP) caíram na armadilha e foram roteados para a máquina atacante.

Resiliência do PROFINET RT: O tráfego de controle do motor (EtherType 0x8892) é operado puramente em Camada 2 (Enlace). O controlador (PLC) possui mapeamentos de hardware (hardcoded) que associam o endereço MAC do dispositivo de destino diretamente à sua porta de saída no switch, ignorando totalmente a tabela ARP.

Conclusão: Ferramentas de TI baseadas em L3 são ineficazes para manipular tráfego de tempo real em redes industriais, pois o PROFINET não consulta tabelas de rede para encaminhar quadros de I/O cíclico.

## 2. MAC Spoofing (Camada 2)

Possíveis problemas a serem enfrentados: 

1. MAC Flapping e instabilidade (Conflito de Tabela CAM)
Ao clonar o MAC do motor (D8:90), o switch TP-Link sofre um MAC Flapping. Ele passa a receber quadros da mesma origem em portas diferentes (a porta física real do motor vs. a porta física do atacante). Isso causa fragmentação de pacotes e perda de integridade do tráfego industrial.

2. O Estouro do Watchdog Timer (Siemens)
Redes PROFINET RT operam com ciclos de ≈2.0 ms. O hardware Siemens é configurado com um Watchdog Timer de segurança que desarma o sistema (ativando o erro Bus Fault - BF) caso o dispositivo perca 3 pacotes consecutivos (≈6.0 ms). O atraso introduzido pelo processamento via user-space no Linux ou pela troca de MACs físicos (Down/Up) é superior a essa janela, causando o desarme imediato.

3. Bloqueio por "Hairpinning Drop"
Se o atacante tentar agir como um "refletor" (receber e encaminhar o pacote para salvar a conexão), o switch bloqueia a operação. Ao ver que o pacote de destino (MAC do motor) está mapeado para a mesma porta de origem de onde o quadro está vindo (a porta do atacante), o firmware do switch descarta o pacote automaticamente para evitar loops de rede.

#### Tentativa
* **Objetivo:** Assumir a identidade do dispositivo alvo (`4C:E7:05:2A:D8:90`) para interceptar o fluxo Unicast de controle.
* **Procedimento:**
    1. `sudo ip link set enp0s31f6 down`
    2. `sudo macchanger -m 4c:e7:05:2a:d8:90 enp0s31f6`
    3. `sudo ip link set enp0s31f6 up`
    4. `sudo tcpdump -i enp0s31f6 ether proto 0x8892`
* **Log do tcpdump:**
```bash
...
11:19:05.524630 68:3e:02:4b:9b:d5 (oui Unknown) > 01:80:c2:00:00:0e (oui Unknown), ethertype Unknown (0x8892), length 60: 
	0x0000:  ff40 0000 0000 0000 0000 0000 0000 0f20  .@..............
	0x0010:  0000 0000 0000 0c06 683e 024b 9bd5 0000  ........h>.K....
	0x0020:  0000 0000 0000 0000 0000 0000 0000       ..............
11:19:06.727644 68:3e:02:4b:9b:d5 (oui Unknown) > 01:80:c2:00:00:0e (oui Unknown), ethertype Unknown (0x8892), length 60: 
	0x0000:  ff40 0000 0000 0000 0000 0000 0000 0f21  .@.............!
	0x0010:  0000 0000 0000 0c06 683e 024b 9bd5 0000  ........h>.K....
	0x0020:  0000 0000 0000 0000 0000 0000 0000       ..............
11:19:07.930853 68:3e:02:4b:9b:d5 (oui Unknown) > 01:80:c2:00:00:0e (oui Unknown), ethertype Unknown (0x8892), length 60: 
	0x0000:  ff40 0000 0000 0000 0000 0000 0000 0f22  .@............."
	0x0010:  0000 0000 0000 0c06 683e 024b 9bd5 0000  ........h>.K....
	0x0020:  0000 0000 0000 0000 0000 0000 0000       ..............
11:19:09.133558 68:3e:02:4b:9b:d5 (oui Unknown) > 01:80:c2:00:00:0e (oui Unknown), ethertype Unknown (0x8892), length 60: 
	0x0000:  ff40 0000 0000 0000 0000 0000 0000 0f23  .@.............#
	0x0010:  0000 0000 0000 0c06 683e 024b 9bd5 0000  ........h>.K....
	0x0020:  0000 0000 0000 0000 0000 0000 0000       ..............
...
```
* **Resultado:** O motor manteve a operação estável (sem *Bus Fault*). A captura via `tcpdump` confirmou que apenas pacotes Multicast (`01:80:c2...`) foram recebidos, enquanto os comandos de controle Unicast do PLC foram entregues exclusivamente ao hardware original.

Ao fazer isso, o motor continuou girando e ainda consegui mudar a velocidade pelo TIA portal, mostrando que ele não confia cegamente a porta pela tabela CAM, provavelmente deve fazer Port Binding ou MAC Locking

O teste do spoofing do endereço MAC em Single-NIC é ineficaz para ataques de MitM em redes PROFINET 

# 3. Análise do Comportamento do Switch (Hardware: TP-Link TL-SG108E)
O switch atuou como um elemento mitigador involuntário de segurança através de dois mecanismos principais:

## Hipoteses (gerado por IA): 
* **Integridade da Tabela CAM (Port Binding Implícito):** O TL-SG108E implementa uma lógica de retenção de entrada na memória CAM. Como o fluxo de controle PROFINET é cíclico e de alta frequência (ciclos de 2.0ms), a atualização da tabela CAM pelo dispositivo legítimo é mais persistente do que a tentativa de inserção por spoofing. O switch, ao detectar o MAC em duas portas distintas (legítima vs. atacante), priorizou a porta com a persistência de fluxo original.
* **Segregação de Unicast vs. Multicast:** O switch não realizou *flooding* de pacotes Unicast para a porta do atacante, confirmando que a lógica do ASIC (Application-Specific Integrated Circuit) filtra o tráfego ponto-a-ponto com base na porta de origem autenticada. A presença de tráfego Multicast (`LLDP/PTCP`) na captura do atacante ocorreu apenas devido à natureza de difusão de protocolos de controle de rede, não representando uma falha de isolamento de dados.

## 4. Conclusão Metodológica para o Artigo
O experimento validou que **ataques triviais de spoofing (L2/L3) são ineficazes em ambientes industriais modernos**. A resiliência da rede não depende de firewalls complexos, mas da própria arquitetura determinística e da lógica de comutação dos switches de camada 2:

1.  **Impossibilidade de MitM via Software:** Em arquiteturas *Single-NIC*, a tentativa de interceptação causa uma exclusão lógica do atacante pelo hardware do switch.
2.  **Necessidade de Ponte Física:** A impossibilidade de realizar um *Man-in-the-Middle* lógico com uma interface única confirma que a metodologia de **Ponte Transparente (Dual-NIC)** — posicionada fisicamente entre o PLC e o Inversor — é a **única via cientificamente válida** para a auditoria de tráfego e injeção de *Jitter* em redes PROFINET RT.


# 5. Auditoria de Rede e Testes de Estresse (Load Testing)
### 5.1 Caracterização do Determinismo (Jitter)
* **Procedimento:** Captura de 5.000 quadros PROFINET RT via `tcpdump` e análise via Wireshark.
* **Resultados:** A análise de *Delta Time* entre quadros `pn_rt` confirmou a estabilidade do ciclo de 2ms. O sistema apresentou comportamento determinístico, sem desvios significativos de *Jitter* em condições operacionais normais.
* **Métrica:** O *Cycle Counter* validou a integridade da sequência, com ausência de descartes (drops) de pacotes, confirmando que a rede mantém o tempo real estrito.

### 5.2 Mapeamento de Topologia (Discovery)
* **Ferramenta:** `nmap -Pn` (Scan forçado sem Ping).
* **Observação:** O estado `filtered` reportado para todos os dispositivos (PLC e Inversor) corrobora a eficácia do *hardening* de rede. Os ativos industriais estão configurados para descartar pacotes de reconhecimento (Ping/Service Discovery), tornando-os invisíveis a escaneamentos de TI tradicionais.

### 5.3 Teste de Estresse (Denial of Service - DoS)
* **Procedimento:** Injeção de mais de 4,4 milhões de pacotes (ICMP e UDP Flood) via `hping3` visando o Inversor e o PLC.
* **Resultado:** 100% de perda de pacotes (Packet Loss) para o tráfego de ataque, enquanto a operação PROFINET RT permaneceu ininterrupta, sem ocorrência de *Bus Fault* ou latência observável.
* **Conclusão de Resiliência:** A infraestrutura demonstrou imunidade a ataques de saturação de rede (Flood). A priorização de tráfego 802.1p do protocolo PROFINET e a filtragem em nível de ASIC do switch isolam o tráfego de controle crítico, garantindo a resiliência do sistema industrial mesmo sob carga extrema de tráfego "Best Effort".

## 6. Conclusão Metodológica para o Artigo
Os experimentos validaram que **ataques triviais de spoofing (L2/L3) e injeção de carga (DoS) são ineficazes em ambientes industriais modernos**. A robustez da rede é intrínseca à arquitetura determinística dos ativos. A falha técnica em comprometer a comunicação através de ataques lógicos confirma que a metodologia de **Ponte Transparente (Dual-NIC)** é a única via cientificamente viável para a auditoria de tráfego e análise de vulnerabilidades em redes PROFINET RT, uma vez que o hardware industrial mitiga automaticamente qualquer tentativa de invasão ou saturação por software.

# Proxima visita 
- Verificar se configuração do switch se manteve (espelhamento de porta e etc)
