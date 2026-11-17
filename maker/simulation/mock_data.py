"""Cenários mockdata e regras equivalentes às usadas no firmware."""
SCENARIOS = [
    {"label": "BAIXO", "temperatureC": 27.0, "humidityPct": 58.0, "smokeDetected": False},
    {"label": "MEDIO", "temperatureC": 32.0, "humidityPct": 38.0, "smokeDetected": False},
    {"label": "ALTO", "temperatureC": 39.0, "humidityPct": 24.0, "smokeDetected": True},
]

def classify_local(observation):
    if (observation["smokeDetected"] or observation["temperatureC"] >= 38.0
            or observation["humidityPct"] < 25.0):
        return "ALTO"
    if observation["temperatureC"] >= 32.0 or observation["humidityPct"] < 40.0:
        return "MEDIO"
    return "BAIXO"

def consolidate_risk(gold_level, local_level):
    """Retorna a maior severidade; nunca reduz um nível Gold conhecido."""
    severity = {"BAIXO": 0, "MEDIO": 1, "MÉDIO": 1, "ALTO": 2}
    if gold_level not in severity:
        return local_level
    if local_level not in severity:
        return gold_level
    return gold_level if severity[gold_level] >= severity[local_level] else local_level
