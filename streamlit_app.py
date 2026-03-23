import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE NOMBRES DE COLUMNAS (Ajusta aquí si otros nombres fallan)
COL_VENDEDOR = "nombre de vendedor" # Actualizado según tu hallazgo
COL_VENTAS = "Ventas"               # Verifica si se llama así o "Ventas Totales", etc.
COL_OBJETIVO = "Objetivo"           # Verifica si se llama así o "Meta", "Cuota", etc.

st.set_page_config(page_title="Performance Comercial 2025-2026", layout="wide")

def load_data(sheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    
    # Limpieza: quitar espacios en nombres de columnas y eliminar columnas vacías (Unnamed)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Eliminar filas que estén completamente vacías
    df = df.dropna(how='all')
    return df

SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC"

st.title("📊 Análisis de Performance Comercial")
st.markdown("### Dashboard de Productividad (Grupo Cenoa)")

try:
    # Carga de datos
    df_2025 = load_data(SHEET_ID, "PERFO%20COMERCIAL2025")
    df_2026 = load_data(SHEET_ID, "PERFO%20COMERCIAL2026")

    df_2025['Año'] = 2025
    df_2026['Año'] = 2026
    df_total = pd.concat([df_2025, df_2026], ignore_index=True)

    # Verificación de que la columna existe antes de seguir
    if COL_VENDEDOR not in df_total.columns:
        st.error(f"No se encontró la columna '{COL_VENDEDOR}'.")
        st.write("Columnas disponibles:", list(df_total.columns))
        st.stop()

    # --- FILTROS ---
    st.sidebar.header("Filtros de Selección")
    vendedores = st.sidebar.multiselect(
        "Seleccionar Asesores", 
        options=sorted(df_total[COL_VENDEDOR].unique()), 
        default=df_total[COL_VENDEDOR].unique()
    )
    
    df_filtered = df_total[df_total[COL_VENDEDOR].isin(vendedores)]

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    
    # Intentamos calcular métricas si existen las columnas de valores
    if COL_VENTAS in df_filtered.columns and COL_OBJETIVO in df_filtered.columns:
        # Convertir a numérico por si vienen como texto
        df_filtered[COL_VENTAS] = pd.to_numeric(df_filtered[COL_VENTAS], errors='coerce').fillna(0)
        df_filtered[COL_OBJETIVO] = pd.to_numeric(df_filtered[COL_OBJETIVO], errors='coerce').fillna(0)
        
        df_filtered['% Cumplimiento'] = (df_filtered[COL_VENTAS] / df_filtered[COL_OBJETIVO].replace(0, 1)) * 100
        
        avg_perfo = df_filtered['% Cumplimiento'].mean()
        col1.metric("Cumplimiento Promedio", f"{avg_perfo:.1f}%")
        col2.metric("Total Ventas (Consolidado)", f"{df_filtered[COL_VENTAS].sum():,.0f}")
        col3.metric("Total Objetivo", f"{df_filtered[COL_OBJETIVO].sum():,.0f}")

        # --- GRÁFICOS ---
        st.subheader("Evolución de Desempeño por Asesor")
        fig_bar = px.bar(
            df_filtered, 
            x=COL_VENDEDOR, 
            y='% Cumplimiento', 
            color='Año',
            barmode='group',
            text_auto='.1f',
            color_discrete_map={2025: '#AEC6CF', 2026: '#779ECB'}
        )
        fig_bar.add_hline(y=100, line_dash="dot", line_color="red", annotation_text="Meta 100%")
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.warning(f"Revisa si las columnas '{COL_VENTAS}' y '{COL_OBJETIVO}' existen en tu Sheets.")
        st.write("Columnas detectadas:", list(df_total.columns))

    # Tabla de datos crudos para control
    with st.expander("Ver tabla de datos completa"):
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Error de conexión o procesamiento: {e}")
