from fpdf import FPDF
import pandas as pd
import tempfile

class EconomicReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Monitor Economico MBAI Native', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf_report(ictr_val, trend_val, indicators_dict, peers_data=None):
    pdf = EconomicReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # --- PAGE 1: EXECUTIVE SUMMARY ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Informe de Situacion: ICTR {ictr_val:.2f}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Tendencia Detectada: {trend_val}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, "Cuadro de Mando - Analisis Detallado (España vs Vecinos)", ln=True)
    pdf.ln(2)
    
    # Header Table - More columns
    pdf.set_font("Arial", "B", 8)
    pdf.cell(45, 10, "Indicador", 1)
    pdf.cell(25, 10, "Valor", 1)
    pdf.cell(35, 10, "Evolucion", 1)
    pdf.cell(45, 10, "vs Vecinos (Rank)", 1)
    pdf.cell(40, 10, "Fecha", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=8)
    
    # Dictionary for labels/units mapping current indicators keys
    meta = {
        'Renta_PC': ('PIB Real pc', 'EUR (Real)'),
        'Gini': ('Desigualdad (Gini)', 'Indice (0-100)'),
        'AROPE': ('Riesgo Pobreza', '% Pob.'),
        'IPC': ('Coste Vida (IPC)', 'Base 100=2015'),
        'Vivienda': ('Precio Vivienda', 'Base 100=2015'),
        'Deuda_PC': ('Deuda Publica', '% PIB'),
        'Presion_Fiscal': ('Presion Fiscal', '% PIB'),
        'Paro': ('Tasa de Paro', '% Activos'),
        'NiNis': ('Jovenes Ni-Ni', '% 15-29a'),
        'Sentiment': ('Sentimiento Econ.', 'Base 100')
    }
    
    for name, df in indicators_dict.items():
        if name in meta and not df.empty:
            last_row = df.iloc[-1]
            val = last_row['value']
            date = str(last_row['date'].date()) if hasattr(last_row['date'], 'date') else str(last_row['date'])
            label, unit = meta[name]
            
            # 1. Calculo Evolucion (Ultimo vs Penultimo)
            evol_text = "-"
            if len(df) > 1:
                prev_val = df['value'].iloc[-2]
                diff = val - prev_val
                percent = (diff / prev_val * 100) if prev_val != 0 else 0
                arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
                
                # Logic of "Better/Worse" depends on indicator
                better = False
                if name in ['Renta_PC', 'Sentiment']:
                    better = diff > 0
                elif name in ['Gini', 'AROPE', 'IPC', 'Vivienda', 'Deuda_PC', 'Paro', 'NiNis']:
                    better = diff < 0
                
                status = "Mejora" if better else ("Empeora" if diff != 0 else "Estable")
                evol_text = f"{arrow} {percent:+.1f}% ({status})"

            # 2. Calculo vs Vecinos (Ranking)
            rank_text = "N/A"
            if peers_data:
                # Map indicators name to peers_data key
                peer_key = None
                if name == 'Renta_PC': peer_key = 'GDP'
                elif name == 'Paro': peer_key = 'Unemployment'
                elif name == 'Sentiment': peer_key = 'Sentiment'
                
                if peer_key and peer_key in peers_data:
                    current_values = {}
                    for ctry, c_df in peers_data[peer_key].items():
                        if not c_df.empty:
                            current_values[ctry] = c_df['value'].iloc[-1]
                    
                    if 'ES' in current_values:
                        # Sort values
                        sorted_ctrys = sorted(current_values.keys(), key=lambda x: current_values[x], 
                                              reverse=(peer_key in ['GDP', 'Sentiment']))
                        rank = sorted_ctrys.index('ES') + 1
                        total = len(sorted_ctrys)
                        
                        # Position description
                        pos_desc = "Lider" if rank == 1 else ("Cola" if rank == total else f"{rank}º de {total}")
                        rank_text = f"{pos_desc} (ES={val:.1f})"

            pdf.cell(45, 10, label, 1)
            pdf.cell(25, 10, f"{val:.1f} {unit[:5]}", 1) # Shorten unit
            pdf.cell(35, 10, evol_text, 1)
            pdf.cell(45, 10, rank_text, 1)
            pdf.cell(40, 10, date, 1)
            pdf.ln()

    # --- PAGE 2: METHODOLOGY & GLOSSARY ---
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Guia de Interpretacion y Metodologia", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, """
1. ICTR (Indicador Combinado de Tiempo Real):
   Es un indice sintetico (Media=100) calculado mediante Analisis de Componentes Principales (PCA).
   - Valor > 100: Crecimiento por encima de la tendencia historica.
   - Valor < 100: Enfriamiento economico.
   - Variacion (+/-): Indica si la situacion mejora o empeora respecto al periodo anterior.

2. Notas sobre los Indicadores Individuales:
   - Fechas Heterogeneas: Cada organismo (INE, Eurostat) publica con frecuencias distintas. El dashboard muestra siempre el ultimo dato disponible de cada fuente.
   - PIB (Producto Interior Bruto): Se muestra habitualmente como Indice de Volumen Encadenado para eliminar el efecto de los precios (inflacion) y medir la produccion real.
   - Deuda Publica: Expresada en porcentaje sobre el PIB trimestral (% GDP). Un valor de 105 significa que la deuda supera en un 5% a todo lo que produce el pais en un ano.
   - Sentimiento Economico (ESI): Es un indicador 'soft' basado en encuestas. Un valor de 100 es la media historica a largo plazo.

3. Fuentes de Datos:
   - Macro: INE (Contabilidad Nacional) y Eurostat.
   - Mercado Laboral: INE (EPA) y Eurostat (Desempleo armonizado).
   - Datos Alta Frecuencia: Red Electrica de Espana (ESIOS) para demanda de energia.
    """)
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 10, "Informe generado automaticamente por MBAI Native Dashboard.")

    # Save
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name