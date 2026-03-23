import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa BI - Sistema Integral", layout="wide", page_icon="📊")

# Estilos CSS Profesionales
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .metric-card { background-color: #ffffff; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA Y LIMPIEZA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo: B=1, C=2, E=4, F=5, G=6, H=7, AG=32, AH=33
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    
    meses_n = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    # Índices: Valores en 8, 10, 12... Alcances (%) en 9, 11, 13...
    idx_v = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    idx_p = [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    
    for i, mes in enumerate(meses_n):
        df[f"{mes}_v"] = pd.to_numeric(df.iloc[:, idx_v[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df[f"{mes}_%"] = pd.to_numeric(df.iloc[:, idx_p[i]].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)

    # Competencias (AM, AO, AQ, AS, AU, AW)
    comp_cols = ['CRM', 'Imagen', 'Autogestión', 'Habilidad', 'Técnica', 'Extra']
    idx_comp = [38, 40, 42, 44, 46, 48]
    for i, col in enumerate(comp_cols):
        df[col] = pd.to_numeric(df.iloc[:, idx_comp[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    df['Comp_Total_%'] = df[comp_cols].mean(axis=1).fillna(0) * 20 # Escala 1-5 a %
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    df['Iniciales'] = df['Vendedor'].apply(lambda x: "".join([n[0] for n in str(x).split() if n]).upper())
    
    # Blindaje de nulos para la Matriz
    df['Size_Marker'] = df['Total_Acumulado'].clip(lower=0.1).fillna(0.1)
    # Alcance Anual Total
    df['Total_%'] = (df['Total_Acumulado'] / (df['Objetivo_Mensual'] * 12).replace(0, 1)) * 100
    
    return df, meses_n, comp_cols[:5]

def get_ant(fecha):
    if pd.isnull(fecha): return "Dato N/A"
    diff = datetime(2025, 12, 31) - fecha
    a, m = diff.days // 365, (diff.days % 365) // 30
    return f"{a} años y {m} meses" if a > 0 else f"{m} meses"

try:
    df_raw, lista_meses, cols_comp = load_data()
    
    # --- MENÚ LATERAL ---
    dimension = st.sidebar.radio("MENÚ DE NAVEGACIÓN", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # ---------------------------------------------------------
    # DIMENSIÓN 1: PERFORMANCE COMERCIAL (RESTAURADA)
    # ---------------------------------------------------------
    if dimension == "Performance Comercial":
        st.markdown("### 📊 Performance Comercial Grupo Cenoa")
        
        # Filtros Superiores
        f1, f2, f3, f4 = st.columns([1, 2, 2, 1.5])
        with f1: st.selectbox("AÑO", ["2025"])
        with f2: f_emp = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique()))
        with f3: f_loc = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique()))
        
        df_p = df_raw.copy()
        if f_emp != "Todas": df_p = df_p[df_p['Empresa'] == f_emp]
        if f_loc != "Todas": df_p = df_p[df_p['Localidad'] == f_loc]
        with f4: st.metric("VENDEDORES", len(df_p))

        # Fila 1: Resumen General
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Cantidad de Operaciones por Empresa**")
            df_m = df_p.groupby('Empresa')[[f"{m}_v" for m in lista_meses]].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            df_m['Mes'] = df_m['Mes'].str.replace('_v', '')
            fig_g = px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f')
            fig_g.update_xaxes(categoryorder='array', categoryarray=lista_meses)
            st.plotly_chart(fig_g, use_container_width=True)
        with c2:
            st.markdown("**Top 10 Asesores**")
            st.plotly_chart(px.bar(df_p.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22']), use_container_width=True)

        st.divider()
        # Detalle Individual
        col_l, col_r = st.columns([1, 2.5])
        with col_l:
            v_sel = st.selectbox("Seleccionar Vendedor:", sorted(df_p['Vendedor'].unique()))
            v_data = df_p[df_p['Vendedor'] == v_sel].iloc[0]
        with col_r:
            d1, d2, d3 = st.columns([3, 1, 1])
            with d1:
                st.subheader(v_sel)
                st.markdown(f"<span style='color:#e67e22; font-weight:bold;'>{get_ant(v_data['Fecha_Ingreso'])}</span>", unsafe_allow_html=True)
                st.caption(f"{v_data['Canal']} | {v_data['Empresa']} | {v_data['Localidad']}")
            d2.metric("META", int(v_data['Objetivo_Mensual']))
            diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
            d3.metric("PROM", f"{v_data['Promedio']:.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")
            
            # Evolución Individual
            fig_i = go.Figure()
            fig_i.add_trace(go.Bar(x=lista_meses, y=[v_data[f"{m}_v"] for m in lista_meses], name="Ventas", text_auto='.0f', marker_color='#3498db'))
            fig_i.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', name="Objetivo", line=dict(color='red', dash='dot')))
            fig_i.update_layout(height=300, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses))
            st.plotly_chart(fig_i, use_container_width=True)

        # Gráficos Pie y Box
        st.divider()
        g1, g2 = st.columns(2)
        with g1: 
            st.markdown("**Desempeño por Localidad**")
            st.plotly_chart(px.pie(df_p, values='Total_Acumulado', names='Localidad', hole=0.5), use_container_width=True)
        with g2: 
            st.markdown("**Consistencia de Ventas (Box Plot)**")
            st.plotly_chart(px.box(df_p, x='Empresa', y='Promedio', points="all", color='Empresa', hover_data=['Vendedor']), use_container_width=True)

    # ---------------------------------------------------------
    # DIMENSIÓN 2: MATRIZ 9-BOX (INTERACTIVA Y FICHA)
    # ---------------------------------------------------------
    elif dimension == "Matriz 9-Box Comercial":
        st.markdown("### 🎯 Matriz de Talento 9-Box")
        
        m_f1, m_f2, m_f3 = st.columns(3)
        with m_f1: sel_periodo = st.selectbox("Periodo de Análisis:", ["Acumulado Anual"] + lista_meses)
        with m_f2: f_emp9 = st.selectbox("Empresa ", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique()))
        with m_f3: f_loc9 = st.selectbox("Localidad ", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique()))

        df_9 = df_raw.copy()
        if f_emp9 != "Todas": df_9 = df_9[df_9['Empresa'] == f_emp9]
        if f_loc9 != "Todas": df_9 = df_9[df_9['Localidad'] == f_loc9]
        
        # Eje X según periodo
        df_9['X_Axis'] = df_9['Total_%'] if sel_periodo == "Acumulado Anual" else df_9[f"{sel_periodo}_%"]
        
        # Gráfico con Iniciales - Blindado contra [NaN]
        fig_9 = px.scatter(
            df_9, x='X_Axis', y='Comp_Total_%', text='Iniciales', color='Empresa',
            size='Size_Marker', hover_name='Vendedor',
            range_x=[-5, 125], range_y=[-5, 105],
            labels={'X_Axis': f'% Alcance ({sel_periodo})', 'Comp_Total_%': '% Competencias'},
            height=600, template="plotly_white"
        )
        fig_9.update_traces(textposition='middle center', marker=dict(opacity=0.7))
        fig_9.add_vline(x=33.3, line_dash="dot", line_color="gray")
        fig_9.add_vline(x=66.6, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=33.3, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=66.6, line_dash="dot", line_color="gray")
        st.plotly_chart(fig_9, use_container_width=True)

        # SECCIÓN INTERACTIVA: FICHA TÉCNICA (Imágenes 73c0a8 / 73c0cd)
        st.divider()
        v_ficha_sel = st.selectbox("🔎 Seleccione un Asesor para ver su Ficha Técnica:", ["-- Seleccione --"] + sorted(df_9['Vendedor'].unique()))
        
        if v_ficha_sel != "-- Seleccione --":
            v_f = df_9[df_9['Vendedor'] == v_ficha_sel].iloc[0]
            
            # Cabecera Ficha
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f"<div class='metric-card'><h2>{v_f['X_Axis']:.1f}%</h2><p>PERFORMANCE ({sel_periodo})</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-card'><h2>{v_f['Comp_Total_%']:.1f}%</h2><p>COMPETENCIAS</p></div>", unsafe_allow_html=True)
            with k3:
                quad = "MIEMBRO CLAVE" if v_f['X_Axis'] > 66 and v_f['Comp_Total_%'] > 66 else "CORE PLAYER"
                st.markdown(f"<div class='metric-card'><h2>{quad}</h2><p>CUADRANTE</p></div>", unsafe_allow_html=True)

            # Detalle Gráfico
            gl, gr = st.columns([1, 1.5])
            with gl:
                st.markdown("**Desglose Competencias**")
                fig_c = px.bar(x=[v_f[c] for c in cols_comp], y=cols_comp, orientation='h', color=cols_comp, text_auto='.1f')
                st.plotly_chart(fig_c, use_container_width=True)
            with gr:
                st.markdown("**Evolución mensual % alcance objetivo**")
                fig_l = px.line(x=lista_meses, y=[v_f[f"{m}_%"] for m in lista_meses], markers=True, text_auto='.0f')
                fig_l.update_traces(line_color='#2ecc71', line_width=3)
                st.plotly_chart(fig_l, use_container_width=True)

except Exception as e:
    st.error(f"Falla crítica: {e}")
