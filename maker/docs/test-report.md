# Relatório de testes

Execute na raiz `maker/`:
```bash
python -m unittest discover -s tests -v
```

A suíte verifica:
- classificação dos três cenários mockdata;
- regra de consolidação por severidade máxima;
- não redução de um nível Gold conhecido;
- geração do cabeçalho C++ a partir de CSV;
- rejeição de CSV sem colunas obrigatórias.

A suíte Python não substitui a compilação embarcada. A compilação e o teste físico devem ser feitos na Arduino IDE com ESP32 Dev Module e com a biblioteca Edge Impulse original instalada.
