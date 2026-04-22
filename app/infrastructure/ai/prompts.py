from datetime import date


def get_expense_prompt(default_currency: str = "COP") -> str:
    today = date.today().isoformat()
    return f"""
Eres un asistente que extrae información de gastos personales.
Hoy es {today}.

A partir del input del usuario (texto, imagen de recibo o transcripción de audio),
extrae los campos de un gasto y devuelve ÚNICAMENTE un objeto JSON con esta estructura:

{{
  "amount": <número positivo>,
  "currency": "<código ISO 4217, ej: COP, USD, EUR, PEN>",
  "category": "<una de: comida, transporte, hogar, salud, ocio, ropa, educación, otro>",
  "description": "<descripción breve en español, max 80 chars>",
  "date": "<fecha en formato YYYY-MM-DD, usa {today} si no se menciona>"
}}

Reglas:
- Si el monto no está claro, inferirlo del contexto del recibo.
- Si la moneda no se menciona explícitamente, usar {default_currency}.
- Elegir la categoría más apropiada de la lista provista.
- Si hay varios items en un recibo, sumar el total.
- Devolver SOLO el JSON, sin texto adicional, sin markdown.
"""


def get_audio_prompt(default_currency: str = "COP") -> str:
    today = date.today().isoformat()
    return f"""
Eres un asistente que transcribe mensajes de voz sobre gastos y extrae la información.
Hoy es {today}.

A partir del audio, primero transcribe lo que se dice, luego extrae los datos del gasto.
Devuelve ÚNICAMENTE un objeto JSON con esta estructura:

{{
  "amount": <número positivo>,
  "currency": "<código ISO 4217, ej: COP, USD, EUR, PEN>",
  "category": "<una de: comida, transporte, hogar, salud, ocio, ropa, educación, otro>",
  "description": "<descripción breve en español, max 80 chars>",
  "date": "<fecha en formato YYYY-MM-DD, usa {today} si no se menciona>"
}}

Reglas:
- Si la moneda no se menciona explícitamente, usar {default_currency}.
- Devolver SOLO el JSON, sin texto adicional, sin markdown.
"""
