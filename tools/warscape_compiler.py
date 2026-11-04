#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Warscape Pack & LOC Compiler / Extractor
Utilitário CLI de alta performance para pacotes Total War (PFH4) e arquivos de localização (.loc).
Desenvolvido sob o protocolo de arquitetura híbrida de modding Total War: Attila.
"""

import sys
import os
import struct
import argparse
from typing import List, Tuple, Dict

# Assinatura PFH4 do Total War Attila
PFH4_MAGIC = b'PFH4'
LOC_BOM = b'\xff\xfe'
LOC_MAGIC = b'LOC\x00'

class LocCodec:
    """Decodificador e codificador de arquivos binários .loc da Creative Assembly."""
    
    @staticmethod
    def decode(loc_bytes: bytes) -> List[Tuple[str, str, int]]:
        """Decodifica .loc binário (UTF-16LE com BOM) em lista de tuplas (chave, valor, flag)."""
        if len(loc_bytes) < 14:
            raise ValueError("Arquivo .loc menor que o cabeçalho mínimo obrigatório.")
        
        bom = loc_bytes[:2]
        magic = loc_bytes[2:6]
        if bom != LOC_BOM or magic != LOC_MAGIC:
            raise ValueError(f"Cabeçalho inválido no .loc: BOM={bom}, Magic={magic}")
        
        version, row_count = struct.unpack_from("<II", loc_bytes, 6)
        pos = 14
        rows = []
        
        for _ in range(row_count):
            if pos >= len(loc_bytes):
                break
            # Leitura da Chave (UInt16 length em caracteres UTF-16LE)
            key_len_chars = struct.unpack_from("<H", loc_bytes, pos)[0]
            pos += 2
            key_bytes_len = key_len_chars * 2
            key = loc_bytes[pos:pos+key_bytes_len].decode("utf-16le", errors="replace")
            pos += key_bytes_len
            
            # Leitura do Valor
            val_len_chars = struct.unpack_from("<H", loc_bytes, pos)[0]
            pos += 2
            val_bytes_len = val_len_chars * 2
            val = loc_bytes[pos:pos+val_bytes_len].decode("utf-16le", errors="replace")
            pos += val_bytes_len
            
            # Leitura da Flag
            flag = loc_bytes[pos]
            pos += 1
            
            # Normalizar quebras de linha para gravação segura em TSV
            val_escaped = val.replace("\r\n", "\\n").replace("\n", "\\n")
            rows.append((key, val_escaped, flag))
            
        return rows

    @staticmethod
    def encode(rows: List[Tuple[str, str, int]]) -> bytes:
        """Codifica lista de tuplas (chave, valor, flag) em bytes .loc (UTF-16LE com BOM)."""
        out = bytearray()
        out.extend(LOC_BOM)
        out.extend(LOC_MAGIC)
        out.extend(struct.pack("<II", 1, len(rows)))
        
        for key, val, flag in rows:
            # Desescapar quebras de linha para o formato nativo do jogo
            val_unescaped = val.replace("\\n", "\n")
            
            key_bytes = key.encode("utf-16le")
            key_len_chars = len(key_bytes) // 2
            out.extend(struct.pack("<H", key_len_chars))
            out.extend(key_bytes)
            
            val_bytes = val_unescaped.encode("utf-16le")
            val_len_chars = len(val_bytes) // 2
            out.extend(struct.pack("<H", val_len_chars))
            out.extend(val_bytes)
            
            out.append(int(flag) & 0xFF)
            
        return bytes(out)


class PackArchive:
    """Manipulador de pacotes .pack no formato PFH4 do Total War: Attila."""
    
    @staticmethod
    def extract_all(pack_path: str, output_dir: str) -> int:
        """Extrai todos os arquivos contidos no .pack para o diretório de destino."""
        with open(pack_path, "rb") as f:
            header = f.read(28)
            if len(header) < 28:
                raise ValueError("Arquivo .pack corrompido ou truncado.")
            
            magic, pack_type, dep_count, dep_idx_sz, file_count, idx_sz, timestamp = struct.unpack("<4sIIIIII", header)
            if magic != PFH4_MAGIC:
                raise ValueError(f"Magic inválido: {magic}. Esperado: {PFH4_MAGIC}")
            
            idx_data = f.read(idx_sz)
            pos = 0
            entries = []
            while pos < idx_sz:
                file_size = struct.unpack_from("<I", idx_data, pos)[0]
                pos += 4
                end_str = idx_data.find(b"\x00", pos)
                rel_path = idx_data[pos:end_str].decode("utf-8", errors="replace")
                pos = end_str + 1
                entries.append((rel_path, file_size))
                
            extracted_count = 0
            for rel_path, file_size in entries:
                data = f.read(file_size)
                # Normaliza separadores de caminho
                norm_rel = rel_path.replace("/", os.sep).replace("\\", os.sep)
                dest_path = os.path.join(output_dir, norm_rel)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as out_f:
                    out_f.write(data)
                extracted_count += 1
                
        return extracted_count

    @staticmethod
    def build_pack(files_list: List[Tuple[str, bytes]], output_pack_path: str, pack_type: int = 3):
        """Compila uma lista de pares (caminho_relativo, bytes) em um contêiner .pack PFH4."""
        # Bloco de Índice
        idx_stream = bytearray()
        for rel_path, data in files_list:
            # CA Warscape usa barras invertidas nos caminhos do índice
            norm_path = rel_path.replace("/", "\\")
            path_bytes = norm_path.encode("utf-8")
            idx_stream.extend(struct.pack("<I", len(data)))
            idx_stream.extend(path_bytes)
            idx_stream.append(0)  # Null terminator
            
        file_count = len(files_list)
        idx_size = len(idx_stream)
        timestamp = 0x648F6EDB  # Timestamp estável de compilação
        
        header = struct.pack("<4sIIIIII", PFH4_MAGIC, pack_type, 0, 0, file_count, idx_size, timestamp)
        
        with open(output_pack_path, "wb") as f:
            f.write(header)
            f.write(idx_stream)
            for _, data in files_list:
                f.write(data)


class MechanicalAnomalySensor:
    """Sensor mecânico anti-alucinação e validador estrito de conformidade."""
    
    @staticmethod
    def audit_tsv(tsv_path: str) -> List[str]:
        anomalies = []
        with open(tsv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if not lines:
            return ["Arquivo TSV vazio"]
            
        header = lines[0].strip().split("\t")
        if len(header) < 2 or header[0] != "key":
            anomalies.append(f"Cabeçalho inválido: {header}")
            
        for idx, line in enumerate(lines[1:], start=2):
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) < 2:
                anomalies.append(f"Linha {idx}: Colunas insuficientes ({len(parts)})")
                continue
            key, val = parts[0], parts[1]
            if not key:
                anomalies.append(f"Linha {idx}: Chave primária vazia")
            if "PLACEHOLDER" in val:
                anomalies.append(f"Linha {idx}: Resíduo de PLACEHOLDER encontrado em '{key}'")
            if "Como um modelo de IA" in val or "As an AI" in val:
                anomalies.append(f"Linha {idx}: Vazamento de alucinação de IA detectado em '{key}'")
                
        return anomalies


def main():
    parser = argparse.ArgumentParser(description="Warscape Compiler / Extractor CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Comando: extract-pack
    p_ext = subparsers.add_parser("extract-pack", help="Extrai todos os arquivos de um .pack")
    p_ext.add_argument("--pack", required=True, help="Caminho do arquivo .pack")
    p_ext.add_argument("--output", required=True, help="Diretório de saída")
    
    # Comando: loc-to-tsv
    p_l2t = subparsers.add_parser("loc-to-tsv", help="Converte .loc para .tsv")
    p_l2t.add_argument("--input", required=True, help="Arquivo .loc de entrada")
    p_l2t.add_argument("--output", required=True, help="Arquivo .tsv de saída")
    
    # Comando: tsv-to-loc
    p_t2l = subparsers.add_parser("tsv-to-loc", help="Converte .tsv para .loc")
    p_t2l.add_argument("--input", required=True, help="Arquivo .tsv de entrada")
    p_t2l.add_argument("--output", required=True, help="Arquivo .loc de saída")
    
    # Comando: audit
    p_aud = subparsers.add_parser("audit", help="Audita diretório de TSVs")
    p_aud.add_argument("--dir", required=True, help="Diretório contendo os TSVs")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    if args.command == "extract-pack":
        count = PackArchive.extract_all(args.pack, args.output)
        print(f"[OK] Extraídos {count} arquivos de '{args.pack}' para '{args.output}'.")
        
    elif args.command == "loc-to-tsv":
        with open(args.input, "rb") as f:
            data = f.read()
        rows = LocCodec.decode(data)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("key\tvalue\tflag\n")
            for k, v, fl in rows:
                f.write(f"{k}\t{v}\t{fl}\n")
        print(f"[OK] Convertido '{args.input}' -> '{args.output}' ({len(rows)} linhas).")
        
    elif args.command == "tsv-to-loc":
        rows = []
        with open(args.input, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[1:]:
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) >= 2:
                fl = int(parts[2]) if len(parts) >= 3 else 1
                rows.append((parts[0], parts[1], fl))
        loc_bytes = LocCodec.encode(rows)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "wb") as f:
            f.write(loc_bytes)
        print(f"[OK] Convertido '{args.input}' -> '{args.output}' ({len(loc_bytes)} bytes).")
        
    elif args.command == "audit":
        total_files = 0
        total_anomalies = 0
        for root, _, files in os.walk(args.dir):
            for file in files:
                if file.endswith(".tsv"):
                    total_files += 1
                    path = os.path.join(root, file)
                    errs = MechanicalAnomalySensor.audit_tsv(path)
                    if errs:
                        total_anomalies += len(errs)
                        print(f"[AVISO] {file}: {len(errs)} anomalias encontradas:")
                        for e in errs[:3]:
                            print(f"  - {e}")
        print(f"[AUDITORIA CONCLUÍDA] Arquivos auditados: {total_files} | Total de anomalias: {total_anomalies}")

if __name__ == "__main__":
    main()
