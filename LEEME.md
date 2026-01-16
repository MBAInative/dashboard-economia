# 🏘️ Monitor Ciudadano de la Economía Real

> **Dashboard de inteligencia económica ciudadana** — Datos reales de Eurostat e INE sin maquillaje estadístico.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dashboard-economia-hxonunwuovtvxs33vvpcuu.streamlit.app/)

---

## 🎯 Objetivo

Proporcionar a los ciudadanos una visión **veraz y sin sesgos** de la realidad económica española, utilizando exclusivamente datos oficiales de fuentes europeas (Eurostat) y nacionales (INE).

### Principios
- ✅ **Datos reales** — Sin datos simulados ni estimaciones propias
- ✅ **Términos reales** — PIB y renta ajustados por inflación (volúmenes encadenados)
- ✅ **Ratios sobre PIB** — Deuda e ingresos como % del PIB para comparabilidad
- ✅ **Comparativa justa** — Solo con "compañeros de clase" económicos (no con Luxemburgo ni Bulgaria)

---

## 📊 Indicadores Incluidos

### 🌍 Comparativa Internacional
| Indicador | Dataset Eurostat | Unidad | Descripción |
|-----------|------------------|--------|-------------|
| PIB (Base 100) | `namq_10_gdp` | CLV_I10 | Crecimiento acumulado desde 2000 en términos reales |
| Tasa de Paro | `une_rt_m` | PC_ACT | % de población activa desempleada (desestacionalizado) |

**Países comparados**: 🇪🇸 España, 🇩🇪 Alemania, 🇫🇷 Francia, 🇮🇹 Italia, 🇵🇹 Portugal, 🇵🇱 Polonia

### 🏘️ Bienestar & Sociedad
| Indicador | Dataset | Último Valor | Descripción |
|-----------|---------|--------------|-------------|
| Gini | `ilc_di12` | 31.2 | Desigualdad de ingresos (0=igualdad, 100=desigualdad máxima) |
| AROPE | `ilc_peps01` | ~26% | % población en riesgo de pobreza o exclusión |
| Ni-Nis (NEET) | `edat_lfse_20` | 7.2% | % jóvenes 15-29 que ni estudian ni trabajan |

### 💰 Economía Doméstica
| Indicador | Dataset | Último Valor | Descripción |
|-----------|---------|--------------|-------------|
| IPC | INE | ~118 | Índice de Precios al Consumo (inflación acumulada) |
| Vivienda | `prc_hpi_q` | ~160 | Índice precios vivienda (Base 100 = 2015) |
| Deuda Pública | `sdg_17_40` | 101.6% PIB | Deuda bruta gobierno general / PIB |
| Ingresos Públicos | `gov_10a_main` | 42.3% PIB | Total recaudación fiscal / PIB |

### 🚦 ICTR (Indicador Combinado de Tiempo Real)
Índice sintético que combina múltiples indicadores usando **PCA (Análisis de Componentes Principales)**:
- Renta Real per Cápita
- IPC
- Tasa de Paro
- Precio Vivienda
- Deuda Pública

---

## 🔧 Arquitectura Técnica

```
dashboard_de_economía/
├── app/
│   ├── main.py           # Dashboard Streamlit principal
│   ├── data_loader.py    # Funciones de carga desde Eurostat/INE
│   ├── utils.py          # Configuración de indicadores y filtros
│   ├── analysis.py       # Cálculo ICTR con PCA
│   ├── ai_report.py      # Generación de informes con Gemini
│   └── requirements.txt  # Dependencias Python
├── requirements.txt      # Copia en raíz para Streamlit Cloud
├── LEEME.md              # Esta documentación
└── README.md             # Readme básico
```

### Flujo de Datos
```
Eurostat API → eurostat library → data_loader.py → main.py → Plotly/Streamlit
     ↓
   Cache (1 hora TTL)
```

---

## 🛠️ Configuración de Indicadores

