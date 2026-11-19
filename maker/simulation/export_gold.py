#!/usr/bin/env python3
"""Gera firmware/gold_snapshot.h a partir de um CSV da view vw_risco_atual."""
import argparse
import csv
import json
from pathlib import Path

REQUIRED_COLUMNS = [
    "id_ibge", "nome", "uf", "data", "nivel_risco", "pontos",
    "focos_ontem", "umidade_min", "vento_max", "temp_max",
    "chuva_3d", "fatores", "atualizado_em"
]

def cpp_string(value):
    return json.dumps("" if value is None else str(value), ensure_ascii=False)

def cpp_number(value, default="0"):
    raw = "" if value is None else str(value).strip()
    if not raw:
        return default
    return raw.replace(",", ".")

def generate_header(rows, output_path):
    if not rows:
        raise ValueError("O CSV não contém registros.")
    missing = [name for name in REQUIRED_COLUMNS if name not in rows[0]]
    if missing:
        raise ValueError("Colunas ausentes no CSV: " + ", ".join(missing))

    lines = [
        "#pragma once",
        '#include "gold_data.h"',
        "",
        "// Gerado automaticamente por simulation/export_gold.py.",
        "static const GoldRiskRecord GOLD_RECORDS[] = {"
    ]
    for row in rows:
        values = [
            cpp_string(row["id_ibge"]), cpp_string(row["nome"]),
            cpp_string(row["uf"]), cpp_string(row["data"]),
            cpp_string(row["nivel_risco"]), cpp_number(row["pontos"]),
            cpp_number(row["focos_ontem"]), cpp_number(row["umidade_min"]),
            cpp_number(row["vento_max"]), cpp_number(row["temp_max"]),
            cpp_number(row["chuva_3d"]), cpp_string(row["fatores"]),
            cpp_string(row["atualizado_em"])
        ]
        lines.append("  {" + ", ".join(values) + "},")
    generated_at = rows[0].get("atualizado_em", "NAO INFORMADO")
    lines.extend([
        "};",
        "static constexpr size_t GOLD_RECORD_COUNT =",
        "  sizeof(GOLD_RECORDS) / sizeof(GOLD_RECORDS[0]);",
        "static constexpr const char* GOLD_SNAPSHOT_GENERATED_AT = "
        + cpp_string(generated_at) + ";",
        ""
    ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1] / "firmware" / "gold_snapshot.h"
    )
    args = parser.parse_args()
    with args.csv_file.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    count = generate_header(rows, args.output)
    print(f"OK: {count} registros exportados para {args.output}")

if __name__ == "__main__":
    main()
