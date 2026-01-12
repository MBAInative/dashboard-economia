import google.generativeai as genai
import streamlit as st

def generate_economic_report(api_key, data_context):
    """
    Generates a narrative report using Gemini.
    data_context: A dictionary or JSON string with the summary statistics.
    """
    if not api_key:
        return "⚠️ Por favor, introduce tu API Key de Google Gemini en la configuración."
        
    genai.configure(api_key=api_key)
    
    # Select model - trying gemini-pro (Gemini 1.5 or newer if available via alias)
    # 'gemini-pro' is the standard stable alias.
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    ROL: Eres el Economista Jefe de un observatorio económico independiente especializado en la economía española. Tu perfil combina el rigor académico de la econometría con la capacidad de comunicación ejecutiva.

    CONTEXTO DE DATOS (JSON):
    {data_context}

    INSTRUCCIONES DE REDACCIÓN:
    Genera un informe titulado "Estado de la Nación: Análisis Económico en Tiempo Real" siguiendo esta estructura estricta:

    1. Síntesis Ejecutiva: Comienza con el valor del ICTR. ¿Indica expansión o contracción? Destaca el "driver" principal del cambio.
    2. Análisis Macroeconómico (La Ilusión Nominal): Analiza el PIB y la Inflación. Discute la tensión entre crecimiento nominal y real.
    3. Radiografía del Mercado Laboral: Contrasta los datos de la EPA/Afiliación.
    4. Pulso Microeconómico y Social: Utiliza los datos de alta frecuencia y sociales.
    5. Perspectiva de Futuro: Basándote en los componentes adelantados.

    RESTRICCIONES:
    - Basa tus conclusiones exclusivamente en los datos numéricos proporcionados.
    - Si un dato falta o es "null", indícalo como "Dato no disponible" y no especules.
    - Mantén un tono objetivo pero analítico. Evita el lenguaje partidista.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generando el informe: {e}"
