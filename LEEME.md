# Dashboard de Economía Española (Streamlit + AI)

Este proyecto es un cuadro de mando integral para analizar la economía española en comparación con Europa, utilizando datos oficiales (INE, Eurostat, ESIOS) y análisis de Inteligencia Artificial (Google Gemini).

## 🚀 Funcionalidades Principales

1.  **Indicadores Macro:** PIB, Paro, Inflación (IPC), Deuda Pública, Presión Fiscal.
2.  **Comparativa Europea:** Posicionamiento de España vs. Media UE-27 y Eurozona.
3.  **Economía Real (Alta Frecuencia):**
    *   **Consumo Eléctrico (ESIOS):** Indicador adelantado de actividad industrial.
    *   *Nota Técnica:* Se usa la estrategia `fetch_esios_data_v6` para descargar datos "raw" mes a mes y evitar inconsistencias en la API de Red Eléctrica.
4.  **Análisis de "La Verdad":**
    *   Uso de **Google Gemini Pro** para auditar los datos y generar informes imparciales ("Informe Ciudadano").
    *   Detecta anomalías o "maquillaje" estadístico.
5.  **Exportación:**
    *   **PDF:** Informes maquetados con gráficos y análisis de IA.
    *   **Excel:** Descarga completa de series históricas.

## 🛠️ Instalación y Ejecución

### Requisitos
*   Python 3.10+
*   Clave API de **ESIOS (Red Eléctrica)** (Opcional, para datos eléctricos).
*   Clave API de **Google Gemini** (Opcional, para análisis de texto).

### Pasos
1.  Clonar el repositorio:
    ```bash
    git clone https://github.com/PabloSanzBayon/dashboard_de_economia.git
    cd dashboard_de_economia
    ```
2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ejecutar la aplicación:
    ```bash
    streamlit run app/main.py
    ```

## 🏗️ Estructura del Proyecto

*   **`app/main.py`**: Punto de entrada. Interfaz UI, integración de gráficas y lógica principal.
*   **`app/data_loader.py`**: Motor de datos.
    *   `fetch_esios_data_v6`: *Crítico*. Descarga datos horarios brutos y recalcula la media diaria localmente.
    *   `fetch_ine_data`, `fetch_eurostat_data`: Conectores a APIs estadísticas.
*   **`app/pdf_report.py`**: Generador de informes PDF con `fpdf` y `matplotlib`.
*   **`app/ai_report.py`**: Módulo de conexión con Google Gemini.

## ☁️ Despliegue en Streamlit Cloud

1.  Crear nuevo proyecto en [share.streamlit.io](https://share.streamlit.io).
2.  Conectar repositorio GitHub.
3.  Configurar **Secrets** (Opcional pero recomendado):
    ```toml
    # .streamlit/secrets.toml
    ESIOS_TOKEN = "tu_token_aqui"
    GEMINI_API_KEY = "tu_api_key_aqui"
    ```

---
**Desarrollado para MBAI Native / Pablo Sanz Bayón**
*Documentación actualizada: Enero 2026*
