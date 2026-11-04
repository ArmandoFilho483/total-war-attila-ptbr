import os
import glob
import sys

sys.path.insert(0, os.path.dirname(__file__))
from warscape_compiler import LocCodec

base_proj = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
loc_dir = os.path.join(base_proj, "temp_extracted", "text", "db")
tsv_dir = os.path.join(base_proj, "src", "text_tsv")
os.makedirs(tsv_dir, exist_ok=True)

loc_files = glob.glob(os.path.join(loc_dir, "*.loc"))
print(f"Encontrados {len(loc_files)} arquivos .loc para conversão...")

total_lines = 0
for loc_path in loc_files:
    base_name = os.path.splitext(os.path.basename(loc_path))[0]
    tsv_path = os.path.join(tsv_dir, f"{base_name}.tsv")
    with open(loc_path, "rb") as f:
        data = f.read()
    rows = LocCodec.decode(data)
    total_lines += len(rows)
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write("key\tvalue\tflag\n")
        for k, v, fl in rows:
            f.write(f"{k}\t{v}\t{fl}\n")

print(f"[SUCESSO] Convertidos {len(loc_files)} arquivos .loc para {tsv_dir}. Total de linhas: {total_lines}")
