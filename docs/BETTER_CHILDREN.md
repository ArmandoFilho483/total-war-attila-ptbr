# 👶 Better Children & Political Marriages (Subprojeto de Balanceamento Dinástico)

Este subprojeto integra os parâmetros balanceados para a árvore genealógica e casamentos dinásticos do *Total War: Attila*, corrigindo os desequilíbrios históricos da versão vanilla da Creative Assembly.

---

## 🎯 Problemas Originais (Vanilla) vs Soluções Implementadas

| Parâmetro da Campanha | Valor Vanilla / Bug | Valor Calibrado | Impacto no Jogo |
| :--- | :--- | :--- | :--- |
| `family_male_child_chance` | 50% (com variações frustrantes) | **65%** | Assegura predominância de herdeiros masculinos para generais e governadores de sangue real. |
| `family_age_of_adulthood` | 16 anos | **5 anos** | Reduz o tempo de espera no motor de jogo (4 turnos por ano) para que a criança cresça. |
| `family_chance_of_adulthood` | 8% por turno | **100%** | Ao atingir a idade mínima (20 turnos após nascer), a transição para general adulto é imediata. |
| `family_rounds_between_wife_offers` | 4 turnos | **2 turnos** | Propostas frequentes de casamento na corte (a cada meio ano). |
| `family_base_wife_chance` | 25% | **50%** | Dobro da probabilidade base de pretendentes qualificados. |
| `family_emergent_wife_maximum_age` | 35 anos | **25 anos** | Assegura que novas noivas cheguem no auge do período fértil, maximizando descendentes. |

---

## ⚙️ Script Reprodutível de Patch Binário

O script abaixo lê o arquivo original ou modificado e aplica as correções de ponto flutuante diretamente na tabela `campaign_variables`:

```python
import struct

def patch_campaign_variables(pack_path: str):
    with open(pack_path, "rb") as f:
        data = bytearray(f.read())
        
    patches = {
        b"family_male_child_chance": 65.0,
        b"family_chance_of_adulthood": 100.0,
        b"family_rounds_between_wife_offers": 2.0,
        b"family_base_wife_chance": 50.0,
        b"family_emergent_wife_maximum_age": 25.0,
        b"family_retainer_wife_maximum_age": 25.0
    }
    
    for var_name, new_val in patches.items():
        idx = data.find(var_name)
        if idx != -1:
            val_offset = idx + len(var_name)
            data[val_offset:val_offset+4] = struct.pack("<f", new_val)
            print(f"[OK] {var_name.decode()} -> {new_val}")
            
    with open(pack_path, "wb") as f:
        f.write(data)
```
