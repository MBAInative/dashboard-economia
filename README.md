# 🇪🇸 Monitor Económico en Tiempo Real (MBAI Native)

Este proyecto implementa el **Indicador Combinado de Tiempo Real (ICTR)** para la economía española, basado en la metodología "Gemini 3". Utiliza datos de alta frecuencia y análisis de IA para ofrecer un diagnóstico económico instantáneo, superando el retraso de las estadísticas oficiales tradicionales.

## 🚀 Despliegue en Streamlit Cloud

1.  Haz un Fork o sube este repositorio a GitHub.
2.  Conecta tu cuenta de GitHub en [Streamlit Cloud](https://share.streamlit.io).
3.  Crea una nueva app seleccionando este repositorio.
4.  **Configuración de Secretos:**
    Para que la IA funcione, debes configurar las claves en el panel de administración de Streamlit (Settings > Secrets):

    ```toml
    GEMINI_API_KEY = "tu-api-key-de-google"
    # Opcional para datos eléctricos reales
    ESIOS_TOKEN = "tu-token-de-red-electrica"
    ```

## 🛠️ Instalación Local

```bash
cd app
pip install -r requirements.txt
streamlit run main.py
```

## 🧠 Arquitectura

*   **Fuentes de Datos:** INE (JSON-stat), Eurostat, ESIOS.
*   **Procesamiento:** Python + Pandas + Scikit-Learn (PCA).
*   **Inteligencia Artificial:** Google Gemini Pro (Generación de informes narrativos).
*   **Frontend:** Streamlit.

## 📄 Licencia

MIT License - MBAI Native
