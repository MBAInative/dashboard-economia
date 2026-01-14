# 🏘️ Monitor Ciudadano de la Economía Real (MBAI Native)

> **✅ ESTADO ACTUAL:** 
> La aplicación funciona correctamente con datos reales de Eurostat e INE.
> Última verificación: Enero 2026

---

## 📋 Requerimientos Funcionales (Visión Pablo)

### 1. Enfoque "Per Cápita" y Bienestar
*   **Prioridad:** Renta Per Cápita y Deuda Per Cápita sobre valores absolutos.
*   **Inclusión:** Métricas de desigualdad (Gini) y pobreza (AROPE/FOESSA).
*   **Vivienda:** Foco en la desposesión (acceso a vivienda en jóvenes).

### 2. Comparativa "Compañeros de Clase"
*   **Países Pares:** Comparar España EXCLUSIVAMENTE con:
    *   🇪🇸 España, 🇩🇪 Alemania, 🇫🇷 Francia, 🇮🇹 Italia, 🇵🇹 Portugal, 🇵🇱 Polonia.
*   **Visualización:** Gráficas normalizadas (Base 100) para ver la "velocidad" de crecimiento relativa, no el tamaño absoluto.

### 3. Mercado Laboral "Sin Maquillaje"
*   Evitar el dato crudo de paro registrado si esconde fijos discontinuos. Usar horas trabajadas o tasas armonizadas.

---

## 🛠️ Arquitectura Técnica

### Estructura de Archivos
*   `app/main.py`: **UI (Streamlit)**. Contiene la lógica de visualización (Plotly).
*   `app/utils.py`: **Configuración**. Diccionario `EUROSTAT_CONFIG` con los códigos de series y filtros.
*   `app/data_loader.py`: **Capa de Datos**. Usa la librería `eurostat` con detección robusta de columnas geo.
*   `app/analysis.py`: **Análisis**. Cálculo del ICTR con PCA.
*   `app/ai_report.py`: **IA**. Generación de informes con Gemini.
*   `app/pdf_report.py`: **Exportación**. Generación de PDFs.

---

## 📊 Diccionario de Variables Clave

| Variable | Código Eurostat | Filtros |
| :--- | :--- | :--- |
| PIB Real pc | `sdg_08_10` | `unit="CLV20_EUR_HAB"` |
| PIB Comparado | `namq_10_gdp` | `unit="CLV_I10"`, `s_adj="SCA"`, `na_item="B1GQ"` |
| Paro Comparado | `une_rt_m` | `unit="PC_ACT"`, `age="TOTAL"`, `sex="T"` |
| Gini | `ilc_di12` | - |
| Pobreza (AROPE) | `ilc_peps01` | `unit="PC"`, `age="TOTAL"`, `sex="T"` |

---

## 🏃 Ejecución

```bash
pip install -r app/requirements.txt
streamlit run app/main.py
```

La app se abrirá en http://localhost:8501

---

## 📝 Notas Técnicas

### Caché de Datos
Los datos de Eurostat se cachean durante 1 hora (`@st.cache_data(ttl=3600)`) para evitar descargas repetidas.

### Función Multi-País
Se añadió `fetch_eurostat_multi_country()` en `data_loader.py` para descargar el dataset una sola vez y filtrar por múltiples países, mejorando el rendimiento.
