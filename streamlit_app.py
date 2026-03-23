import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa Analytics 2025", layout="wide", page_icon="🚗")

# Estilos CSS para el Semáforo y la Estética
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetric"] { 
        background-color: #ffffff; 
        border: 1px solid #e0e0e0; 
        padding: 15px; 
        border-radius: 12px; 
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    .vendedor-header { background-color: #ffffff; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo según estructura (B, D, E, F, G, H, AG, AH)
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[3]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    df = df.rename(columns=mapping)
    
    # Meses (Índices 8 a 19 del Sheets)
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    for i, mes in enumerate(meses):
        df[mes] = pd.to_numeric(df.iloc[:, 8+i].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # Limpieza numérica
    for c in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], errors='coerce')
    return df, meses

try:
    df_raw, lista_meses = load_data()

    # --- 1. FILTROS SUPERIORES (Diseño Horizontal) ---
    st.markdown("### 📊 Panel de Control Comercial 2025")
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 2, 2, 1.5])
    
    with f_col1:
        f_empresa = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique().tolist()))
    with f_col2:
        f_localidad = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique().tolist()))
    with f_col3:
        vendedor_sel = st.selectbox("BUSCAR VENDEDOR", sorted(df_raw['Vendedor'].unique()))
    with f_col4:
        dotacion_f = len(df_raw[df_raw['Empresa'] == f_empresa]) if f_empresa != "Todas" else len(df_raw)
        st.write(f"📈 **Dotación: {dotacion_f}**")
        st.caption("Cierre Ciclo 2025")

    # Aplicar filtros
    df = df_raw.copy()
    if f_empresa != "Todas": df = df[df['Empresa'] == f_empresa]
    if f_localidad != "Todas": df = df[df['Localidad'] == f_localidad]

    # --- 2. FILA DE GRÁFICOS ACUMULADOS CON ETIQUETAS ---
    c_main_1, c_main_2 = st.columns([1.5, 1])

    with c_main_1:
        st.markdown("**Ventas por Empresa (Evolución Mensual)**")
        df_melt = df.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
        fig_emp = px.bar(df_melt, x='Mes', y='Ventas', color='Empresa', barmode='group', 
                         text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_emp.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig_emp, use_container_width=True)

    with c_main_2:
        st.markdown("**Top 10 Vendedores (Ventas Totales)**")
        top_10 = df.nlargest(10, 'Total_Acumulado')
        fig_top = px.bar(top_10, x='Total_Acumulado', y='Vendedor', orientation='h', 
                         text='Total_Acumulado', color_discrete_sequence=['#2ecc71'])
        fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_top.update_layout(height=300, margin=dict(t=10, b=10), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

    # --- 3. ANÁLISIS INDIVIDUAL ---
    st.divider()
    v_data = df_raw[df_raw['Vendedor'] == vendedor_sel].iloc[0]
    
    with st.container():
        d1, d2, d3 = st.columns([2.5, 1, 1])
        
        with d1:
            st.title(vendedor_sel)
            if pd.notnull(v_data['Fecha_Ingreso']):
                hoy = datetime(2025, 12, 31)
                ant = hoy - v_data['Fecha_Ingreso']
                st.markdown(f"🗓️ **Antigüedad:** {ant.days // 365} años y {(ant.days % 365) // 30} meses")
            st.write(f"🏢 **Empresa:** {v_data['Empresa']} | 📍 **Localidad:** {v_data['Localidad']} | 🛣️ **Canal:** {v_data['Canal']}")

        # Semáforo
        dif_objetivo = v_data['Promedio'] - v_data['Objetivo_Mensual']
        color_semaforo = "normal" if dif_objetivo >= 0 else "inverse"
        
        with d2:
            st.metric("META MENSUAL", f"{v_data['Objetivo_Mensual']:,.0f}")
        with d3:
            st.metric(
                label="PROMEDIO REAL", 
                value=f"{v_data['Promedio']:,.1f}", 
                delta=f"{dif_objetivo:,.1f} vs Meta",
                delta_color=color_semaforo
            )

        # Gráfico Mensual con Etiquetas y Target
        ventas_v = v_data[lista_meses].values
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Bar(
            x=lista_meses, 
            y=ventas_v, 
            name="Ventas", 
            marker_color='#3498db',
            text=ventas_v,
            textposition='auto',
            texttemplate='%{text:,.0f}'
        ))
        fig_evol.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', 
                                      name="Target Mensual", line=dict(color='red', width=3, dash='dot')))
        fig_evol.update_layout(height=350, margin=dict(t=30), legend=dict(orientation="h", y=1.1, x=1, xanchor='right'))
        st.plotly_chart(fig_evol, use_container_width=True)

    # --- 4. GRÁFICOS COMPLEMENTARIOS ---
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        st.markdown("**Participación por Localidad**")
        fig_pie = px.pie(df, values='Total_Acumulado', names='Localidad', hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g2:
        st.markdown("**Consistencia de Ventas (Promedio Mensual)**")
        fig_box = px.box(df, x='Empresa', y='Promedio', points="all", color='Empresa')
        st.plotly_chart(fig_box, use_container_width=True)

except Exception as e:
    st.error(f"Error cargando el dashboard: {e}")
