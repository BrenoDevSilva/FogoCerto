import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

DADOS = Path(__file__).resolve().parent / "dados"


@pytest.fixture
def cfg(tmp_path):
    """Configuração isolada: tudo que o fluxo grava vai para tmp_path."""
    from executar import configuracao

    def _cfg(fonte="risco_valido.json", hoje="2026-11-08", *extra):
        fonte_arg = fonte if str(fonte).startswith("http") or Path(str(fonte)).is_absolute() else str(DADOS / fonte)
        return configuracao([
            "--fonte", fonte_arg,
            "--assinantes", str(DADOS / "assinantes_teste.json"),
            "--saida-mvp", str(tmp_path / "site" / "alertas.json"),
            "--pasta-logs", str(tmp_path / "logs"),
            "--estado", str(tmp_path / "estado" / "enviados.json"),
            "--data-referencia", hoje,
            "--espera", "0",
            *extra,
        ])
    return _cfg
