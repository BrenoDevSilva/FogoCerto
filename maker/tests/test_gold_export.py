import tempfile
import unittest
from pathlib import Path
from simulation.export_gold import REQUIRED_COLUMNS, generate_header

class GoldExportTests(unittest.TestCase):
    def test_generates_header(self):
        row = {column: "1" for column in REQUIRED_COLUMNS}
        row.update({"id_ibge": "1505801", "nome": "Portel", "uf": "PA",
                    "nivel_risco": "ALTO", "data": "2026-11-17"})
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "gold_snapshot.h"
            self.assertEqual(generate_header([row], output), 1)
            generated = output.read_text(encoding="utf-8")
            self.assertIn('"1505801"', generated)
            self.assertIn('"Portel"', generated)
            self.assertIn("GOLD_RECORD_COUNT", generated)

    def test_rejects_missing_columns(self):
        with self.assertRaises(ValueError):
            generate_header([{"nome": "Portel"}], Path("unused.h"))

if __name__ == "__main__":
    unittest.main()
