import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Performance Comercial 2025-2026", layout="wide")

# Función para cargar datos desde Google Sheets (formato export CSV)
def load_data(sheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

# ID de tu documento
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC"

st.title("📊 Análisis de Performance Comercial")
st.markdown("### Enfoque: Productividad y Cumplimiento de Objetivos (People Analytics)")

try:
    # Carga de las solapas específicas
    df_2025 = load_data(SHEET_ID, "PERFO%20COMERCIAL2025")
    df_2026 = load_data(SHEET_ID, "PERFO%20COMERCIAL2026")

    # Limpieza básica (asegurar que existan columnas clave)
    # Nota: El código asume columnas como 'Vendedor', 'Ventas', 'Objetivo'
    df_2025['Año'] = 2025
    df_2026['Año'] = 2026
    df_total = pd.concat([df_2025, df_2026], ignore_index=True)

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    vendedores = st.sidebar.multiselect("Seleccionar Vendedores", options=df_total['Vendedor'].unique(), default=df_total['Vendedor'].unique())
    
    df_filtered = df_total[df_total['Vendedor'].isin(vendedores)]

    # --- MÉTRICAS CLAVE ---
    col1, col2, col3 = st.columns(3)
    
    # Cálculo de cumplimiento promedio
    df_filtered['Cumplimiento'] = (df_filtered['Ventas'] / df_filtered['Objetivo']) * 100
    avg_cumplimiento = df_filtered['Cumplimiento'].mean()
    
    col1.metric("Cumplimiento Promedio", f"{avg_cumplimiento:.1f}%")
    col2.metric("Total Ventas 2025", f"{df_2025['Ventas'].sum():,.0f}")
    col3.metric("Total Ventas 2026 (YTD)", f"{df_2026['Ventas'].sum():,.0f}")

    # --- VISUALIZACIONES ---
    
    # 1. Comparativa de Cumplimiento por Vendedor
    st.subheader("Desempeño Individual: 2025 vs 2026")
    fig_bar = px.bar(df_filtered, x='Vendedor', y='Cumplimiento', color='Año', 
                     barmode='group', labels={'Cumplimiento': '% Cumplimiento'},
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_bar.add_hline(y=100, line_dash="dot", line_color="red", annotation_text="Objetivo 100%")
    st.plotly_chart(fig_bar, use_container_width=True)

    # 2. Análisis de Dispersión: Ventas vs Objetivos
    st.subheader("Relación Ventas vs Objetivos (Matriz de Productividad)")
    fig_scatter = px.scatter(df_filtered, x='Objetivo', y='Ventas', size='Ventas', color='Año',
                             hover_name='Vendedor', trendline="ols")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # 3. Vista de Datos
    with st.expander("Ver base de datos consolidada"):
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.info("Asegúrate de que el Google Sheets tenga el acceso compartido para 'Cualquier persona con el enlace'.")
