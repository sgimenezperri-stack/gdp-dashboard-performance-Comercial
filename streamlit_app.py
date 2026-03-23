import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Performance Comercial Grupo Cenoa", layout="wide", page_icon="🚗")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { 
        background-color: #ffffff; 
        border-radius: 10px; 
        padding: 15px; 
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    
    # 1. Mapeo por Índice (B=1, D=3, E=4, F=5, G=6, H=7, AG=32, AH=33)
    mapping = {
        df.columns[1]: 'Vendedor', 
        df.columns[3]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', 
        df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', 
        df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', 
        df.columns[33]: 'Promedio'
    }
    
    # 2. Meses Saltados (I=8, K=10, M=12, O=14, Q=16, S=18, U=20, W=22, Y=24, AA=26, AC=28, AE=30)
    indices_meses = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for i, idx in enumerate(indices_meses):
        col_name = df.columns[idx]
        df[nombres_meses[i]] = pd.to_numeric(df[col_name].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df = df.rename(columns=mapping)
    
    # Limpieza de valores clave
    for c in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # Convertir Fecha_Ingreso a formato fecha (Columna D)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], errors='coerce')
    
    return df, nombres_meses

try:
    df_raw, lista_meses = load_data()

    # --- 1. FILTROS SUPERIORES ---
    st.markdown("### 📊 Performance Comercial Grupo Cenoa")
    f_col1, f_col2, f_col3, f_col4 = st.columns([1, 2, 2, 1.5])
    
    with f_col1:
        st.selectbox("AÑO", ["2025"])
    with f_col2:
        f_empresa = st.selectbox("EMPRESA", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique().tolist()))
    with f_col3:
        f_localidad = st.selectbox("LOCALIDAD", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique().tolist()))

    # --- APLICAR FILTROS ANTES DE MOSTRAR LA DOTACIÓN ---
    df_filtered = df_raw.copy()
    if f_empresa != "Todas":
        df_filtered = df_filtered[df_filtered['Empresa'] == f_empresa]
    if f_localidad != "Todas":
        df_filtered = df_filtered[df_filtered['Localidad'] == f_localidad]

    with f_col4:
        # PUNTO 1: Dotación dinámica según filtros aplicados
        st.metric("VENDEDORES", len(df_filtered))

    # --- 2. FILA DE GRÁFICOS GENERALES ---
    c1, c2 = st.columns([1.5, 1])

    with c1:
        st.markdown("**Cantidad de Operaciones por Empresa (Acumulado)**")
        df_melt = df_filtered.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
        fig_emp = px.bar(df_melt, x='Mes', y='Ventas', color='Empresa', barmode='group', 
                         text_auto='.0f', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_emp.update_xaxes(categoryorder='array', categoryarray=lista_meses)
        fig_emp.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig_emp, use_container_width=True)

    with c2:
        st.markdown("**Top 10 Vendedores (Operaciones)**")
        top_10 = df_filtered.nlargest(10, 'Total_Acumulado')
        fig_top = px.bar(top_10, x='Total_Acumulado', y='Vendedor', orientation='h', 
                         text='Total_Acumulado', color_discrete_sequence=['#e67e22'])
        fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_top.update_layout(height=300, margin=dict(t=10, b=10), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

    # --- 3. ANÁLISIS INDIVIDUAL ---
    st.divider()
    col_list, col_chart = st.columns([1, 2.5])

    with col_list:
        # Selección de vendedor dentro de los filtrados
        vendedor_sel = st.selectbox("Seleccionar Vendedor:", sorted(df_filtered['Vendedor'].unique()))
        v_data = df_filtered[df_filtered['Vendedor'] == vendedor_sel].iloc[0]
        st.info(f"Ventas Acumuladas: {v_data['Total_Acumulado']:,.0f}")

    with col_chart:
        # Cabecera individual
        d_cab, d_obj, d_prom = st.columns([2.5, 1, 1])
        with d_cab:
            st.subheader(vendedor_sel)
            
            # PUNTO 2: Mostrar antigüedad basada en Columna D
            if pd.notnull(v_data['Fecha_Ingreso']):
                fecha_ref = datetime(2025, 12, 31) # Referencia cierre 2025
                ant = fecha_ref - v_data['Fecha_Ingreso']
                anios = ant.days // 365
                meses_ant = (ant.days % 365) // 30
                st.markdown(f"🗓️ **Antigüedad:** <span style='color:#e67e22; font-weight:bold;'>{anios} Años {meses_ant} Meses</span>", unsafe_allow_html=True)
            else:
                st.caption("Fecha de ingreso no disponible")
            
            st.write(f"Canal: {v_data['Canal']} | Empresa: {v_data['Empresa']} | Localidad: {v_data['Localidad']}")

        # Semáforo
        diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
        with d_obj:
            st.metric("META MENSUAL", f"{v_data['Objetivo_Mensual']:,.0f}")
        with d_prom:
            st.metric("PROMEDIO REAL", f"{v_data['Promedio']:,.1f}", delta=f"{diff:.1f} vs Meta", delta_color="normal" if diff >= 0 else "inverse")

        # Gráfico Mensual (Corregido para mostrar todos los meses I-K-M...)
        vals_vendedor = [v_data[m] for m in lista_meses]
        fig_ind = go.Figure()
        fig_ind.add_trace(go.Bar(x=lista_meses, y=vals_vendedor, name="Ventas", marker_color='#3498db',
                                 text=vals_vendedor, textposition='auto', texttemplate='%{text:,.0f}'))
        fig_ind.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', 
                                      name="Objetivo", line=dict(color='red', width=3, dash='dot')))
        
        # Forzar visualización de los 12 meses aunque estén vacíos
        fig_ind.update_layout(height=350, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses))
        st.plotly_chart(fig_ind, use_container_width=True)

    # --- 4. GRÁFICOS COMPLEMENTARIOS ---
    st.divider()
    pie_col, box_col = st.columns(2)
    with pie_col:
        st.markdown("**Participación por Localidad**")
        st.plotly_chart(px.pie(df_filtered, values='Total_Acumulado', names='Localidad', hole=0.5), use_container_width=True)
    with box_col:
        st.markdown("**Consistencia de Ventas (Promedio Mensual)**")
        st.plotly_chart(px.box(df_filtered, x='Empresa', y='Promedio', points="all", color='Empresa'), use_container_width=True)

except Exception as e:
    st.error(f"Error en la estructura del Dashboard: {e}")
