import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Performance Comercial 2025-2026", layout="wide")

# Función para cargar datos desde Google Sheets (formato export CSV)
def load_data(sheet_id, sheet_name):
    # Formato de URL para exportación directa como CSV
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    # Lee y limpia espacios en blanco de los nombres de columna
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

# ID de tu documento (extraído del nuevo enlace que pasaste)
# https://docs.google.com/spreadsheets/d/1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC/edit
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC"

st.title("📊 Análisis de Performance Comercial")
st.markdown("### Enfoque: Productividad y Cumplimiento de Objetivos (People Analytics)")

try:
    # 1. HERRAMIENTA DE INSPECCIÓN (Temporal)
    # Mostramos los nombres de las columnas para verificar por qué falla
    st.info("🔎 Inspección de Columnas (esto se puede quitar luego)")
    
    # Intenta cargar datos para la inspección
    test_df_2025 = load_data(SHEET_ID, "PERFO%20COMERCIAL2025")
    test_df_2026 = load_data(SHEET_ID, "PERFO%20COMERCIAL2026")

    col_insp1, col_insp2 = st.columns(2)
    with col_insp1:
        st.write("**Columnas encontradas en PERFO COMERCIAL2025:**")
        st.write(list(test_df_2025.columns))
    with col_insp2:
        st.write("**Columnas encontradas en PERFO COMERCIAL2026:**")
        st.write(list(test_df_2026.columns))
    
    st.divider()

    # 2. CARGA DE DATOS PRINCIPAL
    df_2025 = load_data(SHEET_ID, "PERFO%20COMERCIAL2025")
    df_2026 = load_data(SHEET_ID, "PERFO%20COMERCIAL2026")

    # Mapeo de columnas corregido (basado en la inspección)
    # Por favor, revisa la inspección y actualiza 'Vendedor', 'Ventas', 'Objetivo'
    # con los nombres EXACTOS de tus columnas.
    # El error sugiere que 'Vendedor' es incorrecto.

    # -- EJEMPLO DE CORRECCIÓN --
    # Si la inspección muestra ['Vendedor ', ' Ventas_Final', 'Cuota']
    # Cambia las claves de abajo (Vendedor, Ventas, Objetivo) para que coincidan.
    # column_mapping = {'Vendedor ': 'Vendedor', ' Ventas_Final': 'Ventas', 'Cuota': 'Objetivo'}
    
    # Por ahora, mantengo tu solicitud pero envuelta para diagnóstico.
    try:
        df_2025['Año'] = 2025
        df_2026['Año'] = 2026
        df_total = pd.concat([df_2025, df_2026], ignore_index=True)
    except KeyError as ke:
        st.error(f"Falla crítica: Las columnas principales no coinciden entre los años 2025 y 2026. Error de columna: {ke}")
        st.stop()

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    
    # Comprobación de seguridad para 'Vendedor'
    if 'Vendedor' not in df_total.columns:
        st.error("La columna 'Vendedor' no existe en los datos combinados. Revisa la sección de 'Inspección de Columnas' para corregir el nombre en el código.")
        st.stop()

    vendedores = st.sidebar.multiselect("Seleccionar Vendedores", options=df_total['Vendedor'].unique(), default=df_total['Vendedor'].unique())
    df_filtered = df_total[df_total['Vendedor'].isin(vendedores)]

    # --- MÉTRICAS Y VISUALIZACIONES (Asumiendo nombres de columna corregidos) ---
    if 'Ventas' in df_filtered.columns and 'Objetivo' in df_filtered.columns:
        col1, col2, col3 = st.columns(3)
        df_filtered['Cumplimiento'] = (df_filtered['Ventas'] / df_filtered['Objetivo']) * 100
        avg_cumplimiento = df_filtered['Cumplimiento'].mean()
        
        col1.metric("Cumplimiento Promedio", f"{avg_cumplimiento:.1f}%")
        col2.metric("Total Ventas 2025", f"{df_2025['Ventas'].sum():,.0f}")
        col3.metric("Total Ventas 2026 (YTD)", f"{df_2026['Ventas'].sum():,.0f}")

        # Visualizaciones
        st.subheader("Desempeño Individual: 2025 vs 2026")
        fig_bar = px.bar(df_filtered, x='Vendedor', y='Cumplimiento', color='Año', 
                         barmode='group', labels={'Cumplimiento': '% Cumplimiento'},
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_bar.add_hline(y=100, line_dash="dot", line_color="red", annotation_text="Objetivo 100%")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No se pueden generar las visualizaciones porque faltan las columnas 'Ventas' u 'Objetivo'.")

    # Vista de Datos
    with st.expander("Ver base de datos consolidada"):
        st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
