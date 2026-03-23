import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa Performance Analytics", layout="wide", page_icon="🚗")

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border: 1px solid #e0e0e0; padding: 10px; border-radius: 8px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS (Link Publicado) ---
# Convertimos tu link de HTML a formato de descarga CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRUIM7cEzymYekqDN9I4Jyd0o9peeJh5izcTtFFHPDzxBmt1zWJxa3gyD8hDMBLDw/pub?output=csv"

@st.cache_data
def get_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip().str.lower()
        # Limpieza de valores numéricos
        cols_to_fix = ['ventas', 'objetivo', 'competencias', 'potencial']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = get_data()

# --- INTERFAZ PRINCIPAL ---
st.title("📊 Business Intelligence: Performance Comercial")
st.info("Visualización analítica para la gestión de equipos y resultados.")

if not df.empty:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Análisis")
    
    # Filtros dinámicos basados en tus datos
    brand_col = next((c for c in df.columns if 'marca' in c or 'empresa' in c), None)
    vendedor_col = next((c for c in df.columns if 'nombre' in c or 'vendedor' in c), 'vendedor')
    
    selected_brands = []
    if brand_col:
        selected_brands = st.sidebar.multiselect("Marca/Empresa", options=df[brand_col].unique(), default=df[brand_col].unique())
    
    # Filtrado de datos
    df_filtered = df.copy()
    if selected_brands:
        df_filtered = df_filtered[df_filtered[brand_col].isin(selected_brands)]

    # --- KPIs SUPERIORES ---
    m1, m2, m3, m4 = st.columns(4)
    
    # Cálculo de cumplimiento
    if 'ventas' in df_filtered.columns and 'objetivo' in df_filtered.columns:
        total_ventas = df_filtered['ventas'].sum()
        total_obj = df_filtered['objetivo'].sum()
        cumplimiento_gen = (total_ventas / total_obj * 100) if total_obj > 0 else 0
        
        m1.metric("Ventas Totales", f"{total_ventas:,.0f}")
        m2.metric("Objetivo Global", f"{total_obj:,.0f}")
        m3.metric("% Cumplimiento", f"{cumplimiento_gen:.1f}%")
        m4.metric("Dotación Activa", len(df_filtered))

    st.divider()

    # --- BLOQUE ANALÍTICO 1: PERFORMANCE ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏆 Ranking de Cumplimiento por Asesor")
        df_filtered['% cumpl.'] = (df_filtered['ventas'] / df_filtered['objetivo'] * 100).round(1)
        fig_rank = px.bar(
            df_filtered.sort_values('% cumpl.', ascending=True).tail(10),
            x='% cumpl.', y=vendedor_col, orientation='h',
            text='% cumpl.', color='% cumpl.',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with col_b:
        st.subheader("📈 Relación Ventas vs Objetivos")
        fig_scatter = px.scatter(
            df_filtered, x='objetivo', y='ventas', 
            size='ventas', color='% cumpl.',
            hover_name=vendedor_col, trendline="ols",
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- BLOQUE ANALÍTICO 2: MATRIZ 9-BOX (People Analytics) ---
    st.divider()
    st.subheader("🎯 Matriz de Talento: Desempeño vs Competencias")
    
    if 'competencias' in df_filtered.columns:
        # Definimos cuadrantes
        fig_9box = px.scatter(
            df_filtered, 
            x='competencias', 
            y='ventas' if 'ventas' not in df_filtered.columns else '% cumpl.',
            text=vendedor_col,
            size_max=20,
            labels={'x': 'Nivel de Competencias', 'y': '% Desempeño'},
            template="plotly_white",
            height=600
        )
        # Líneas de cuadrantes (promedios)
        fig_9box.add_hline(y=df_filtered['% cumpl.'].mean(), line_dash="dot", line_color="red")
        fig_9box.add_vline(x=df_filtered['competencias'].mean(), line_dash="dot", line_color="red")
        
        st.plotly_chart(fig_9box, use_container_width=True)
        st.caption("Los cuadrantes ayudan a identificar: Estrellas (Sup-Der), Potenciales (Inf-Der) y Áreas de Mejora (Inf-Izq).")

    # --- TABLA MAESTRA ---
    with st.expander("🔍 Ver Detalle de Datos"):
        st.dataframe(df_filtered.style.background_gradient(cmap='Blues', subset=['ventas']))

else:
    st.warning("No se pudo leer la información. Verifica que el enlace de publicación sea el correcto.")
