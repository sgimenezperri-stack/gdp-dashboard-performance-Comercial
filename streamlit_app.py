import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa Analytics 2025", layout="wide", page_icon="📈")

# Estilo para mejorar la visualización de métricas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1f77b4; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data_2025():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    
    # Mapeo por posición (B=1, D=3, E=4, F=5, G=6)
    rename_dict = {
        df.columns[1]: 'Vendedor',
        df.columns[3]: 'Fecha Ingreso',
        df.columns[4]: 'Empresa',
        df.columns[5]: 'Localidad',
        df.columns[6]: 'Tipo de Venta'
    }
    df = df.rename(columns=rename_dict)
    
    # Auto-detección de Ventas y Objetivo (posiciones H=7 e I=8 aprox)
    col_ventas = df.columns[7]
    col_obj = df.columns[8]
    df = df.rename(columns={col_ventas: 'Ventas', col_obj: 'Objetivo'})
    
    # Limpieza numérica
    for c in ['Ventas', 'Objetivo']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    return df

try:
    df = load_data_2025()

    # --- TÍTULO PRINCIPAL ---
    st.title("📊 Performance Comercial Grupo Cenoa")
    st.caption("Dashboard de Análisis de Ventas y Cumplimiento - Ciclo 2025")

    # --- FILTROS LIMPIOS (Sin referencias de columnas) ---
    st.sidebar.header("🎯 Panel de Filtros")
    
    with st.sidebar:
        f_empresa = st.multiselect("Filtrar por Empresa", options=sorted(df['Empresa'].dropna().unique()), default=df['Empresa'].dropna().unique())
        f_localidad = st.multiselect("Filtrar por Localidad", options=sorted(df['Localidad'].dropna().unique()), default=df['Localidad'].dropna().unique())
        f_tipo = st.multiselect("Filtrar por Tipo de Venta", options=sorted(df['Tipo de Venta'].dropna().unique()), default=df['Tipo de Venta'].dropna().unique())
        f_vendedor = st.multiselect("Buscar Vendedor Específico", options=sorted(df['Vendedor'].dropna().unique()))

    # Lógica de filtrado
    mask = df['Empresa'].isin(f_empresa) & df['Localidad'].isin(f_localidad) & df['Tipo de Venta'].isin(f_tipo)
    if f_vendedor:
        mask = mask & df['Vendedor'].isin(f_vendedor)
    
    df_filtered = df[mask].copy()

    # --- INDICADORES ---
    c1, c2, c3, c4 = st.columns(4)
    total_vta = df_filtered['Ventas'].sum()
    total_obj = df_filtered['Objetivo'].sum()
    cumpl_prom = (total_vta / total_obj * 100) if total_obj > 0 else 0
    
    c1.metric("Ventas Totales", f"$ {total_vta:,.0f}")
    c2.metric("Objetivo Total", f"$ {total_obj:,.0f}")
    c3.metric("% Cumplimiento", f"{cumpl_prom:.1f}%")
    c4.metric("Efectivos", len(df_filtered))

    st.divider()

    # --- SECCIÓN: RANKING DE VENTAS ---
    st.subheader("🏆 Ranking de Ventas por Asesor")
    
    # Preparamos el ranking
    ranking_df = df_filtered.sort_values('Ventas', ascending=True) # Ascending True para que el mayor quede arriba en el bar chart horizontal

    fig_ranking = px.bar(
        ranking_df,
        x='Ventas',
        y='Vendedor',
        orientation='h',
        text='Ventas',
        color='Ventas',
        color_continuous_scale='Blues',
        labels={'Ventas': 'Volumen de Ventas', 'Vendedor': 'Asesor Comercial'}
    )
    
    fig_ranking.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig_ranking.update_layout(showlegend=False, height=max(400, len(ranking_df) * 30)) # Altura dinámica según cantidad de vendedores
    
    st.plotly_chart(fig_ranking, use_container_width=True)

    # --- ANÁLISIS SECUNDARIO ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📍 Ventas por Localidad")
        fig_loc = px.pie(df_filtered, values='Ventas', names='Localidad', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_loc, use_container_width=True)

    with col_b:
        st.subheader("🏢 Mix de Ventas por Empresa")
        fig_emp = px.bar(df_filtered.groupby('Empresa')['Ventas'].sum().reset_index(), 
                         x='Empresa', y='Ventas', color='Empresa', text_auto='.2s')
        st.plotly_chart(fig_emp, use_container_width=True)

    # Tabla detallada
    with st.expander("📋 Ver detalle de datos filtrados"):
        st.dataframe(df_filtered[['Vendedor', 'Empresa', 'Localidad', 'Tipo de Venta', 'Ventas', 'Objetivo']].sort_values('Ventas', ascending=False))

except Exception as e:
    st.error(f"Se detectó un cambio en la estructura del archivo: {e}")
