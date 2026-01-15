import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import fetch_ine_data, fetch_eurostat_data, fetch_esios_data
from analysis import calculate_ictr
from ai_report import generate_economic_report
from pdf_report import create_pdf_report
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
    | **Eurostat** | Oficina estadística de la UE | PIB, Paro, Gini, AROPE, Vivienda, Deuda, Presión Fiscal |
    | **INE** | Instituto Nacional de Estadística | IPC |
    
    **Actualización**: Los datos se descargan en tiempo real y se cachean durante 1 hora.
    
    **Periodo**: Datos desde el año 2000 hasta la actualidad.
    
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
    | **IPC** | Índice de Precios al Consumo | Base 100=2021. Subidas = inflación |
    | **Vivienda** | Índice de precios de vivienda | Base 100=2015. Subidas = encarecimiento |
    | **Deuda Pública** | Deuda total del Estado | En millones de € |
    | **Presión Fiscal** | Ingresos fiscales / PIB | % del PIB que recauda el Estado |
    
    ### Comparativa
    | Indicador | Qué mide | Interpretación |
    |-----------|----------|----------------|
    | **PIB (Base 100)** | Crecimiento acumulado | Permite comparar "velocidad" de crecimiento entre países |
    | **Tasa de Paro** | % población activa desempleada | Datos armonizados de Eurostat |
    
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
esios_token = st.sidebar.text_input("ESIOS Token (Opcional)", type="password", key="esios_token")

# Main Title
st.title("🏘️ Monitor de la Economía Real")
st.markdown("Más allá del PIB: Bienestar, Desigualdad y Comparativa Real.")

# 1. Data Loading Section
with st.spinner('Analizando datos de España y Europa...'):
    
    indicators = {}
    peers_data = {'GDP': {}, 'Unemployment': {}}
    
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
    indicators['IPC'] = get_data_or_dummy(fetch_ine_data, INE_CONFIG["IPC_GENERAL"], "Coste Vida (IPC)", 'M')
    indicators['Vivienda'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["HOUSE_PRICES"], "Precio Vivienda", 'Q')
    
    # 3. Deuda & Esfuerzo Fiscal
    indicators['Deuda_PC'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["DEBT_PC"], "Deuda Pública Total", 'Q')
    indicators['Presion_Fiscal'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["TAX_REVENUE"], "Presión Fiscal", 'Y')

    # 4. Laboral & Educación
    indicators['Paro'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["UNEMPLOYMENT"], "Paro Registrado", 'M')
    indicators['NiNis'] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["NEET"], "Jóvenes Ni-Ni", 'Y')
    
    # --- COMPARATIVA INTERNACIONAL (PEERS) ---
    # Fetch GDP and Unemployment for all peers
    for country in PEER_COUNTRIES:
        peers_data['GDP'][country] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["GDP_PEERS"], f"PIB {country}", 'Q', country=country)
        peers_data['Unemployment'][country] = get_data_or_dummy(fetch_eurostat_data, EUROSTAT_CONFIG["UNEMPLOYMENT"], f"Paro {country}", 'M', country=country)

# 2. Analysis Section (ICTR - Semáforo)
ictr_subset = {k: v for k, v in indicators.items() if k in ['Renta_PC', 'IPC', 'Paro', 'Vivienda', 'Deuda_PC']}
ictr_df, explained_var = calculate_ictr(ictr_subset)

# 3. Dashboard Layout

# Top Metrics (Semaforo Ciudadano)
col1, col2, col3, col4 = st.columns(4)
if ictr_df is not None and not ictr_df.empty:
    current_ictr = ictr_df['ICTR'].iloc[-1]
    prev_ictr = ictr_df['ICTR'].iloc[-2] if len(ictr_df) > 1 else current_ictr
    delta = current_ictr - prev_ictr
    
    # Obtener fechas para contexto
    current_date = ictr_df.index[-1]
    prev_date = ictr_df.index[-2] if len(ictr_df) > 1 else current_date
    
    status_color = "🟢" if delta > 0 else "🔴"
    status_text = "Mejorando" if delta > 0 else "Empeorando"
    
    # Formatear fechas para display
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
tab_peers, tab_welfare, tab_pocket, tab_ia = st.tabs([
    "🌍 Comparativa (Compañeros)", "🏘️ Bienestar & Sociedad", "💰 Tu Bolsillo", "🤖 Informe Inteligente"
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
        st.info("Introduce tu clave Gemini para el análisis inteligente.")
        if st.button("Descargar PDF Datos"):
            pdf_path = create_pdf_report(current_ictr, status_text, indicators)
            with open(pdf_path, "rb") as f:
                st.download_button("Descargar PDF", f, "informe_ciudadano.pdf")