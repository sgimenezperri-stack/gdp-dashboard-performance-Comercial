import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa Analytics 2025 - Precise", layout="wide", page_icon="📊")

# Estilo visual para KPIs
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; color: #004a99; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #dee2e6; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data_final():
    df = pd.read_csv(URL)
    
    # MAPEADO QUIRÚRGICO POR POSICIÓN (Basado en tus indicaciones)
    # Col B(1): Vendedor | Col D(3): Fecha | Col E(4): Empresa | Col F(5): Loc | Col G(6): Tipo
    # Col H(7): Objetivo | Col AG(32): Total Anual | Col AH(33): Promedio
    
    mapping = {
        df.columns[1]: 'Vendedor',
        df.columns[3]: 'Fecha Ingreso',
        df.columns[4]: 'Empresa',
        df.columns[5]: 'Localidad',
        df.columns[6]: 'Tipo de Venta',
        df.columns[7]: 'Objetivo Anual',
        df.columns[32]: 'Total Ventas',
        df.columns[33]: 'Promedio Mensual'
    }
    
    df = df.rename(columns=mapping)
    
    # Selección de solo las columnas necesarias para el análisis
    cols_interes = ['Vendedor', 'Fecha Ingreso', 'Empresa', 'Localidad', 'Tipo de Venta', 'Objetivo Anual', 'Total Ventas', 'Promedio Mensual']
    df = df[cols_interes].copy()

    # Limpieza numérica (Convertir comas a puntos y manejar nulos)
    for c in ['Objetivo Anual', 'Total Ventas', 'Promedio Mensual']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    return df

try:
    df = load_data_final()

    st.title("🚀 Business Intelligence: Grupo Cenoa 2025")
    st.caption("Análisis acumulado de performance comercial (Enero - Diciembre)")

    # --- PANEL DE FILTROS ---
    st.sidebar.header("🔍 Filtros de Negocio")
    
    with st.sidebar:
        f_empresa = st.multiselect("Filtrar por Empresa", options=sorted(df['Empresa'].dropna().unique()), default=df['Empresa'].dropna().unique())
        f_localidad = st.multiselect("Filtrar por Localidad", options=sorted(df['Localidad'].dropna().unique()), default=df['Localidad'].dropna().unique())
        f_tipo = st.multiselect("Filtrar por Tipo de Venta", options=sorted(df['Tipo de Venta'].dropna().unique()), default=df['Tipo de Venta'].dropna().unique())
        f_vendedor = st.sidebar.text_input("🔍 Buscar Vendedor por nombre")

    # Lógica de filtrado
    mask = df['Empresa'].isin(f_empresa) & df['Localidad'].isin(f_localidad) & df['Tipo de Venta'].isin(f_tipo)
    if f_vendedor:
        mask = mask & df['Vendedor'].str.contains(f_vendedor, case=False, na=False)
    
    df_filtered = df[mask].copy()

    # --- KPIs PRINCIPALES ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_acumulado = df_filtered['Total Ventas'].sum()
    meta_acumulada = df_filtered['Objetivo Anual'].sum()
    alcance_real = (total_acumulado / meta_acumulada * 100) if meta_acumulada > 0 else 0
    promedio_vendedores = df_filtered['Promedio Mensual'].mean()

    c1.metric("Ventas Acumuladas", f"{total_acumulado:,.0f}")
    c2.metric("Meta Total", f"{meta_acumulada:,.0f}")
    c3.metric("% Alcance Anual", f"{alcance_real:.1f}%")
    c4.metric("Promedio de Venta", f"{promedio_vendedores:,.1f}")

    st.divider()

    # --- RANKING DE VENTAS (Col AG) ---
    st.subheader("🏆 Ranking de Ventas Totales por Asesor")
    
    ranking_data = df_filtered.sort_values('Total Ventas', ascending=True).tail(15) # Top 15 para no saturar
    
    fig_rank = px.bar(
        ranking_data,
        x='Total Ventas',
        y='Vendedor',
        orientation='h',
        text='Total Ventas',
        color='Total Ventas',
        color_continuous_scale='Greens',
        labels={'Total Ventas': 'Ventas Acumuladas (Col AG)', 'Vendedor': 'Asesor'}
    )
    fig_rank.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    st.plotly_chart(fig_rank, use_container_width=True)

    # --- COMPARATIVA: OBJETIVO VS REAL ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📍 Desempeño por Localidad")
        fig_loc = px.sunburst(df_filtered, path=['Localidad', 'Empresa'], values='Total Ventas', color='Total Ventas', color_continuous_scale='RdBu')
        st.plotly_chart(fig_loc, use_container_width=True)

    with col_b:
        st.subheader("🎯 Consistencia (Promedio Mensual)")
        # Gráfico para ver quién mantiene el mejor promedio (Col AH)
        fig_avg = px.box(df_filtered, x='Empresa', y='Promedio Mensual', points="all", color="Empresa")
        st.plotly_chart(fig_avg, use_container_width=True)

    # --- TABLA DETALLADA ---
    with st.expander("📄 Ver detalle técnico de columnas (B, D, E, F, G, H, AG, AH)"):
        st.dataframe(df_filtered.sort_values('Total Ventas', ascending=False))

except Exception as e:
    st.error(f"Error de estructura: {e}")
