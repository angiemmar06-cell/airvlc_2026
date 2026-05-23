"""
Indice de Calidad del Aire (ICA).

Clasifica un valor numerico en una de cuatro categorias (Bueno, Moderado, Malo,
Peligroso) segun umbrales por contaminante. Devuelve etiqueta + color hex
listos para pintar en mapa y graficas.

Los umbrales se basan en una version simplificada (4 niveles) de las bandas
EEA / OMS. Para contaminantes sin umbrales definidos (variables meteorologicas)
y para valores None, classify() devuelve None.
"""

ICA_CATEGORIES = {
    "good":      {"label": "Bueno",     "color": "#2ECC71"},
    "moderate":  {"label": "Moderado",  "color": "#F1C40F"},
    "bad":       {"label": "Malo",      "color": "#E67E22"},
    "hazardous": {"label": "Peligroso", "color": "#C0392B"},
}

# Umbrales superiores (inclusivos). value <= good -> bueno, etc.
# Cualquier valor por encima del umbral "bad" cae en "hazardous".
POLLUTANT_THRESHOLDS = {
    "no2":   {"good": 40,  "moderate": 100, "bad": 200},  # µg/m³
    "pm10":  {"good": 20,  "moderate": 50,  "bad": 100},  # µg/m³
    "pm2_5": {"good": 10,  "moderate": 25,  "bad": 50},   # µg/m³
    "o3":    {"good": 60,  "moderate": 120, "bad": 180},  # µg/m³
    "so2":   {"good": 40,  "moderate": 100, "bad": 200},  # µg/m³
    "co":    {"good": 4,   "moderate": 9,   "bad": 15},   # mg/m³
}


def classify(pollutant, value):
    """
    Devuelve {key, label, color} para `value` segun `pollutant`, o None si:
    - value es None
    - pollutant no tiene umbrales (variables meteo, metales, etc.)
    """
    if value is None:
        return None

    thresholds = POLLUTANT_THRESHOLDS.get(pollutant)
    if thresholds is None:
        return None

    if value <= thresholds["good"]:
        key = "good"
    elif value <= thresholds["moderate"]:
        key = "moderate"
    elif value <= thresholds["bad"]:
        key = "bad"
    else:
        key = "hazardous"

    return {"key": key, **ICA_CATEGORIES[key]}
