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

def create_pdf_report(ictr_val, trend_val, indicators_dict):
    pdf = EconomicReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # --- PAGE 1: EXECUTIVE SUMMARY ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Informe de Situacion: ICTR {ictr_val:.2f}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Tendencia Detectada: {trend_val}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Cuadro de Mando - Ultimos Datos Registrados", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    # Header Table
    pdf.cell(70, 10, "Indicador", 1)
    pdf.cell(30, 10, "Valor", 1)
    pdf.cell(50, 10, "Unidad / Ref", 1)
    pdf.cell(40, 10, "Fecha", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    
    # Dictionary for labels/units
    meta = {
        'GDP': ('PIB (Volumen)', 'Indice 2020=100'),
        'IPC': ('Inflacion (IPC)', 'Indice 2021=100'),
        'Debt': ('Deuda Publica', '% del PIB'),
        'Unemployment': ('Tasa de Paro', '% Activos'),
        'Youth_Unemp': ('Paro Juvenil', '% Activos <25'),
        'Hours_Worked': ('Horas Trabajadas', 'Indice'),
        'AROPE': ('Tasa AROPE', '% Poblacion'),
        'Foreclosures': ('Ejecuciones Hipot.', 'Total Trimestral'),
        'Electricity': ('Demanda Elec.', 'MWh / Indice'),
        'Sentiment': ('Sentimiento Econ.', 'Balance (+/-)'),
        'Mercantiles': ('Creacion Empresas', 'Total Mensual')
    }
    
    for name, df in indicators_dict.items():
        if not df.empty:
            last_row = df.iloc[-1]
            val = last_row['value']
            date = str(last_row['date'].date()) if hasattr(last_row['date'], 'date') else str(last_row['date'])
            
            label, unit = meta.get(name, (name, '-'))
            
            pdf.cell(70, 10, label, 1)
            pdf.cell(30, 10, f"{val:.2f}", 1)
            pdf.cell(50, 10, unit, 1)
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