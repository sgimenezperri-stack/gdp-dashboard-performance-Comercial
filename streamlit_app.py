import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cenoa Analytics BI", layout="wide", page_icon="📊")

# Estilos CSS - Blindaje de Interfaz
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .category-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #e67e22; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
SHEET_NAME = "PERFO%20COMERCIAL2025"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data
def load_data():
    df = pd.read_csv(URL)
    # Mapeo: B=1, C=2, E=4, F=5, G=6, H=7, AG=32, AH=33
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    # Resultados (I, K, M...): 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30
    idx_res = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    meses_n = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    for i, idx in enumerate(idx_res):
        df[meses_n[i]] = pd.to_numeric(df.iloc[:, idx].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # Competencias (AM, AO, AQ, AS, AU, AW): 38, 40, 42, 44, 46, 48
    idx_comp = [38, 40, 42, 44, 46, 48]
    df['Score_Comp'] = df.iloc[:, idx_comp].apply(pd.to_numeric, errors='coerce').mean(axis=1).fillna(0)
    df['Comp_Porc'] = (df['Score_Comp'] / 5) * 100 
    
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    
    # Iniciales para el gráfico
    df['Iniciales'] = df['Vendedor'].apply(lambda x: "".join([n[0] for n in str(x).split() if n]).upper())
    
    return df, meses_n

# Función Antigüedad
def get_ant(fecha):
    if pd.isnull(fecha): return "Dato N/A"
    hoy = datetime(2025, 12, 31)
    diff = hoy - fecha
    a, m = diff.days // 365, (diff.days % 365) // 30
    return f"{a} años y {m} meses" if a > 0 else f"{m} meses"

try:
    df_raw, lista_meses = load_data()

    # --- NAVEGACIÓN LATERAL ---
    dimension = st.sidebar.radio("DIMENSIÓN", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # =========================================================
    # DIMENSIÓN 1: PERFORMANCE COMERCIAL (RESTAURADA)
    # =========================================================
    if dimension == "Performance Comercial":
        # FILTROS SUPERIORES (Blindados)
        st.markdown("### Performance Comercial Grupo Cenoa")
        f1, f2, f3, f4 = st.columns([1, 2, 2, 1])
        with f1: st.selectbox("AÑO", ["2025"])
        with f2: 
            op_e = [x for x in sorted(df_raw['Empresa'].unique()) if str(x).upper() != "EMPRESA"]
            sel_emp = st.selectbox("EMPRESA", ["Todas"] + op_e)
        with f3: 
            op_l = [x for x in sorted(df_raw['Localidad'].unique()) if str(x).upper() != "LOCALIDAD"]
            sel_loc = st.selectbox("LOCALIDAD", ["Todas"] + op_l)
        
        df_p = df_raw.copy()
        if sel_emp != "Todas": df_p = df_p[df_p['Empresa'] == sel_emp]
        if sel_loc != "Todas": df_p = df_p[df_p['Localidad'] == sel_loc]
        with f4: st.metric("VENDEDORES", len(df_p))

        # Fila de Gráficos Principales
        c_p1, c_p2 = st.columns([1.5, 1])
        with c_p1:
            st.markdown("**Cantidad de Operaciones por Empresa**")
            df_m = df_p.groupby('Empresa')[lista_meses].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            st.plotly_chart(px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f', color_discrete_sequence=px.colors.qualitative.Pastel).update_xaxes(categoryorder='array', categoryarray=lista_meses), use_container_width=True)
        with c_p2:
            st.markdown("**Top 10 Vendedores (Operaciones)**")
            st.plotly_chart(px.bar(df_p.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22']), use_container_width=True)

        st.divider()
        # Sección Individual
        col_list, col_det = st.columns([1, 2.5])
        with col_list:
            v_sel = st.selectbox("Seleccionar Vendedor:", sorted(df_p['Vendedor'].unique()))
            v_data = df_p[df_p['Vendedor'] == v_sel].iloc[0]
        with col_det:
            d1, d2, d3 = st.columns([3, 1, 1])
            with d1:
                st.subheader(v_sel)
                st.markdown(f"<span style='color:#e67e22; font-weight:bold;'>{get_ant(v_data['Fecha_Ingreso'])}</span>", unsafe_allow_html=True)
                st.caption(f"{v_data['Canal']} | {v_data['Empresa']} | {v_data['Localidad']}")
            d2.metric("OBJ", int(v_data['Objetivo_Mensual']))
            diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
            d3.metric("PROM", f"{v_data['Promedio']:.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")
            
            fig_i = go.Figure()
            fig_i.add_trace(go.Bar(x=lista_meses, y=[v_data[m] for m in lista_meses], name="Ventas", text_auto='.0f'))
            fig_i.add_trace(go.Scatter(x=lista_meses, y=[v_data['Objetivo_Mensual']]*12, mode='lines', name="Objetivo", line=dict(color='red', dash='dot')))
            st.plotly_chart(fig_i.update_layout(height=300, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses)), use_container_width=True)

    # =========================================================
    # DIMENSIÓN 2: MATRIZ 9-BOX (MEJORADA)
    # =========================================================
    elif dimension == "Matriz 9-Box Comercial":
        st.markdown("### 🎯 Matriz de Talento 9-Box")
        
        # Filtros de Matriz
        m_f1, m_f2, m_f3 = st.columns(3)
        with m_f1: sel_mes = st.selectbox("Seleccionar Mes para Resultados", lista_meses)
        with m_f2: 
            op_e9 = [x for x in sorted(df_raw['Empresa'].unique()) if str(x).upper() != "EMPRESA"]
            f_emp9 = st.selectbox("Empresa ", ["Todas"] + op_e9)
        with m_f3: 
            op_l9 = [x for x in sorted(df_raw['Localidad'].unique()) if str(x).upper() != "LOCALIDAD"]
            f_loc9 = st.selectbox("Localidad ", ["Todas"] + op_l9)

        df_9 = df_raw.copy()
        if f_emp9 != "Todas": df_9 = df_9[df_9['Empresa'] == f_emp9]
        if f_loc9 != "Todas": df_9 = df_9[df_9['Localidad'] == f_loc9]
        
        # Cálculo de Eje X (Normalizado al mes seleccionado)
        max_m = df_9[sel_mes].max() if df_9[sel_mes].max() > 0 else 1
        df_9['Res_Porc'] = (df_9[sel_mes] / max_m) * 100

        # Botones de Categoría (9 Box)
        st.write("**Filtrar por Categoría de Talento:**")
        b1, b2, b3 = st.columns(3)
        b4, b5, b6 = st.columns(3)
        b7, b8, b9 = st.columns(3)
        
        cat_map = {
            "Dilema": (df_9['Res_Porc'] < 33) & (df_9['Comp_Porc'] > 66),
            "E. Emergente": (df_9['Res_Porc'].between(33, 66)) & (df_9['Comp_Porc'] > 66),
            "ESTRELLA": (df_9['Res_Porc'] > 66) & (df_9['Comp_Porc'] > 66),
            "Cuestionable": (df_9['Res_Porc'] < 33) & (df_9['Comp_Porc'].between(33, 66)),
            "Core Player": (df_9['Res_Porc'].between(33, 66)) & (df_9['Comp_Porc'].between(33, 66)),
            "High Performer": (df_9['Res_Porc'] > 66) & (df_9['Comp_Porc'].between(33, 66)),
            "Bajo Rend.": (df_9['Res_Porc'] < 33) & (df_9['Comp_Porc'] < 33),
            "En Riesgo": (df_9['Res_Porc'].between(33, 66)) & (df_9['Comp_Porc'] < 33),
            "Eficaz": (df_9['Res_Porc'] > 66) & (df_9['Comp_Porc'] < 33)
        }

        # Estado de categoría seleccionada
        if "cat_sel" not in st.session_state: st.session_state.cat_sel = None
        
        # Render de botones
        keys = list(cat_map.keys())
        for i, col in enumerate([b1, b2, b3, b4, b5, b6, b7, b8, b9]):
            if col.button(keys[i]): st.session_state.cat_sel = keys[i]

        # Gráfico con Iniciales
        fig_9 = px.scatter(
            df_9, x='Res_Porc', y='Comp_Porc', text='Iniciales', color='Empresa',
            size='Total_Acumulado', hover_name='Vendedor',
            range_x=[0, 105], range_y=[0, 105],
            labels={'Res_Porc': f'Resultados {sel_mes} (%)', 'Comp_Porc': 'Competencias (%)'},
            height=600, template="plotly_white"
        )
        fig_9.update_traces(textposition='middle center', textfont_size=10, marker=dict(opacity=0.7))
        fig_9.add_vline(x=33.3, line_dash="dot", line_color="gray")
        fig_9.add_vline(x=66.6, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=33.3, line_dash="dot", line_color="gray")
        fig_9.add_hline(y=66.6, line_dash="dot", line_color="gray")
        st.plotly_chart(fig_9, use_container_width=True)

        # Detalle de Categoría Seleccionada
        if st.session_state.cat_sel:
            st.markdown(f"#### Detalle: {st.session_state.cat_sel}")
            df_cat = df_9[cat_map[st.session_state.cat_sel]]
            st.dataframe(df_cat[['Vendedor', 'Empresa', sel_mes, 'Comp_Porc']].rename(columns={sel_mes: 'Ventas Mes', 'Comp_Porc': '% Competencias'}))

except Exception as e:
    st.error(f"Error de sistema: {e}")
