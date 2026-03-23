import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa BI - Talento & Performance", layout="wide", page_icon="📊")

# Estilos CSS - Estética de "Miembro Clave" y Tarjetas
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .metric-card { background-color: #ffffff; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .header-vendedor { background-color: #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-bottom: 4px solid #e67e22; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    # Resultados (J, L, N...): 9, 11, 13... y Alcance % (K, M, O...): 10, 12, 14...
    meses_n = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    idx_ventas = [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    idx_alcance = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32] # Columnas de % alcance
    
    for i, mes in enumerate(meses_n):
        df[f"{mes}_v"] = pd.to_numeric(df.iloc[:, idx_ventas[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df[f"{mes}_%"] = pd.to_numeric(df.iloc[:, idx_alcance[i]].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)

    # Competencias Detalladas (AM, AO, AQ, AS, AU)
    comp_labels = ['CRM', 'Imagen', 'Autogestión', 'Habilidad', 'Técnica']
    idx_comp = [38, 40, 42, 44, 46]
    for i, label in enumerate(comp_labels):
        df[label] = pd.to_numeric(df.iloc[:, idx_comp[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    df['Comp_Total_%'] = df[comp_labels].mean(axis=1).fillna(0) * 20 # Convertir escala 1-5 a %
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    df['Iniciales'] = df['Vendedor'].apply(lambda x: "".join([n[0] for n in str(x).split() if n]).upper())
    
    # Limpieza final para evitar el error de Matriz
    df['Size_Marker'] = df['Total_Acumulado'].clip(lower=0.1).fillna(0.1)
    
    return df, meses_n, comp_labels

def get_ant(fecha):
    if pd.isnull(fecha): return "Dato N/A"
    hoy = datetime(2025, 12, 31)
    diff = hoy - fecha
    a, m = diff.days // 365, (diff.days % 365) // 30
    return f"{a} años y {m} meses" if a > 0 else f"{m} meses"

try:
    df_raw, lista_meses, comp_labels = load_data()
    dimension = st.sidebar.radio("MENÚ DE NAVEGACIÓN", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # =========================================================
    # DIMENSIÓN: PERFORMANCE COMERCIAL (BLINDADA)
    # =========================================================
    if dimension == "Performance Comercial":
        st.markdown("### 📊 Performance Comercial Grupo Cenoa")
        f1, f2, f3, f4 = st.columns([1, 2, 2, 1.5])
        with f1: st.selectbox("AÑO", ["2025"])
        with f2: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique()))
        with f3: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique()))
        
        df_p = df_raw.copy()
        if f_emp != "Todas": df_p = df_p[df_p['Empresa'] == f_emp]
        if f_loc != "Todas": df_p = df_p[df_p['Localidad'] == f_loc]
        with f4: st.metric("VENDEDORES", len(df_p))

        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Evolución Mensual (Operaciones)**")
            df_m = df_p.groupby('Empresa')[[f"{m}_v" for m in lista_meses]].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            df_m['Mes'] = df_m['Mes'].str.replace('_v', '')
            fig_g = px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f').update_xaxes(categoryorder='array', categoryarray=lista_meses)
            st.plotly_chart(fig_g, use_container_width=True)
        with c2:
            st.markdown("**Top 10 Asesores**")
            st.plotly_chart(px.bar(df_p.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22']), use_container_width=True)

        st.divider()
        v_sel = st.selectbox("Seleccionar Vendedor para Detalle:", sorted(df_p['Vendedor'].unique()))
        v_data = df_p[df_p['Vendedor'] == v_sel].iloc[0]
        
        # Tarjeta Individual (como la imagen solicitada)
        det1, det2, det3 = st.columns([3, 1, 1])
        with det1:
            st.subheader(v_sel)
            st.markdown(f"<span style='color:#e67e22; font-weight:bold;'>{get_ant(v_data['Fecha_Ingreso'])}</span>", unsafe_allow_html=True)
            st.caption(f"{v_data['Canal']} | {v_data['Empresa']} | {v_data['Localidad']}")
        det2.metric("META", int(v_data['Objetivo_Mensual']))
        diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
        det3.metric("PROM", f"{v_data['Promedio']:.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")
        
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Bar(x=lista_meses, y=[v_data[f"{m}_v"] for m in lista_meses], name="Ventas", text_auto='.0f'))
        fig_evol.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', name="Objetivo", line=dict(color='red', dash='dot')))
        st.plotly_chart(fig_evol.update_layout(height=300, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses)), use_container_width=True)

    # =========================================================
    # DIMENSIÓN: MATRIZ 9-BOX (INTERACTIVA AL CLICK)
    # =========================================================
    elif dimension == "Matriz 9-Box Comercial":
        st.markdown("### 🎯 Matriz de Talento 9-Box")
        
        m_f1, m_f2, m_f3 = st.columns(3)
        with m_f1: sel_mes = st.selectbox("Analizar Resultado por Mes:", lista_meses)
        with m_f2: f_emp9 = st.selectbox("Empresa ", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique()))
        with m_f3: f_loc9 = st.selectbox("Localidad ", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique()))

        df_9 = df_raw.copy()
        if f_emp9 != "Todas": df_9 = df_9[df_9['Empresa'] == f_emp9]
        if f_loc9 != "Todas": df_9 = df_9[df_9['Localidad'] == f_loc9]
        
        # Eje X: % Alcance del mes seleccionado
        df_9['X_Axis'] = df_9[f"{sel_mes}_%"]
        
        # Gráfico 9-Box con Iniciales
        fig_9 = px.scatter(
            df_9, x='X_Axis', y='Comp_Total_%', text='Iniciales', color='Empresa',
            size='Size_Marker', hover_name='Vendedor',
            range_x=[0, 130], range_y=[0, 105],
            labels={'X_Axis': f'% Alcance {sel_mes}', 'Comp_Total_%': '% Competencias'},
            height=600, template="plotly_white"
        )
        fig_9.update_traces(textposition='middle center', marker=dict(opacity=0.7))
        fig_9.add_vline(x=33.3, line_dash="dot", line_color="gray")
        fig_9.add_vline(x=66.6, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=33.3, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=66.6, line_dash="dot", line_color="gray")
        
        # Selección del Vendedor al Click (Simulada por Selectbox para estabilidad)
        v_click = st.selectbox("🔎 Ver Ficha Detallada del Asesor:", ["Seleccione un vendedor..."] + sorted(df_9['Vendedor'].unique()))
        
        st.plotly_chart(fig_9, use_container_width=True)

        if v_click != "Seleccione un vendedor...":
            v_ficha = df_9[df_9['Vendedor'] == v_click].iloc[0]
            
            # --- DISEÑO DE FICHA DETALLADA (Imagen 73c0a8) ---
            st.divider()
            st.markdown(f"### Ficha de Desempeño: {v_click}")
            
            # Encabezado 3 Tarjetas
            kpi_a, kpi_b, kpi_c = st.columns(3)
            with kpi_a:
                st.markdown(f"<div class='metric-card'><h2>{v_ficha[f'{sel_mes}_%']:.1f}%</h2><p>PERFORMANCE ({sel_mes})</p></div>", unsafe_allow_html=True)
            with kpi_b:
                st.markdown(f"<div class='metric-card'><h2>{v_ficha['Comp_Total_%']:.1f}%</h2><p>COMPETENCIAS</p></div>", unsafe_allow_html=True)
            with kpi_c:
                # Lógica de Cuadrante
                quad = "MIEMBRO CLAVE" if v_ficha['X_Axis'] > 66 and v_ficha['Comp_Total_%'] > 66 else "POR DESARROLLAR"
                st.markdown(f"<div class='metric-card'><h2>{quad}</h2><p>CUADRANTE</p></div>", unsafe_allow_html=True)

            # Gráficos Desglose (Imagen 73c0cd)
            g_left, g_right = st.columns([1, 1.5])
            
            with g_left:
                st.markdown("**Desglose Competencias**")
                scores = [v_ficha[c] for c in comp_labels]
                fig_comp = px.bar(x=scores, y=comp_labels, orientation='h', text=[f"{s*20}%" for s in scores], color=scores, color_continuous_scale='Blues')
                fig_comp.update_layout(showlegend=False, height=350, margin=dict(t=10, b=10))
                st.plotly_chart(fig_comp, use_container_width=True)
            
            with g_right:
                st.markdown("**Evolución mensual % alcance objetivo de ventas**")
                evol_data = [v_ficha[f"{m}_%"] for m in lista_meses]
                fig_line = px.line(x=lista_meses, y=evol_data, markers=True, text=[f"{val:.0f}%" for val in evol_data])
                fig_line.update_traces(line_color='#2ecc71', line_width=3, marker_size=10)
                fig_line.update_layout(height=350, yaxis_range=[0, max(evol_data)+20], margin=dict(t=10))
                st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error(f"Error de sistema: {e}")
