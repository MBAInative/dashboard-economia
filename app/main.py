import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import fetch_ine_data, fetch_eurostat_data, fetch_esios_data_v6, fetch_eurostat_multi_country
from analysis import calculate_ictr
from ai_report import generate_economic_report
from pdf_report import build_pdf_report
from utils import INE_CONFIG, EUROSTAT_CONFIG, PEER_COUNTRIES

# Page Config
st.set_page_config(page_title="Monitor de la Economía Real", layout="wide", page_icon="🏘️")

# --- HELP & CONFIGURATION SIDEBAR ---
st.sidebar.title("Configuración")

with st.sidebar.expander("ℹ️ Ayuda y Metodología Detallada", expanded=False):
    st.markdown("""
    ## 🧠 ¿Cómo funciona esta App?
    
    Esta herramienta es un **monitor de inteligencia económica ciudadana** diseñado para ofrecer una visión veraz y sin sesgos ("sin maquillaje") de la realidad económica española.
    
    ---
    
    ## 📊 Fuentes de Datos
    
    | Fuente | Descripción | Indicadores |
    |--------|-------------|-------------|
    | **Eurostat** | Oficina estadística de la UE | PIB, Paro, Gini, AROPE, Vivienda, Deuda, Presión Fiscal, IPC (HICP), Sentimiento, Población |
    | **INE** | Instituto Nacional de Estadística | Otros indicadores nacionales |
    
    **Actualización**: Los datos se descargan en tiempo real y se cachean durante 24 horas para optimizar el rendimiento.
    
    **Periodo**: Datos desde el año 2000 hasta la actualidad (o fecha disponible).
    
    **Nota sobre retraso**: Los indicadores anuales (PIB pc, Gini) sufren un retraso de 6-18 meses por parte de los organismos oficiales. Los mensuales (Paro, IPC, Sentimiento) son mucho más recientes.
    
    ---
    
    ## 🧮 Metodología del ICTR (El Semáforo)
    
    El **Indicador Combinado de Tiempo Real (ICTR)** sintetiza múltiples indicadores en un único "termómetro" de la economía.
    
    ### Proceso:
    1. **Normalización (Z-Score)**: Transformamos datos heterogéneos (%, €, índices) a una escala común.
    2. **PCA (Análisis de Componentes Principales)**: Extrae matemáticamente la "tendencia común" subyacente.
    3. **Pesos Dinámicos**: El algoritmo asigna pesos según la calidad de la señal, no pesos fijos arbitrarios.
    
    ### Interpretación:
    - **🟢 Mejorando**: El indicador combinado sube respecto al periodo anterior.
    - **🔴 Empeorando**: El indicador combinado baja.
    - **Fiabilidad**: Porcentaje de varianza explicada por el primer componente principal. Un valor alto (>50%) indica que los indicadores "se mueven juntos".
    
    ---
    
    ## 🌍 Comparativa Internacional
    
    ### Países "Compañeros de Clase"
    Comparamos España exclusivamente con economías similares en tamaño y estructura:
    - 🇪🇸 **España** | 🇩🇪 **Alemania** | 🇫🇷 **Francia**
    - 🇮🇹 **Italia** | 🇵🇹 **Portugal** | 🇵🇱 **Polonia**
    
    ### Método "Base 100"
    Para comparar países de distintos tamaños, normalizamos todas las series para que **empiecen en 100** al inicio del periodo.
    
    **Ejemplo**: Si España acaba en **120** y Alemania en **110**:
    - España creció un **20%** desde 2000
    - Alemania creció un **10%** desde 2000
    - España crece más *rápido* (aunque su economía sea menor en tamaño absoluto)
    
    ---
    
    ## 📈 Guía de Indicadores
    
    ### Bienestar & Sociedad
    | Indicador | Qué mide | Interpretación |
    |-----------|----------|----------------|
    | **Gini** | Desigualdad de ingresos (0-100) | 0=Igualdad total, 100=Desigualdad máxima. España ~33 |
    | **AROPE** | % población en riesgo de pobreza | Incluye baja renta, privación material o baja intensidad laboral |
    | **Ni-Nis** | % jóvenes (15-29) que ni estudian ni trabajan | Proxy de fracaso educativo/laboral |
    
    ### Economía Doméstica
    | Indicador | Qué mide | Interpretación |
    |-----------|----------|----------------|
    | **IPC (HICP)** | Índice de Precios al Consumo Armonizado | Base 100=2015. Mide la inflación comparativa en la UE |
    | **Vivienda** | Índice de precios de vivienda | Base 100=2015. Subidas = encarecimiento |
    | **Deuda Per Cápita** | Deuda total / Población | Cuánto debemos cada ciudadano (ajustado por población histórica) |
    | **Presión Fiscal** | Ingresos fiscales / PIB | % del PIB que recauda el Estado |
    
    ### Comparativa & Per Cápita
    | Indicador | Qué mide | Interpretación |
    |-----------|----------|----------------|
    | **PIB (Base 100)** | Crecimiento acumulado | Compara la "velocidad" de crecimiento desde el año 2000 |
    | **Tasa de Paro** | % población activa desempleada | Datos armonizados de Eurostat |
    | **Sentimiento (ESI)** | Confianza de agentes económicos | >100 Optimismo, <100 Pesimismo. Es un indicador adelantado |
    | **PIB Per Cápita** | Riqueza por habitante | Ajustado por inflación (términos reales) |
    
    ---
    
    ## ❓ Preguntas Frecuentes
    
    **¿Por qué los datos empiezan en 2000?**
    Para centrarnos en la economía del siglo XXI y evitar discontinuidades metodológicas.
    
    **¿Por qué España es más gruesa en las gráficas?**
    Destacamos España con una línea más gruesa para facilitar la comparación visual.
    
    **¿Por qué algunos indicadores tienen pocos datos?**
    No todos los indicadores tienen histórico desde 2000. Eurostat actualiza con diferente frecuencia.
    """)

gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password", key="gemini_api_key")
esios_token = st.sidebar.text_input("ESIOS Token (Opcional)", type="password", key="esios_token_input")

if st.sidebar.button("⚡ Probar Conexión ESIOS"):
    if not esios_token:
        st.sidebar.error("Introduce un token primero.")
    else:
        try:
            headers = {
                "Accept": "application/json; application/vnd.esios-api-v1+json",
                "Content-Type": "application/json",
                "x-api-key": esios_token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            # Indicator 1001: Precios Voluntarios Pequeño Consumidor (Simple metadata check)
            url = "https://api.esios.ree.es/indicators/1001"
            with st.spinner("Conectando con REE..."):
                r = requests.get(url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                data = r.json()
                name = data['indicator']['short_name'] if 'indicator' in data else "OK"
                st.sidebar.success(f"✅ Conexión Exitosa\n\nAcceso a: {name}")

            elif r.status_code == 401:
                st.sidebar.error("❌ Token Inválido (401)")
            else:
                st.sidebar.error(f"❌ Error {r.status_code}")
        except Exception as e:
            st.sidebar.error(f"Error de conexión: {e}")


st.sidebar.markdown("---")
# (El botón de PDF se renderizará al final del script para asegurar que los datos están listos)

# Main Title
st.title("🏘️ Monitor de la Economía Real")
st.markdown("Más allá del PIB: Bienestar, Desigualdad y Comparativa Real.")
st.caption("📅 **Nota sobre datos**: Eurostat publica indicadores anuales con 6-18 meses de retraso. Los datos mensuales (paro, IPC) son más recientes.")

# 1. Data Loading Section
with st.spinner('Analizando datos de España y Europa...'):
    
    indicators = {}
    peers_data = {'GDP': {}, 'Unemployment': {}, 'Sentiment': {}}
    
    # Helper for fetching data (NO dummy data - only real data)
    def get_data_or_dummy(func, config_item, name, freq='M', country='ES'):
        code = config_item
        filters = {}
        
        if isinstance(config_item, dict):
            if 'code' in config_item:
                code = config_item['code']
                filters = config_item.get('filters', {}).copy()
                # Override geo if creating peers data
                if country != 'ES':
                    filters['geo'] = country
            elif 'id' in config_item: 
                code = config_item['id']
        
        df = pd.DataFrame()
        try:
            if func:
                if func.__name__ == 'fetch_ine_data' and country == 'ES':
                    df = func(code)
                elif func.__name__ == 'fetch_eurostat_data':
                    df = func(code, filters=filters)
        except Exception as e:
            st.warning(f"Error cargando {name}: {e}")
            
        # NO fallback to dummy data - return empty DataFrame if no data
        if df is None:
            df = pd.DataFrame()
        
        return df

    # --- INDICADORES ESPAÑA (PRINCIPALES) ---
    # 1. Bienestar & Desigualdad
    indicators['Renta_PC'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["REAL_GDP_PC"], "Renta Real per Cápita", 'Y')
    indicators['Gini'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["GINI"], "Desigualdad (Gini)", 'Y')
    indicators['AROPE'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["AROPE"], "Riesgo Pobreza", 'Y')
    
    # 2. Economía Doméstica
    indicators['IPC'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["HICP"], "Coste Vida (IPC)", 'M')
    indicators['Vivienda'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["HOUSE_PRICES"], "Precio Vivienda", 'Q')
    
    # 3. Deuda & Esfuerzo Fiscal
    indicators['Deuda_PC'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["DEBT_PC"], "Deuda Pública Total", 'Q')
    indicators['Presion_Fiscal'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["TAX_REVENUE"], "Presión Fiscal", 'Y')

    # 4. Laboral & Educación
    indicators['Paro'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["UNEMPLOYMENT"], "Paro Registrado", 'M')
    indicators['NiNis'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["NEET"], "Jóvenes Ni-Ni", 'Y')
    
    # 5. Per Cápita
    indicators['Poblacion'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["POPULATION"], "Población", 'Y')
    indicators['Deuda_Abs'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["DEBT_ABSOLUTE"], "Deuda Absoluta", 'Y')
    
    # 6. Datos de Alta Frecuencia (ESIOS)
    if esios_token:
        indicators['Demanda_Electrica'] = fetch_esios_data_v6(esios_token)
    else:
        indicators['Demanda_Electrica'] = pd.DataFrame()
    
    # --- COMPARATIVA INTERNACIONAL (PEERS) ---
    # Usar fetch_eurostat_multi_country para eficiencia (1 descarga por indicador)
    gdp_config = EUROSTAT_CONFIG["GDP_PEERS"]
    gdp_filters = {k: v for k, v in gdp_config.get('filters', {}).items() if k.lower() != 'geo'}
    peers_data['GDP'] = fetch_eurostat_multi_country(gdp_config['code'], PEER_COUNTRIES, gdp_filters)
    
    unemp_config = EUROSTAT_CONFIG["UNEMPLOYMENT"]
    unemp_filters = {k: v for k, v in unemp_config.get('filters', {}).items() if k.lower() != 'geo'}
    peers_data['Unemployment'] = fetch_eurostat_multi_country(unemp_config['code'], PEER_COUNTRIES, unemp_filters)
    
    sent_config = EUROSTAT_CONFIG["SENTIMENT"]
    sent_filters = {k: v for k, v in sent_config.get('filters', {}).items() if k.lower() != 'geo'}
    peers_data['Sentiment'] = fetch_eurostat_multi_country(sent_config['code'], PEER_COUNTRIES, sent_filters)

# 2. Analysis Section (ICTR - Semáforo)
ictr_subset = {k: v for k, v in indicators.items() if k in ['Renta_PC', 'IPC', 'Paro', 'Vivienda', 'Deuda_PC']}
ictr_df, explained_var = calculate_ictr(ictr_subset)

# Save to session state for PDF/persistence
st.session_state.indicators = indicators
st.session_state.peers_data = peers_data
st.session_state.current_ictr = ictr_df['ICTR'].iloc[-1] if not ictr_df.empty else 100
current_ictr = st.session_state.current_ictr

# Determine status
last_ictr = ictr_df['ICTR'].iloc[-1] if not ictr_df.empty else 100
prev_ictr = ictr_df['ICTR'].iloc[-2] if len(ictr_df) > 1 else last_ictr
delta = last_ictr - prev_ictr

status_color = "🟢" if delta > 0 else ("🔴" if delta < 0 else "🟡")
status_text = "Mejorando" if delta > 0 else ("Empeorando" if delta < 0 else "Estable")
status_full = f"{status_color} {status_text}"

st.session_state.status_text = status_full
st.session_state.status_color = status_color # Added for metrics use

# 3. Dashboard Layout
# Top Metrics (Semaforo Ciudadano)
col1, col2, col3, col4 = st.columns(4)

if not ictr_df.empty:
    # Obtener fechas para contexto
    current_date = ictr_df.index[-1]
    prev_date = ictr_df.index[-2] if len(ictr_df) > 1 else current_date
    
    # Formatear fechas para display (usando .date() si es Timestamp para evitar problemas)
    current_date_str = current_date.strftime('%b %Y') if hasattr(current_date, 'strftime') else str(current_date)[:7]
    prev_date_str = prev_date.strftime('%b %Y') if hasattr(prev_date, 'strftime') else str(prev_date)[:7]
    
    col1.metric(
        f"ICTR {status_color}", 
        f"{current_ictr:.1f}", 
        f"{delta:+.2f} vs {prev_date_str}",
        help=f"Indicador Combinado de Tiempo Real. Base 100. Último periodo: {current_date_str}"
    )
    
    col2.metric(
        "Tendencia", 
        status_text, 
        f"Comparado con {prev_date_str}"
    )
    
    renta_df = indicators['Renta_PC']
    if not renta_df.empty:
        r_current = renta_df['value'].iloc[-1]
        r_prev = renta_df['value'].iloc[-2] if len(renta_df) > 1 else r_current
        r_delta = r_current - r_prev
        col3.metric("Renta Real pc", f"{r_current:,.0f} €", f"{r_delta:+,.0f} € YoY")
    else:
        col3.metric("Renta Real pc", "N/A")
        
    col4.metric(
        "Fiabilidad ICTR", 
        f"{explained_var[0]*100:.1f}%" if explained_var is not None else "N/A",
        help="Varianza explicada por el primer componente PCA. >50% indica indicadores correlacionados."
    )
    
    # Gráfica ICTR
    with st.expander("📈 Ver evolución histórica del ICTR", expanded=False):
        st.caption("El ICTR (Indicador Combinado de Tiempo Real) sintetiza múltiples indicadores en un único valor. Base 100 = nivel neutral. Por encima = economía en expansión, por debajo = contracción.")
        
        # Crear gráfica con Plotly para mejor control
        fig_ictr = go.Figure()
        fig_ictr.add_trace(go.Scatter(
            x=ictr_df.index, 
            y=ictr_df['ICTR'], 
            mode='lines',
            name='ICTR',
            line=dict(color='#1f77b4', width=3),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))
        
        # Línea de base 100
        fig_ictr.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="Base 100")
        
        fig_ictr.update_layout(
            yaxis_title="ICTR",
            xaxis_title="",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            height=300
        )
        st.plotly_chart(fig_ictr, use_container_width=True)
        
        # Estadísticas resumidas
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        col_stats1.metric("Mínimo histórico", f"{ictr_df['ICTR'].min():.1f}")
        col_stats2.metric("Máximo histórico", f"{ictr_df['ICTR'].max():.1f}")
        col_stats3.metric("Media", f"{ictr_df['ICTR'].mean():.1f}")

# Tabs Reorganized
tab_peers, tab_percapita, tab_welfare, tab_pocket, tab_ia = st.tabs([
    "🌍 Comparativa", "👤 Per Cápita", "🏘️ Bienestar", "💰 Tu Bolsillo", "🤖 Informe IA"
])

with tab_peers:
    st.header("¿Cómo vamos respecto a nuestros vecinos?")
    st.caption("Comparativa exclusiva con: Alemania, Francia, Italia, Portugal y Polonia.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Evolución del Crecimiento (PIB)")
        st.caption("Base 100 al inicio de la serie. Permite comparar quién crece más rápido independientemente del tamaño del país.")
        fig_gdp = go.Figure()
        
        all_vals = []
        for ctry, df in peers_data['GDP'].items():
            if not df.empty:
                # Normalización: (Valor / Primer Valor) * 100
                first_val = df['value'].iloc[0]
                df_norm = df.copy()
                df_norm['value_norm'] = (df['value'] / first_val) * 100
                
                # Highlight Spain
                width = 5 if ctry=='ES' else 2
                opacity = 1.0 if ctry=='ES' else 0.6
                
                fig_gdp.add_trace(go.Scatter(x=df_norm['date'], y=df_norm['value_norm'], mode='lines', name=ctry, 
                                             line=dict(width=width), opacity=opacity,
                                             hovertemplate='%{y:.1f} (Base 100)'))
                all_vals.extend(df_norm['value_norm'])
        
        # Dynamic Layout for Zoom (Preserved)
        if all_vals:
            y_min = min(all_vals)
            y_max = max(all_vals)
            margin = (y_max - y_min) * 0.1
            fig_gdp.update_layout(
                yaxis=dict(range=[y_min - margin, y_max + margin]),
                hovermode="x unified",
                yaxis_title="Crecimiento Acumulado",
                legend=dict(orientation="h", y=1.1),
                margin=dict(l=0, r=0, t=10, b=0)
            )
        st.plotly_chart(fig_gdp, use_container_width=True)
        st.info("Interpretación: Si la línea de España está por encima, crecemos más rápido que el resto.")
        
    with col_b:
        st.subheader("Desempleo (Tasa de Paro)")
        fig_unemp = go.Figure()
        all_vals_unemp = []
        for ctry, df in peers_data['Unemployment'].items():
            if not df.empty:
                width = 5 if ctry=='ES' else 2
                opacity = 1.0 if ctry=='ES' else 0.6
                fig_unemp.add_trace(go.Scatter(x=df['date'], y=df['value'], mode='lines', name=ctry,
                                               line=dict(width=width), opacity=opacity,
                                               hovertemplate='%{y:.1f}%'))
                all_vals_unemp.extend(df['value'])
        
        # Dynamic Layout
        if all_vals_unemp:
            y_min = min(all_vals_unemp)
            y_max = max(all_vals_unemp)
            margin = (y_max - y_min) * 0.1
            fig_unemp.update_layout(
                yaxis=dict(range=[y_min - margin, y_max + margin]),
                hovermode="x unified",
                yaxis_title="Tasa de Paro (%)",
                legend=dict(orientation="h", y=1.1),
                margin=dict(l=0, r=0, t=10, b=0)
            )
        st.plotly_chart(fig_unemp, use_container_width=True)
        st.info("Nota: Menos es mejor. Compara la brecha de España con el resto.")
        
    st.markdown("---")
    st.subheader("🧠 Índice de Sentimiento Económico (Expectativas)")
    st.caption("Indicador adelantado que mide la confianza de empresas y consumidores. **100** es el promedio histórico. Valores > 100 indican optimismo. Fuente: Eurostat (teibs010).")
    
    fig_sent = go.Figure()
    all_vals_sent = []
    for ctry, df in peers_data['Sentiment'].items():
        if not df.empty:
            width = 5 if ctry=='ES' else 2
            opacity = 1.0 if ctry=='ES' else 0.6
            fig_sent.add_trace(go.Scatter(x=df['date'], y=df['value'], mode='lines', name=ctry,
                                           line=dict(width=width), opacity=opacity,
                                           hovertemplate='%{y:.1f}'))
            all_vals_sent.extend(df['value'])
            
    if all_vals_sent:
        y_min = min(all_vals_sent)
        y_max = max(all_vals_sent)
        margin = (y_max - y_min) * 0.1
        fig_sent.update_layout(
            yaxis=dict(range=[y_min - margin, y_max + margin]),
            hovermode="x unified",
            yaxis_title="Índice de Confianza",
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=0, r=0, t=10, b=0)
        )
    st.plotly_chart(fig_sent, use_container_width=True)
    st.info("💡 **Dato clave**: El sentimiento suele 'adelantarse' a los movimientos del PIB. Caídas continuadas predicen recesiones.")