Todos los indicadores se configuran en `app/utils.py`:

```python
EUROSTAT_CONFIG = {
    "REAL_GDP_PC": {"code": "sdg_08_10", "filters": {"unit": "CLV20_EUR_HAB", "geo": "ES"}},
    "GINI": {"code": "ilc_di12", "filters": {"age": "TOTAL", "geo": "ES"}},
    "UNEMPLOYMENT": {"code": "une_rt_m", "filters": {"unit": "PC_ACT", "age": "TOTAL", "sex": "T", "s_adj": "SA"}},
    # ... etc
}
```

### Filtros Importantes
| Filtro | Significado | Ejemplo |
|--------|-------------|---------|
| `unit: CLV20_EUR_HAB` | Volúmenes encadenados 2020, EUR/habitante | PIB real per cápita |
| `unit: PC_GDP` | Porcentaje del PIB | Deuda, Ingresos fiscales |
| `unit: PC_ACT` | % población activa | Tasa de paro |
| `s_adj: SA` | Desestacionalizado | Series mensuales |
| `age: TOTAL` | Todas las edades | Evitar desglose por edad |

---

## 🚀 Ejecución

### Local
```bash
# Clonar repositorio
git clone https://github.com/MBAInative/dashboard-economia.git
cd dashboard-economia

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app/main.py
```

### Producción (Streamlit Cloud)
La app está desplegada automáticamente desde GitHub:
- **URL**: https://dashboard-economia-hxonunwuovtvxs33vvpcuu.streamlit.app/
- **Auto-deploy**: Cada push a `master` actualiza la app

---

## 📝 Notas Técnicas

### Cache de Datos
- Los datos de Eurostat se cachean 1 hora (`@st.cache_data(ttl=3600)`)
- Para forzar recarga: añade `?refresh=1` a la URL o reinicia la app

### Agregación de Datos
El `data_loader.py` agrega datos por fecha para evitar duplicados:
```python
result = result.groupby('date')['value'].mean().reset_index()
```
Esto previene las "bandas azules" en gráficas cuando hay múltiples valores por periodo.

### Filtro Temporal
Todos los datos se filtran desde el año 2000:
```python
result = result[result['date'] >= '2000-01-01']
```

### Sin Datos Simulados
A partir de la versión actual, **NO se generan datos simulados**. Si un indicador falla, se muestra un warning y la gráfica queda vacía.

---

## 🔑 Variables de Entorno (Opcionales)

| Variable | Uso |
|----------|-----|
| `gemini_api_key` | Generación de informes IA (sidebar) |
| `esios_token` | Datos de energía ESIOS (futuro) |

---

## 📈 Metodología ICTR

El **Indicador Combinado de Tiempo Real (ICTR)** sintetiza múltiples series en un único valor:

1. **Normalización Z-Score**: Cada indicador se transforma a media 0, desviación 1
2. **PCA**: Se extrae el primer componente principal (tendencia común)
3. **Reescalado**: Se ajusta a base 100 para interpretabilidad

**Interpretación**:
- ICTR > 100 → Economía en expansión
- ICTR < 100 → Economía en contracción
- Fiabilidad (varianza explicada) > 50% → Indicadores correlacionados

---

## 🐛 Problemas Conocidos y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| Gráfica vacía | Dataset sin datos para filtros aplicados | Verificar filtros en `utils.py` |
| Valores incorrectos (ej: 113% Ni-Ni) | Filtro `unit` incorrecto | Usar `PC` en lugar de `PC_POP` |
| Bandas azules en gráficas | Datos duplicados por fecha | Agregar con `.groupby('date').mean()` |
| Datos desde 1975 | Sin filtro temporal | Aplicar `>= 2000-01-01` |

---

## 📄 Licencia

MIT License - Uso libre con atribución.

---

## 👥 Contribuciones

Repositorio: https://github.com/MBAInative/dashboard-economia

Para reportar errores o sugerir mejoras, abre un Issue en GitHub.
