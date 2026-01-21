from fpdf import FPDF
import pandas as pd
import tempfile
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

class EconomicReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Monitor Economico MBAI Native', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_chart_image(df, title, kind='line', color='blue', trend=None, peers_dict=None):
    """Genera un archivo temporal PNG con el grafico."""
    plt.figure(figsize=(10, 5))
    
    if peers_dict:
        # Modo Comparativa
        for ctry, c_df in peers_dict.items():
            if not c_df.empty:
                width = 3 if ctry == 'ES' else 1
                alpha = 1.0 if ctry == 'ES' else 0.5
                lbl = ctry
                
                # Normalizar si es GDP
                y_vals = c_df['value']
                if "Crecimiento" in title:
                    start_val = y_vals.iloc[0]
                    y_vals = (y_vals / start_val) * 100
                    
                plt.plot(c_df['date'], y_vals, label=lbl, linewidth=width, alpha=alpha)
        plt.legend()
    
    elif trend is not None:
        # Modo ESIOS (Dual)
        plt.plot(df.index, df['value'], color='skyblue', label='Diario/Mensual', alpha=0.5, linewidth=2, marker='.', markersize=5)
        plt.plot(df.index, trend, color='red', label='Tendencia (Anual)', linewidth=3)
        plt.legend()
        
    else:
        # Modo Simple
        plt.plot(df['date'], df['value'], color=color, linewidth=2, marker='o', markersize=3)
        
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(tmp.name, bbox_inches='tight', dpi=100)
    finally:
        plt.close() # Important to close plot to free memory
        
    return tmp.name

def build_pdf_report(ictr_val, trend_val, indicators_dict, peers_data=None, ai_analysis=None, esios_data=None):
    pdf = EconomicReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # --- PAGE 1: DASHBOARD SUMMARY ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Informe de Situacion: ICTR {ictr_val:.2f}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Tendencia Detectada: {trend_val}", ln=True)
    pdf.ln(5)
    
    # Table (Condensed)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "Indicadores Clave", ln=True)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(50, 8, "Indicador", 1)
    pdf.cell(30, 8, "Valor", 1)
    pdf.cell(40, 8, "Fecha", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=8)
    meta = {
        'Renta_PC': 'PIB Real pc', 'Gini': 'Desigualdad', 'AROPE': 'Riesgo Pobreza',
        'IPC': 'IPC Coste Vida', 'Paro': 'Tasa Paro', 'Deuda_PC': 'Deuda Pub (% PIB)',
        'Vivienda': 'Precio Vivienda', 'Presion_Fiscal': 'Presion Fiscal', 'NiNis': 'Tasa Ni-Nis'
    }
    
    for name, lbl in meta.items():
        if name in indicators_dict and not indicators_dict[name].empty:
            row = indicators_dict[name].iloc[-1]
            pdf.cell(50, 8, lbl, 1)
            pdf.cell(30, 8, f"{row['value']:.1f}", 1)
            d_val = row['date']
            d_str = str(d_val.date()) if hasattr(d_val, 'date') else str(d_val)[:10]
            pdf.cell(40, 8, d_str, 1)
            pdf.ln()
            
    pdf.ln(5)

    # --- CHARTS SECTION (EXPANDED) ---
    
    # A. ESIOS CHART (High Priority)
    if esios_data is not None and not esios_data.empty:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Demanda Electrica (Indicador Adelantado)", ln=True)
        trend_series = esios_data['Trend_365'] if 'Trend_365' in esios_data else None
        img_path = create_chart_image(esios_data, "Consumo Electrico vs Tendencia", trend=trend_series)
        pdf.image(img_path, w=170)
        os.unlink(img_path)
    
    # B. COMPARISON CHARTS
    if peers_data:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "1. Comparativa Internacional", ln=True)
        
        # GDP
        if 'GDP' in peers_data:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 8, "Crecimiento Acumulado (Base 100)", ln=True)
            img_gdp = create_chart_image(None, "Crecimiento PIB (Base 100)", peers_dict=peers_data['GDP'])
            pdf.image(img_gdp, w=170)
            os.unlink(img_gdp)
            
        # Unemployment
        if 'Unemployment' in peers_data:
            pdf.ln(5)
            pdf.cell(0, 8, "Tasa de Paro (%)", ln=True)
            img_un = create_chart_image(None, "Tasa de Desempleo Comparison", peers_dict=peers_data['Unemployment'])
            pdf.image(img_un, w=170)
            os.unlink(img_un)

    # C. INDIVIDAL INDICATORS CHARTS (Categorized)
    
    # Page: Bienestar & Sociedad
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Bienestar y Sociedad", ln=True)
    
    # Layout: 2 charts per page logic roughly
    
    if 'Gini' in indicators_dict and not indicators_dict['Gini'].empty:
        pdf.ln(2)
        img = create_chart_image(indicators_dict['Gini'], "Desigualdad (Indice Gini)", color='purple')
        pdf.image(img, w=160, h=80)
        os.unlink(img)
        
    if 'AROPE' in indicators_dict and not indicators_dict['AROPE'].empty:
        pdf.ln(5)
        img = create_chart_image(indicators_dict['AROPE'], "Riesgo de Pobreza (% Poblacion)", color='orange')
        pdf.image(img, w=160, h=80)
        os.unlink(img)
        
    # Page: Economía Doméstica
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "3. Economia Domestica", ln=True)
    
    if 'IPC' in indicators_dict and not indicators_dict['IPC'].empty:
        pdf.ln(2)
        img = create_chart_image(indicators_dict['IPC'], "Indice de Precios (IPC)", color='red')
        pdf.image(img, w=160, h=80)
        os.unlink(img)

    if 'Vivienda' in indicators_dict and not indicators_dict['Vivienda'].empty:
        pdf.ln(5)
        img = create_chart_image(indicators_dict['Vivienda'], "Precio Vivienda (Indice)", color='brown')
        pdf.image(img, w=160, h=80)
        os.unlink(img)
        
    # Page: Fiscalidad y Deuda
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "4. Deuda y Fiscalidad", ln=True)
    
    if 'Deuda_PC' in indicators_dict and not indicators_dict['Deuda_PC'].empty:
        pdf.ln(2)
        img = create_chart_image(indicators_dict['Deuda_PC'], "Deuda Publica (% PIB)", color='black')
        pdf.image(img, w=160, h=80)
        os.unlink(img)
        
    if 'Presion_Fiscal' in indicators_dict and not indicators_dict['Presion_Fiscal'].empty:
        pdf.ln(5)
        img = create_chart_image(indicators_dict['Presion_Fiscal'], "Presion Fiscal (% PIB)", color='grey')
        pdf.image(img, w=160, h=80)
        os.unlink(img)

    # --- AI ANALYSIS ---
    if ai_analysis and len(ai_analysis) > 10:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Analisis Inteligente (Gemini)", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        sanitized_ai = ai_analysis.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, sanitized_ai)

    # Save
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name