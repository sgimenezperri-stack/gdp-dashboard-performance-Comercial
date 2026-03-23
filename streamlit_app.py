import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Cenoa Analytics 2025", layout="wide")

# ID del documento original para poder elegir la solapa por nombre
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data_2025():
    # Cargamos el CSV
    df = pd.read_csv(URL)
    
    # Mapeo manual basado en tus instrucciones de columnas:
    # Col A (0): CUIL -> Ignorar
    # Col B (1): Vendedor
    # Col D (3): Fecha de ingreso
    # Col E (4): Empresa
    # Col F (5): Localidad
    # Col G (6): Tipo de Venta
    
    # Seleccionamos por índice para evitar errores de nombres
    columnas_indices = [1, 3, 4, 5, 6] 
    # También necesitamos traer las columnas de métricas (asumiendo que están después de la G)
    # Traeremos todas y luego renombraremos las específicas que pediste.
    
    # Limpieza de nombres de columnas actuales
    df.columns = df.columns.str.strip()
    
    # Renombrado forzado según tu estructura
    rename_dict = {
        df.columns[1]: 'Vendedor',
        df.columns[3]: 'Fecha Ingreso',
        df.columns[4]: 'Empresa',
        df.columns[5]: 'Localidad',
        df.columns[6]: 'Tipo de Venta'
    }
    df = df.rename(columns=rename_dict)
    
    # Convertir Fecha de Ingreso a formato fecha
    df['Fecha Ingreso'] = pd.to_datetime(df['Fecha Ingreso'], errors='coerce')
    
    # Auto-detectar columnas de Ventas y Objetivo (suelen estar en H e I / índices 7 y 8)
    col_ventas = next((c for c in df.columns if 'Venta' in c and c != 'Tipo de Venta'), df.columns[7])
    col_obj = next((c for c in df.columns if 'Obj' in c or 'Meta' in c), df.columns[8])
    
    df = df.rename(columns={col_ventas: 'Ventas', col_obj: 'Objetivo'})
    
    # Limpieza numérica
    for c in ['Ventas', 'Objetivo']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
    return df

try:
    df = load_data_2025()

    st.title("🚗 Control Comercial 2025")
    st.markdown("### Análisis por Estructura y Segmentación")

    # --- BLOQUE DE FILTROS (Basado en tus columnas solicitadas) ---
    st.sidebar.header("🔍 Filtros de Negocio")
    
    with st.sidebar:
        f_empresa = st.multiselect("Empresa (Col E)", options=sorted(df['Empresa'].dropna().unique()), default=df['Empresa'].dropna().unique())
        f_localidad = st.multiselect("Localidad (Col F)", options=sorted(df['Localidad'].dropna().unique()), default=df['Localidad'].dropna().unique())
        f_tipo = st.multiselect("Tipo de Venta (Col G)", options=sorted(df['Tipo de Venta'].dropna().unique()), default=df['Tipo de Venta'].dropna().unique())
        f_vendedor = st.multiselect("Vendedor (Col B)", options=sorted(df['Vendedor'].dropna().unique()))

    # Aplicar Filtros
    mask = df['Empresa'].isin(f_empresa) & df['Localidad'].isin(f_localidad) & df['Tipo de Venta'].isin(f_tipo)
    if f_vendedor:
        mask = mask & df['Vendedor'].isin(f_vendedor)
    
    df_filtered = df[mask]

    # --- DASHBOARD ---
    # Métricas principales
    c1, c2, c3 = st.columns(3)
    total_vta = df_filtered['Ventas'].sum()
    total_obj = df_filtered['Objetivo'].sum()
    cumpl = (total_vta / total_obj * 100) if total_obj > 0 else 0
    
    c1.metric("Ventas Totales", f"{total_vta:,.0f}")
    c2.metric("Cumplimiento Promedio", f"{cumpl:.1f}%")
    c3.metric("Asesores Filtrados", len(df_filtered))

    st.divider()

    # Gráfico de Productividad por Localidad y Empresa
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Performance por Empresa")
        fig_emp = px.bar(df_filtered.groupby('Empresa')['Ventas'].sum().reset_index(), 
                         x='Empresa', y='Ventas', color='Empresa', text_auto=True)
        st.plotly_chart(fig_emp, use_container_width=True)

    with col_right:
        st.subheader("Cumplimiento por Vendedor (Col B)")
        df_filtered['%'] = (df_filtered['Ventas'] / df_filtered['Objetivo'] * 100).round(1)
        fig_vend = px.bar(df_filtered.sort_values('%'), x='%', y='Vendedor', orientation='h', 
                          color='%', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_vend, use_container_width=True)

    # Tabla Maestra
    with st.expander("📄 Ver Base de Datos (Columnas B, D, E, F, G)"):
        st.write(df_filtered[['Vendedor', 'Fecha Ingreso', 'Empresa', 'Localidad', 'Tipo de Venta', 'Ventas', 'Objetivo']])

except Exception as e:
    st.error(f"Error en la estructura: {e}")
    st.info("Verifica que la solapa 'PERFO COMERCIAL2025' sea la correcta.")
