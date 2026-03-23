import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa BI - Performance & Talento", layout="wide", page_icon="📊")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo Básico
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    
    # 1. Extracción de Resultados/Ventas (J, L, N, P, R, T, V, X, Z, AB, AD, AF -> Índices 9 a 31 saltados)
    idx_resultados = [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    for i, idx in enumerate(idx_resultados):
        df[nombres_meses[i]] = pd.to_numeric(df.iloc[:, idx].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # 2. Extracción de Competencias (AM, AO, AQ, AS, AU, AW -> Índices 38, 40, 42, 44, 46, 48)
    idx_competencias = [38, 40, 42, 44, 46, 48]
    # Calculamos el promedio de las competencias y lo pasamos a % (Asumiendo escala 1-5, si es otra escala ajustar el /5)
    df['Score_Competencias'] = df.iloc[:, idx_competencias].apply(pd.to_numeric, errors='coerce').mean(axis=1).fillna(0)
    df['Competencias_Porc'] = (df['Score_Competencias'] / 5) * 100 # Normalización a %
    
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    return df, nombres_meses

try:
    df_raw, lista_meses = load_data()

    # --- MENU LATERAL IZQUIERDO ---
    st.sidebar.title("Navegación")
    dimension = st.sidebar.radio("Seleccione Dimensión:", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # ---------------------------------------------------------
    # PANEL: PERFORMANCE COMERCIAL
    # ---------------------------------------------------------
    if dimension == "Performance Comercial":
        st.title("📊 Performance Comercial")
        
        # Filtros Superiores
        f1, f2, f3 = st.columns(3)
        with f1: f_emp = st.selectbox("Empresa", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique().tolist()))
        with f2: f_loc = st.selectbox("Localidad", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique().tolist()))
        
        df_f = df_raw.copy()
        if f_emp != "Todas": df_f = df_f[df_f['Empresa'] == f_emp]
        if f_loc != "Todas": df_f = df_f[df_f['Localidad'] == f_loc]
        with f3: st.metric("Dotación", len(df_f))

        # El contenido previo de Performance (Evolución, Ranking, etc.)
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Evolución Acumulada**")
            df_m = df_f.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            st.plotly_chart(px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f'), use_container_width=True)
        with c2:
            st.markdown("**Top 10 Vendedores**")
            st.plotly_chart(px.bar(df_f.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f'), use_container_width=True)

        st.divider()
        # Detalle Vendedor
        v_sel = st.selectbox("Seleccionar Vendedor:", sorted(df_f['Vendedor'].unique()))
        v_d = df_f[df_f['Vendedor'] == v_sel].iloc[0]
        st.subheader(f"Análisis Individual: {v_sel}")
        # (Aquí iría el resto de métricas y gráficos individuales que ya teníamos)

    # ---------------------------------------------------------
    # PANEL: MATRIZ 9-BOX COMERCIAL
    # ---------------------------------------------------------
    elif dimension == "Matriz 9-Box Comercial":
        st.title("🎯 Matriz de Talento 9-Box")
        st.markdown("Eje X: Resultados (Ventas) | Eje Y: Competencias (%)")

        # Preparar datos 9-box
        # Eje X: Usamos el Total Acumulado normalizado a % respecto al máximo o meta
        df_9 = df_raw.copy()
        max_ventas = df_9['Total_Acumulado'].max() if df_9['Total_Acumulado'].max() > 0 else 1
        df_9['Ventas_Porc'] = (df_9['Total_Acumulado'] / max_ventas) * 100

        fig_9 = px.scatter(
            df_9, 
            x='Ventas_Porc', 
            y='Competencias_Porc',
            text='Vendedor',
            color='Empresa',
            size='Total_Acumulado',
            labels={'Ventas_Porc': 'Resultados / Ventas (%)', 'Competencias_Porc': 'Competencias (%)'},
            range_x=[0, 100], range_y=[0, 100],
            height=700
        )

        # Añadir líneas divisorias para crear las 9 cajas (cortes en 33% y 66%)
        fig_9.add_vline(x=33, line_dash="dot", line_color="gray", opacity=0.5)
        fig_9.add_vline(x=66, line_dash="dot", line_color="gray", opacity=0.5)
        fig_9.add_hline(y=33, line_dash="dot", line_color="gray", opacity=0.5)
        fig_9.add_hline(y=66, line_dash="dot", line_color="gray", opacity=0.5)

        # Anotaciones de las categorías
        categorias = [
            (15, 85, "Dilema"), (50, 85, "Estrella Emergente"), (85, 85, "ESTRELLA"),
            (15, 50, "Cuestionable"), (50, 50, "Core Player"), (85, 50, "High Performer"),
            (15, 15, "Bajo Rendimiento"), (50, 15, "En Riesgo"), (85, 15, "Eficaz")
        ]
        for x_pos, y_pos, label in categorias:
            fig_9.add_annotation(x=x_pos, y=y_pos, text=label, showarrow=False, font=dict(color="rgba(0,0,0,0.15)", size=20))

        st.plotly_chart(fig_9, use_container_width=True)
        
        with st.expander("Ver Clasificación Detallada"):
            st.dataframe(df_9[['Vendedor', 'Empresa', 'Ventas_Porc', 'Competencias_Porc']].sort_values('Competencias_Porc', ascending=False))

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
