import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN E IDENTIFICADORES
SHEET_ID = "1bjkGqCy_ftvAxfqkbxprVrvDMGIaQV91"
# Nombres de columnas detectados en tus reportes de Cenoa
COL_NOMBRE = "Nombre y apellido"
COL_COMPETENCIAS = "Puntaje competencias"
COL_OBJETIVOS = "Puntaje objetivos 2"
COL_JEFE = "Jefe directo"
COL_PUNTAJE_FINAL = "Nuevo puntaje (1-5)"

st.set_page_config(page_title="Cenoa Analytics Pro", layout="wide", initial_sidebar_state="expanded")

# Estilo personalizado
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(sheet_id):
    # Intentamos cargar la primera solapa útil (usualmente la de resultados)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    
    # Limpieza de datos numéricos (manejo de comas decimales y nulos)
    for col in [COL_COMPETENCIAS, COL_OBJETIVOS, COL_PUNTAJE_FINAL]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0)
    
    return df

# --- CARGA DE DATOS ---
try:
    df = load_and_clean_data(SHEET_ID)
    
    st.title("🚀 Business Intelligence: Performance Comercial")
    st.subheader("Grupo Cenoa - Análisis Integral de Talento y Resultados")

    # --- SIDEBAR / FILTROS ---
    st.sidebar.image("https://via.placeholder.com/150x50?text=GRUPO+CENOA", use_container_width=True) # Reemplazar con URL de logo real
    st.sidebar.header("Panel de Control")
    
    filter_jefe = st.sidebar.multiselect("Filtrar por Líder Directo", options=sorted(df[COL_JEFE].unique()) if COL_JEFE in df.columns else ["N/A"])
    
    df_plot = df.copy()
    if filter_jefe:
        df_plot = df_plot[df_plot[COL_JEFE].isin(filter_jefe)]

    # --- INDICADORES CLAVE (KPIs) ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Dotación Evaluada", len(df_plot))
    with kpi2:
        avg_obj = df_plot[COL_OBJETIVOS].mean()
        st.metric("Promedio Objetivos", f"{avg_obj:.2f}")
    with kpi3:
        avg_comp = df_plot[COL_COMPETENCIAS].mean()
        st.metric("Promedio Competencias", f"{avg_comp:.2f}")
    with kpi4:
        top_perf = len(df_plot[df_plot[COL_PUNTAJE_FINAL] >= 4])
        st.metric("High Performers (>4)", top_perf)

    st.divider()

    # --- ANÁLISIS ANALÍTICO ---
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### 🎯 Matriz de Talento (Competencias vs Objetivos)")
        # Este gráfico es clave en People Analytics para ver quién "sabe hacer" vs "quién llega a la meta"
        fig_matrix = px.scatter(
            df_plot, 
            x=COL_COMPETENCIAS, 
            y=COL_OBJETIVOS,
            size=COL_PUNTAJE_FINAL,
            color=COL_JEFE if COL_JEFE in df.columns else None,
            hover_name=COL_NOMBRE,
            text=COL_NOMBRE if len(df_plot) < 15 else None,
            labels={COL_COMPETENCIAS: "Nivel de Competencias", COL_OBJETIVOS: "Cumplimiento Objetivos"},
            template="plotly_white"
        )
        fig_matrix.add_hline(y=df_plot[COL_OBJETIVOS].mean(), line_dash="dot", line_color="gray")
        fig_matrix.add_vline(x=df_plot[COL_COMPETENCIAS].mean(), line_dash="dot", line_color="gray")
        st.plotly_chart(fig_matrix, use_container_width=True)

    with col_right:
        st.markdown("### 🏆 Top 10 Desempeño Consolidado")
        top_10 = df_plot.nlargest(10, COL_PUNTAJE_FINAL)
        fig_rank = px.bar(
            top_10, 
            x=COL_PUNTAJE_FINAL, 
            y=COL_NOMBRE, 
            orientation='h',
            color=COL_PUNTAJE_FINAL,
            color_continuous_scale='Blues',
            text_auto=True
        )
        fig_rank.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_rank, use_container_width=True)

    # --- DETALLE POR LÍDER ---
    st.markdown("### 📊 Desempeño Promedio por Equipo (Jefe Directo)")
    if COL_JEFE in df_plot.columns:
        df_jefe = df_plot.groupby(COL_JEFE)[[COL_COMPETENCIAS, COL_OBJETIVOS]].mean().reset_index()
        fig_jefe = go.Figure()
        fig_jefe.add_trace(go.Bar(name='Competencias', x=df_jefe[COL_JEFE], y=df_jefe[COL_COMPETENCIAS], marker_color='#1f77b4'))
        fig_jefe.add_trace(go.Bar(name='Objetivos', x=df_jefe[COL_JEFE], y=df_jefe[COL_OBJETIVOS], marker_color='#ff7f0e'))
        fig_jefe.update_layout(barmode='group', template="plotly_white")
        st.plotly_chart(fig_jefe, use_container_width=True)

    # --- TABLA DE DATOS ---
    with st.expander("🔍 Explorar Base de Datos Completa"):
        st.dataframe(df_plot.style.highlight_max(axis=0, subset=[COL_PUNTAJE_FINAL]))

except Exception as e:
    st.error(f"Error al procesar la nueva base de datos: {e}")
    st.info("Asegúrate de que el link de Google Sheets sea público ('Cualquier persona con el enlace').")
