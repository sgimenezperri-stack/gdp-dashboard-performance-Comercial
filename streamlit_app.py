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
    .analisis-box {
        background-color: #e8f4f8;
        padding: 20px;
        border-left: 5px solid #3498db;
        border-radius: 5px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Función para dar formato a la antigüedad (Columna C)
def format_antiguedad(fecha_ingreso):
    if pd.isnull(fecha_ingreso):
        return "Sin dato"
    hoy = datetime(2025, 12, 31)
    diff = hoy - fecha_ingreso
    anios = diff.days // 365
    meses = (diff.days % 365) // 30
    partes = []
    if anios > 0: partes.append(f"{anios} {'año' if anios == 1 else 'años'}")
    if meses > 0: partes.append(f"{meses} {'mes' if meses == 1 else 'meses'}")
    return " y ".join(partes) if partes else "Menos de un mes"

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo por Índice (B=1, C=2, E=4, F=5, G=6, H=7, AG=32, AH=33)
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    # Meses saltados (I, K, M, O, Q, S, U, W, Y, AA, AC, AE)
    indices_meses = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    for i, idx in enumerate(indices_meses):
        df[nombres_meses[i]] = pd.to_numeric(df.iloc[:, idx].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df = df.rename(columns=mapping)
    for c in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    
    # Limpieza: eliminar filas donde el Vendedor sea "Vendedor" o similar (encabezados repetidos)
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    return df, nombres_meses

try:
    df_raw, lista_meses = load_data()

    # --- 1. FILTROS SUPERIORES ---
    st.markdown("### 📊 Performance Comercial Grupo Cenoa")
    f_col1, f_col2, f_col3, f_col4 = st.columns([1, 2, 2, 1.5])
    
    with f_col1: st.selectbox("AÑO", ["2025"])
    with f_col2:
        op_emp = [x for x in sorted(df_raw['Empresa'].dropna().unique().tolist()) if str(x).upper() != "EMPRESA"]
        f_empresa = st.selectbox("EMPRESA", ["Todas"] + op_emp)
    with f_col3:
        op_loc = [x for x in sorted(df_raw['Localidad'].dropna().unique().tolist()) if str(x).upper() != "LOCALIDAD"]
        f_localidad = st.selectbox("LOCALIDAD", ["Todas"] + op_loc)

    df_filtered = df_raw.copy()
    if f_empresa != "Todas": df_filtered = df_filtered[df_filtered['Empresa'] == f_empresa]
    if f_localidad != "Todas": df_filtered = df_filtered[df_filtered['Localidad'] == f_localidad]

    with f_col4: st.metric("VENDEDORES", len(df_filtered))

    # --- 2. FILA DE GRÁFICOS GENERALES ---
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("**Cantidad de Operaciones por Empresa (Acumulado)**")
        df_melt = df_filtered.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
        fig_emp = px.bar(df_melt, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_emp.update_xaxes(categoryorder='array', categoryarray=lista_meses)
        st.plotly_chart(fig_emp, use_container_width=True)

    with c2:
        st.markdown("**Top 10 Vendedores (Operaciones)**")
        top_10 = df_filtered.nlargest(10, 'Total_Acumulado')
        fig_top = px.bar(top_10, x='Total_Acumulado', y='Vendedor', orientation='h', text='Total_Acumulado', color_discrete_sequence=['#e67e22'])
        fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_top, use_container_width=True)

    # --- 3. ANÁLISIS INDIVIDUAL ---
    st.divider()
    col_list, col_chart = st.columns([1, 2.5])
    with col_list:
        vendedor_sel = st.selectbox("Seleccionar Vendedor:", sorted(df_filtered['Vendedor'].unique()))
        v_data = df_filtered[df_filtered['Vendedor'] == vendedor_sel].iloc[0]
    
    with col_chart:
        d_cab, d_obj, d_prom = st.columns([2.5, 1, 1])
        with d_cab:
            st.subheader(vendedor_sel)
            st.markdown(f"🗓️ **Antigüedad:** <span style='color:#e67e22; font-size:20px; font-weight:bold;'>{format_antiguedad(v_data['Fecha_Ingreso'])}</span>", unsafe_allow_html=True)
            st.write(f"Canal: {v_data['Canal']} | Empresa: {v_data['Empresa']} | Localidad: {v_data['Localidad']}")
        
        diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
        d_obj.metric("META MENSUAL", f"{v_data['Objetivo_Mensual']:,.0f}")
        d_prom.metric("PROMEDIO REAL", f"{v_data['Promedio']:,.1f}", delta=f"{diff:.1f} vs Meta", delta_color="normal" if diff >= 0 else "inverse")

        # Evolución Mensual
        vals_v = [v_data[m] for m in lista_meses]
        fig_ind = go.Figure()
        fig_ind.add_trace(go.Bar(x=lista_meses, y=vals_v, name="Ventas", marker_color='#3498db', text=vals_v, textposition='auto', texttemplate='%{text:,.0f}'))
        fig_ind.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', name="Objetivo", line=dict(color='red', width=3, dash='dot')))
        fig_ind.update_layout(height=350, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses))
        st.plotly_chart(fig_ind, use_container_width=True)

    # --- 4. GRÁFICOS COMPLEMENTARIOS Y ANÁLISIS VIRTUAL ---
    st.divider()
    pie_col, box_col = st.columns(2)
    with pie_col:
        st.markdown("**Participación por Localidad**")
        st.plotly_chart(px.pie(df_filtered, values='Total_Acumulado', names='Localidad', hole=0.5), use_container_width=True)
    
    with box_col:
        st.markdown("**Consistencia de Ventas (Promedio Mensual)**")
        # MEJORA: Identificación de puntos con nombre y promedio
        fig_box = px.box(
            df_filtered, 
            x='Empresa', 
            y='Promedio', 
            points="all", 
            color='Empresa',
            hover_data={'Vendedor': True, 'Promedio': ':.2f', 'Empresa': False} # Muestra Nombre y Promedio al pasar el cursor
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
        # BLOQUE DE ANÁLISIS VIRTUAL
        st.markdown("""
        <div class="analisis-box">
            <strong>🧠 Análisis Virtual de Consistencia:</strong><br>
            • <b>Dispersión:</b> Las cajas más anchas indican una brecha mayor entre sus vendedores estrella y el resto del equipo.<br>
            • <b>Outliers (Puntos Aislados):</b> Son tus asesores de alto rendimiento que superan la media del grupo.<br>
            • <b>Interpretación:</b> Busca reducir la caja (estandarizar procesos) y subir la línea media (mejorar el rendimiento general).
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en la estructura del Dashboard: {e}")