with tab_percapita:
    st.header("Indicadores Per Cápita")
    st.caption("La economía vista desde la perspectiva del ciudadano individual. Todos los valores divididos por la población de cada año.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("PIB Real per Cápita (€)")
        st.caption("Producción económica dividida entre la población. En términos reales (ajustado por inflación). Fuente: Eurostat (sdg_08_10).")
        if not indicators['Renta_PC'].empty:
            st.line_chart(indicators['Renta_PC'].set_index('date')['value'])
            ultimo = indicators['Renta_PC']['value'].iloc[-1]
            primero = indicators['Renta_PC']['value'].iloc[0]
            crecimiento = ((ultimo / primero) - 1) * 100
            st.info(f"**Último dato**: {ultimo:,.0f} € | **Crecimiento desde 2000**: +{crecimiento:.1f}%")
        else:
            st.warning("Datos no disponibles")
    
    with col_b:
        st.subheader("Deuda Pública per Cápita (€)")
        st.caption("Deuda del gobierno dividida entre la población de cada año. Fuente: Eurostat (gov_10dd_edpt1).")
        
        # Calcular deuda per cápita usando población histórica
        if not indicators['Deuda_Abs'].empty and not indicators['Poblacion'].empty:
            deuda_df = indicators['Deuda_Abs'].copy()
            pob_df = indicators['Poblacion'].copy()
            
            # Merge por año
            deuda_df['year'] = deuda_df['date'].dt.year
            pob_df['year'] = pob_df['date'].dt.year
            
            merged = deuda_df.merge(pob_df[['year', 'value']], on='year', suffixes=('_deuda', '_pob'))
            
            if not merged.empty:
                # Deuda en millones EUR, población en unidades -> per cápita en EUR
                merged['deuda_pc'] = (merged['value_deuda'] * 1_000_000) / merged['value_pob']
                
                chart_data = merged[['date', 'deuda_pc']].set_index('date')
                st.line_chart(chart_data['deuda_pc'])
                
                ultimo_deuda_pc = merged['deuda_pc'].iloc[-1]
                primero_deuda_pc = merged['deuda_pc'].iloc[0]
                crecimiento_deuda = ((ultimo_deuda_pc / primero_deuda_pc) - 1) * 100
                st.info(f"**Último dato**: {ultimo_deuda_pc:,.0f} € por habitante | **Crecimiento**: +{crecimiento_deuda:.1f}%")
            else:
                st.warning("No se pudo calcular - datos incompatibles")
        else:
            st.warning("Datos de deuda o población no disponibles")
    
    st.markdown("---")
    st.subheader("📊 Población de España (histórico)")
    st.caption("Evolución de la población residente en España. Fuente: Eurostat (demo_gind).")
    if not indicators['Poblacion'].empty:
        pob_chart = indicators['Poblacion'].copy()
        pob_chart['value'] = pob_chart['value'] / 1000  # Convertir a millones
        st.line_chart(pob_chart.set_index('date')['value'])
        ultimo_pob = indicators['Poblacion']['value'].iloc[-1] / 1000
        st.info(f"**Última población**: {ultimo_pob:.1f} millones de habitantes")
    else:
        st.warning("Datos no disponibles")

with tab_welfare:
    st.header("La Realidad Social: Pobreza y Desigualdad")
    st.caption("Indicadores de bienestar que miden cómo se reparte la riqueza y quién queda atrás.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Desigualdad (Índice Gini)")
        st.caption("Mide la distribución de la riqueza. **0** = igualdad perfecta (todos igual), **100** = desigualdad máxima (uno tiene todo). Fuente: Eurostat (ilc_di12).")
        if not indicators['Gini'].empty:
            st.line_chart(indicators['Gini'].set_index('date')['value'])
            ultimo_gini = indicators['Gini']['value'].iloc[-1]
            interpretacion = "alta" if ultimo_gini > 35 else ("moderada" if ultimo_gini > 30 else "baja")
            st.info(f"**Último dato**: {ultimo_gini:.1f} | **Interpretación**: Desigualdad {interpretacion} para estándares europeos")
        else:
            st.warning("Datos no disponibles")
        
    with col_b:
        st.subheader("Riesgo de Pobreza (Tasa AROPE)")
        st.caption("% de población en riesgo de pobreza o exclusión social. Combina: baja renta (<60% mediana), privación material severa, y baja intensidad laboral. Fuente: Eurostat (ilc_peps01).")
        if not indicators['AROPE'].empty:
            st.line_chart(indicators['AROPE'].set_index('date')['value'])
            ultimo_arope = indicators['AROPE']['value'].iloc[-1]
            st.info(f"**Último dato**: {ultimo_arope:.1f}% de la población | Aproximadamente {ultimo_arope * 0.47:.1f} millones de personas")
        else:
            st.warning("Datos no disponibles")
        
    st.markdown("---")
    st.subheader("Futuro: Jóvenes 'Ni-Ni' (Educación/Laboral)")
    st.caption("Porcentaje de jóvenes de 15-29 años que **ni estudian ni trabajan** (NEET). Es un proxy del fracaso del sistema educativo y del mercado laboral juvenil. Fuente: Eurostat (edat_lfse_20).")
    if not indicators['NiNis'].empty:
        st.line_chart(indicators['NiNis'].set_index('date')['value'])
        ultimo_nini = indicators['NiNis']['value'].iloc[-1]
        st.info(f"**Último dato**: {ultimo_nini:.1f}% de jóvenes (15-29 años) | Aprox. {int(ultimo_nini * 8 / 100 * 1000)}k jóvenes afectados")
    else:
        st.warning("Datos no disponibles")

with tab_pocket:
    st.header("Economía Doméstica")
    st.caption("Indicadores que afectan directamente a tu bolsillo: inflación, vivienda y fiscalidad.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Coste de la Vida (IPC)")
        st.caption("Índice de Precios al Consumo. Mide la inflación acumulada. Base 100 = año referencia. Si sube, tu dinero vale menos.")
        if not indicators['IPC'].empty:
            st.line_chart(indicators['IPC'].set_index('date')['value'])
            st.info(f"**Último dato**: {indicators['IPC']['value'].iloc[-1]:.1f} | **Variación desde inicio**: {((indicators['IPC']['value'].iloc[-1] / indicators['IPC']['value'].iloc[0]) - 1) * 100:.1f}%")
        else:
            st.warning("Datos no disponibles")
        
    with col_b:
        st.subheader("Vivienda (Precio)")
        st.caption("Índice de precios de la vivienda. Base 100 = 2015. Refleja la evolución del coste de acceso a la vivienda.")
        if not indicators['Vivienda'].empty:
            st.line_chart(indicators['Vivienda'].set_index('date')['value'])
            st.info(f"**Último dato**: {indicators['Vivienda']['value'].iloc[-1]:.1f} | **Variación desde 2015**: {indicators['Vivienda']['value'].iloc[-1] - 100:.1f}%")
        else:
            st.warning("Datos no disponibles")
        
    st.markdown("---")
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Deuda Pública (% PIB)")
        st.caption("Deuda bruta del gobierno general como porcentaje del PIB. Mide el nivel de endeudamiento relativo a la economía. Fuente: Eurostat (sdg_17_40).")
        if not indicators['Deuda_PC'].empty:
            st.line_chart(indicators['Deuda_PC'].set_index('date')['value'])
            ultimo_deuda = indicators['Deuda_PC']['value'].iloc[-1]
            st.info(f"**Último dato**: {ultimo_deuda:.1f}% del PIB | El criterio de Maastricht establece un límite del 60%")
        else:
            st.warning("Datos no disponibles")
            
    with col_d:
        st.subheader("Ingresos Públicos (% PIB)")
        st.caption("Total de ingresos del gobierno general como % del PIB. Incluye impuestos y cotizaciones sociales. Fuente: Eurostat (gov_10a_main).")
        if not indicators['Presion_Fiscal'].empty:
            st.line_chart(indicators['Presion_Fiscal'].set_index('date')['value'])
            st.info(f"**Último dato**: {indicators['Presion_Fiscal']['value'].iloc[-1]:.1f}% del PIB | Media UE: ~46%")
        else:
            st.warning("Datos no disponibles")

    # Demanda Eléctrica (ESIOS)
    if not indicators['Demanda_Electrica'].empty:
        st.markdown("---")
        st.subheader("⚡ Demanda Eléctrica en Tiempo Real (ESIOS)")
        st.caption("Consumo diario promedio en MW. Un aumento sostenido suele preceder a una mayor actividad industrial. Fuente: ESIOS (REE).")
        
        esios_df = indicators['Demanda_Electrica'].set_index('date')
        
        # Calcular Tendencia (Media Móvil 365 días - Anual)
        if len(esios_df) > 365:
            esios_df['Trend_365'] = esios_df['value'].rolling(window=365).mean()
            
            # Calcular Variación Cuantitativa
            try:
                current_val = float(esios_df['Trend_365'].dropna().iloc[-1])
                # Comparar con hace 1 año (365 días)
                year_ago_val = float(esios_df['Trend_365'].dropna().iloc[-366]) if len(esios_df['Trend_365'].dropna()) > 366 else current_val
                delta_perc = ((current_val / year_ago_val) - 1) * 100
                
                status_elec = "CRECIENTE" if delta_perc > 0 else "DECRECIENTE"
                color_elec = "green" if delta_perc > 0 else "red"
                
                st.markdown(f"""
                **Análisis de Tendencia (Media Móvil Anual):** 
                La demanda estructural está en fase **:{color_elec}[{status_elec}]** ({delta_perc:+.2f}% vs hace un año).
                """)
            except IndexError:
                st.warning("Datos ESIOS insuficientes para calcular tendencia anual.")
                
            # Gráfica Plotly
            fig_esios = go.Figure()
            
            # Datos DIARIOS (Azul suave)
            fig_esios.add_trace(go.Scatter(
                x=esios_df.index, y=esios_df['value'],
                mode='lines', name='Demanda Diaria',
                line=dict(color='rgba(31, 119, 180, 0.4)', width=1)
            ))
            
            # Tendencia Roja (Media 365 días)
            fig_esios.add_trace(go.Scatter(
                x=esios_df.index, y=esios_df['Trend_365'],
                mode='lines', name='Tendencia (Media 1 año)',
                line=dict(color='red', width=3)
            ))
            
            fig_esios.update_layout(
                height=400,
                yaxis_title="Potencia (MW)",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_esios, use_container_width=True)
            
        else:
            st.warning(f"Histórico ESIOS incompleto ({len(esios_df)} días). Se requieren >365 días para la tendencia.")

with tab_ia:
    st.header("Análisis de la Verdad")
    st.markdown("Generación de informes para detectar 'maquillaje' estadístico.")
    
    if gemini_api_key:
        if st.button("Generar Informe Ciudadano"):
            with st.spinner("Analizando datos reales..."):
                context = {
                    "Tendencia": status_text,
                    "Renta_PC": indicators['Renta_PC']['value'].iloc[-1] if not indicators['Renta_PC'].empty else "N/A",
                    "Gini": indicators['Gini']['value'].iloc[-1] if not indicators['Gini'].empty else "N/A",
                    "Paro_ES": indicators['Paro']['value'].iloc[-1] if not indicators['Paro'].empty else "N/A",
                }
                report = generate_economic_report(gemini_api_key, context)
                st.markdown(report)
    else:
        st.info("Introduce tu clave Gemini en el sidebar para el análisis inteligente.")

# --- SIDEBAR: PDF EXPORT (At the end to ensure data is ready) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("📥 Exportar Informe PDF")
    st.caption("Análisis detallado de España vs. Europa")
    
    if st.button("📄 Generar Informe Analítico", key="gen_pdf_btn"):
        with st.spinner("Procesando datos y análisis IA..."):
            try:
                ai_text = None
                if gemini_api_key:
                    context = {
                        "Tendencia": status_text,
                        "Renta_PC": indicators['Renta_PC']['value'].iloc[-1] if not indicators['Renta_PC'].empty else "N/A",
                        "Gini": indicators['Gini']['value'].iloc[-1] if not indicators['Gini'].empty else "N/A",
                        "Paro_ES": indicators['Paro']['value'].iloc[-1] if not indicators['Paro'].empty else "N/A",
                    }
                    ai_text = generate_economic_report(gemini_api_key, context)

                # Prepare ESIOS data if available
                esios_data_for_pdf = None
                if 'Demanda_Electrica' in indicators and not indicators['Demanda_Electrica'].empty:
                    # Re-create trend logic locally for PDF (window 365 days)
                    esios_raw = indicators['Demanda_Electrica'].set_index('date')
                    esios_raw['Trend_365'] = esios_raw['value'].rolling(window=365).mean()
                    esios_data_for_pdf = esios_raw

                # We have direct access to indicators, peers_data, etc. at this point in the script
                pdf_path = build_pdf_report(current_ictr, status_text, indicators, peers_data, ai_analysis=ai_text, esios_data=esios_data_for_pdf)
                st.session_state.final_pdf_path = pdf_path
                if ai_text:
                    st.success("¡Informe con IA listo!")
                else:
                    st.success("¡Informe listo!")
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")

    if "final_pdf_path" in st.session_state:
        try:
            with open(st.session_state.final_pdf_path, "rb") as f:
                st.download_button(
                    label="💾 Descargar PDF Ahora",
                    data=f,
                    file_name="informe_ciudadano_completo.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Error al descargar PDF: {e}")

    st.markdown("---")
    st.subheader("📊 Exportar Datos (Excel)")
    st.caption("Descarga todos los indicadores en formato .xlsx")
    
    if st.button("Generar Excel Completo"):
        import io
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer) as writer:
                # ESIOS
                if 'Demanda_Electrica' in indicators and not indicators['Demanda_Electrica'].empty:
                    indicators['Demanda_Electrica'].to_excel(writer, sheet_name='ESIOS_Demanda')
                
                # Otros Indicadores (INE/Eurostat)
                for name, df in indicators.items():
                    if name != 'Demanda_Electrica' and not df.empty:
                        # Limpiar nombre para sheet (max 31 chars)
                        sheet_name = name[:30]
                        df.to_excel(writer, sheet_name=sheet_name)
                        
                # Peers Data (Comparativa)
                if not peers_data.empty:
                    peers_data.to_excel(writer, sheet_name='Comparativa_Europa')
                    
            st.download_button(
                label="💾 Descargar Excel",
                data=buffer.getvalue(),
                file_name="datos_economia_espana.xlsx",
                mime="application/vnd.ms-excel"
            )
            st.success("Excel generado correctamente.")
        except Exception as e:
            st.error(f"Error generando Excel: {e}")
        except FileNotFoundError:
            pass

    st.markdown("---")
    st.caption("© 2026 Luis Benedicto Tuzón & Gemini")
    st.caption("lbt00001@gmail.com")