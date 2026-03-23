import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- INTENTAR IMPORTAR LIBRERÍA DE CLICKS ---
try:
    from streamlit_plotly_events import plotly_events
    CLICK_HABILITADO = True
except ImportError:
    CLICK_HABILITADO = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Performance Comercial Cenoa", layout="wide", page_icon="📈")

# Estilos CSS - DISEÑO PROFESIONAL INTACTO
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stSidebar"] { background-color: #1e272e; }
    [data-testid="stSidebar"] .stRadio > label { font-size: 14px !important; color: #ffffff !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label { padding: 15px 20px; background-color: #2f3640; border-radius: 8px; margin-bottom: 10px; transition: all 0.3s ease; border-left: 5px solid transparent; cursor: pointer; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label p, [data-testid="stSidebar"] div[role="radiogroup"] > label div { color: #ffffff !important; font-size: 16px !important; font-weight: 600; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: #353b48; border-left: 5px solid #e67e22; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] { background-color: #e67e22 !important; border-left: 5px solid #d35400; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #ffffff; border: 1px solid #c8d6e5; transition: 0.3s; }
    .stButton>button:hover { border: 1px solid #2e86de; box-shadow: 0px 4px 10px rgba(0,0,0,0.08); }
    .metric-card { background-color: #ffffff; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .perfil-asesor { background-color: #ffffff; padding: 15px 20px; border-radius: 10px; border-left: 5px solid #e67e22; margin-bottom: 20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);}
    </style>
    """, unsafe_allow_html=True)

# --- CARGA Y LIMPIEZA DE DATOS DINÁMICA POR AÑO ---
@st.cache_data
def load_data(anio_seleccionado):
    SHEET_ID = "1fXJ2UsTeOE8ipYXeP5oQYYCHRNtDJDRC" 
    # Reemplazamos estáticamente el 2025 por la variable del año para leer la solapa correcta
    SHEET_NAME = f"PERFO%20COMERCIAL{anio_seleccionado}" 
    URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

    df = pd.read_csv(URL)
    mapping = {
        df.columns[1]: 'Vendedor', df.columns[2]: 'Fecha_Ingreso',
        df.columns[4]: 'Empresa', df.columns[5]: 'Localidad',
        df.columns[6]: 'Canal', df.columns[7]: 'Objetivo_Mensual',
        df.columns[32]: 'Total_Acumulado', df.columns[33]: 'Promedio'
    }
    
    meses_n = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    idx_v = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] 
    idx_p = [9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    
    for i, mes in enumerate(meses_n):
        df[f"{mes}_v"] = pd.to_numeric(df.iloc[:, idx_v[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df[f"{mes}_%"] = pd.to_numeric(df.iloc[:, idx_p[i]].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)

    comp_labels = ['CRM', 'Imagen', 'Autogestión', 'Habilidad', 'Técnica']
    idx_comp = [38, 40, 42, 44, 46]
    for i, label in enumerate(comp_labels):
        df[label] = pd.to_numeric(df.iloc[:, idx_comp[i]].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    df['Comp_Total_%'] = df[comp_labels].mean(axis=1).fillna(0) * 20
    df = df.rename(columns=mapping)
    df['Fecha_Ingreso'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    
    for col in ['Objetivo_Mensual', 'Total_Acumulado', 'Promedio', 'Comp_Total_%']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    df = df[df['Vendedor'].astype(str).str.upper() != 'VENDEDOR']
    df['Iniciales'] = df['Vendedor'].apply(lambda x: "".join([n[0] for n in str(x).split() if n]).upper())
    df['Size_Marker'] = df['Total_Acumulado'].clip(lower=1).fillna(1)
    df['Alcance_Total_Anual'] = (df['Total_Acumulado'] / (df['Objetivo_Mensual'] * 12).replace(0, 1)) * 100
    
    return df, meses_n, comp_labels

# Calculamos la antigüedad basándonos en el año seleccionado
def get_ant(fecha, anio_ref):
    if pd.isnull(fecha): return "Sin Dato"
    diff = datetime(int(anio_ref), 12, 31) - fecha
    a, m = diff.days // 365, (diff.days % 365) // 30
    return f"{a} años y {m} meses" if a > 0 else f"{m} meses"

try:
    st.sidebar.markdown("<br><h2 style='text-align: center; color: white;'>GRUPO CENOA</h2><br>", unsafe_allow_html=True)
    dimension = st.sidebar.radio("MÓDULOS", ["Performance Comercial", "Matriz 9-Box Comercial"])

    # =========================================================
    # DIMENSIÓN 1: PERFORMANCE COMERCIAL
    # =========================================================
    if dimension == "Performance Comercial":
        st.markdown("## Performance Comercial Cenoa")
        
        # Filtros (Añadido 2026 por defecto)
        f1, f2, f3, f4 = st.columns([1, 2, 2, 1.5])
        with f1: anio_sel = st.selectbox("AÑO", ["2026", "2025"])
        
        # Cargamos la data del año que seleccionó el usuario
        df_raw, lista_meses, comp_labels = load_data(anio_sel)
        
        with f2: 
            op_e = [x for x in sorted(df_raw['Empresa'].dropna().unique()) if str(x).upper() != "EMPRESA"]
            sel_emp = st.selectbox("EMPRESA", ["Todas"] + op_e)
        with f3: 
            op_l = [x for x in sorted(df_raw['Localidad'].dropna().unique()) if str(x).upper() != "LOCALIDAD"]
            sel_loc = st.selectbox("LOCALIDAD", ["Todas"] + op_l)
        
        df_p = df_raw.copy()
        if sel_emp != "Todas": df_p = df_p[df_p['Empresa'] == sel_emp]
        if sel_loc != "Todas": df_p = df_p[df_p['Localidad'] == sel_loc]
        with f4: st.metric("VENDEDORES", len(df_p))

        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Cantidad de Operaciones por Empresa**")
            df_m = df_p.groupby('Empresa')[[f"{m}_v" for m in lista_meses]].sum().reset_index().melt(id_vars='Empresa', var_name='Mes', value_name='Ventas')
            df_m['Mes'] = df_m['Mes'].str.replace('_v', '')
            fig_g = px.bar(df_m, x='Mes', y='Ventas', color='Empresa', barmode='group', text_auto='.0f')
            fig_g.update_layout(xaxis=dict(type='category', categoryarray=lista_meses)) 
            st.plotly_chart(fig_g, use_container_width=True)
            
        with c2:
            st.markdown("**Top 10 Asesores (Operaciones)**")
            fig_top = px.bar(df_p.nlargest(10, 'Total_Acumulado'), x='Total_Acumulado', y='Vendedor', orientation='h', text_auto='.0f', color_discrete_sequence=['#e67e22'])
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)

        st.divider()
        col_l, col_r = st.columns([1, 2.5])
        with col_l:
            v_sel = st.selectbox("🔎 Seleccionar Vendedor:", sorted(df_p['Vendedor'].unique()))
            v_data = df_p[df_p['Vendedor'] == v_sel].iloc[0]
        with col_r:
            d1, d2, d3 = st.columns([3, 1, 1])
            with d1:
                st.subheader(v_sel)
                st.markdown(f"<span style='color:#e67e22; font-weight:bold;'>{get_ant(v_data['Fecha_Ingreso'], anio_sel)}</span>", unsafe_allow_html=True)
                st.caption(f"Canal: {v_data['Canal']} | Empresa: {v_data['Empresa']} | Localidad: {v_data['Localidad']}")
            d2.metric("META", int(v_data['Objetivo_Mensual']))
            diff = v_data['Promedio'] - v_data['Objetivo_Mensual']
            d3.metric("PROM", f"{v_data['Promedio']:.1f}", delta=f"{diff:.1f}", delta_color="normal" if diff >= 0 else "inverse")
            
            y_vals = [float(v_data[f"{m}_v"]) for m in lista_meses]
            text_vals = [f"{v:.0f}" for v in y_vals]
            fig_evol = go.Figure()
            fig_evol.add_trace(go.Bar(x=lista_meses, y=y_vals, name="Ventas", text=text_vals, textposition='auto', marker_color='#3498db'))
            fig_evol.add_trace(go.Scatter(x=lista_meses, y=[float(v_data['Objetivo_Mensual'])]*12, mode='lines', name="Objetivo", line=dict(color='red', dash='dot', width=3)))
            fig_evol.update_layout(height=300, margin=dict(t=20), xaxis=dict(type='category', categoryorder='array', categoryarray=lista_meses))
            st.plotly_chart(fig_evol, use_container_width=True)

        st.divider()
        g1, g2 = st.columns(2)
        with g1: 
            st.markdown("**Participación por Localidad**")
            st.plotly_chart(px.pie(df_p, values='Total_Acumulado', names='Localidad', hole=0.5), use_container_width=True)
        with g2: 
            st.markdown("**Consistencia de Ventas (Box Plot)**")
            st.plotly_chart(px.box(df_p, x='Empresa', y='Promedio', points="all", color='Empresa', hover_data=['Vendedor']), use_container_width=True)

    # =========================================================
    # DIMENSIÓN 2: MATRIZ 9-BOX
    # =========================================================
    elif dimension == "Matriz 9-Box Comercial":
        st.markdown("## Matriz 9-Box Comercial")
        
        # Agregamos el selector de año en la misma fila superior
        m_f0, m_f1, m_f2, m_f3 = st.columns(4)
        with m_f0: anio_sel9 = st.selectbox("AÑO", ["2026", "2025"])
        
        # Cargamos los datos del año seleccionado
        df_raw, lista_meses, comp_labels = load_data(anio_sel9)
        
        with m_f1: sel_p = st.selectbox("Periodo:", ["Acumulado Anual", "Todos los meses (Promedio)"] + lista_meses)
        with m_f2: f_emp9 = st.selectbox("Empresa", ["Todas"] + sorted(df_raw['Empresa'].dropna().unique()))
        with m_f3: f_loc9 = st.selectbox("Localidad", ["Todas"] + sorted(df_raw['Localidad'].dropna().unique()))

        df_9 = df_raw.copy()
        if f_emp9 != "Todas": df_9 = df_9[df_9['Empresa'] == f_emp9]
        if f_loc9 != "Todas": df_9 = df_9[df_9['Localidad'] == f_loc9]
        
        df_9['X_Axis'] = df_9['Alcance_Total_Anual'] if sel_p in ["Acumulado Anual", "Todos los meses (Promedio)"] else df_9[f"{sel_p}_%"]

        quadrants = {
            "Dilema": ("rgba(255, 198, 26, 0.2)", "🟡", -5, 33.3, 66.6, 110),
            "E. Emergente": ("rgba(144, 238, 144, 0.3)", "🌱", 33.3, 66.6, 66.6, 110),
            "ESTRELLA": ("rgba(46, 204, 113, 0.3)", "🌟", 66.6, 130, 66.6, 110),
            "Cuestionable": ("rgba(243, 156, 18, 0.2)", "🟧", -5, 33.3, 33.3, 66.6),
            "Core Player": ("rgba(189, 195, 199, 0.2)", "⬜", 33.3, 66.6, 33.3, 66.6),
            "High Performer": ("rgba(46, 204, 113, 0.15)", "❇️", 66.6, 130, 33.3, 66.6),
            "Bajo Rendimiento": ("rgba(231, 76, 60, 0.2)", "🟥", -5, 33.3, -5, 33.3),
            "En Riesgo": ("rgba(230, 126, 34, 0.2)", "🟠", 33.3, 66.6, -5, 33.3),
            "Eficaz": ("rgba(39, 174, 96, 0.15)", "🟢", 66.6, 130, -5, 33.3)
        }

        st.write("**Visualizar Listado por Categoría Comercial:**")
        cats = list(quadrants.keys())
        bc1, bc2, bc3 = st.columns(3)
        bc4, bc5, bc6 = st.columns(3)
        bc7, bc8, bc9 = st.columns(3)
        
        if 'cat_filtrada' not in st.session_state: st.session_state.cat_filtrada = None
        
        for i, b_col in enumerate([bc1, bc2, bc3, bc4, bc5, bc6, bc7, bc8, bc9]):
            nombre_cat = cats[i]
            emoji = quadrants[nombre_cat][1]
            if b_col.button(f"{emoji} {nombre_cat}", use_container_width=True): 
                st.session_state.cat_filtrada = nombre_cat

        if st.session_state.cat_filtrada:
            emoji_sel = quadrants[st.session_state.cat_filtrada][1]
            st.markdown(f"#### 📋 Asesores en Categoría: {emoji_sel} {st.session_state.cat_filtrada}")
            
            q_info = quadrants[st.session_state.cat_filtrada]
            df_detalle = df_9[(df_9['X_Axis'] >= q_info[2]) & (df_9['X_Axis'] <= q_info[3]) & 
                              (df_9['Comp_Total_%'] >= q_info[4]) & (df_9['Comp_Total_%'] <= q_info[5])]
            
            st.dataframe(df_detalle[['Vendedor', 'Empresa', 'Localidad', 'X_Axis', 'Comp_Total_%']].rename(columns={'X_Axis': '% Resultados', 'Comp_Total_%': '% Competencias'}), use_container_width=True)
            
            col_cerrar, _ = st.columns([1, 4])
            with col_cerrar:
                if st.button("❌ Cerrar Listado", key="btn_cerrar"):
                    st.session_state.cat_filtrada = None
                    st.rerun() 
            st.divider()

        fig_9 = px.scatter(
            df_9, x='X_Axis', y='Comp_Total_%', text='Iniciales', color='Empresa',
            size='Size_Marker', hover_name='Vendedor',
            range_x=[-5, 130], range_y=[-5, 110],
            labels={'X_Axis': f'% Resultados ({sel_p})', 'Comp_Total_%': '% Competencias'},
            height=650, template="plotly_white"
        )
        fig_9.update_traces(textposition='middle center', textfont=dict(color='white', size=11), marker=dict(opacity=0.9, line=dict(width=1.5, color='DarkSlateGrey')))
        
        for cat, info in quadrants.items():
            fig_9.add_shape(type="rect", x0=info[2], x1=info[3], y0=info[4], y1=info[5], fillcolor=info[0], layer="below", line_width=0)
        
        fig_9.add_vline(x=33.3, line_dash="dash", line_color="rgba(0,0,0,0.3)")
        fig_9.add_vline(x=66.6, line_dash="dash", line_color="rgba(0,0,0,0.3)")
        fig_9.add_hline(y=33.3, line_dash="dash", line_color="rgba(0,0,0,0.3)")
        fig_9.add_hline(y=66.6, line_dash="dash", line_color="rgba(0,0,0,0.3)")

        vendedor_seleccionado = None
        
        if CLICK_HABILITADO:
            st.caption("👈 **Haz click en una esfera** para ver la ficha técnica del vendedor.")
            puntos_click = plotly_events(fig_9, click_event=True, hover_event=False)
            if len(puntos_click) > 0:
                click_x = puntos_click[0]['x']
                click_y = puntos_click[0]['y']
                match = df_9[(df_9['X_Axis'].round(1) == round(click_x, 1)) & (df_9['Comp_Total_%'].round(1) == round(click_y, 1))]
                if not match.empty: vendedor_seleccionado = match.iloc[0]['Vendedor']
        else:
            st.plotly_chart(fig_9, use_container_width=True)
            
        st.divider()
        opciones_vendedores = ["-- Seleccionar Asesor --"] + sorted(df_9['Vendedor'].unique())
        idx_defecto = opciones_vendedores.index(vendedor_seleccionado) if vendedor_seleccionado in opciones_vendedores else 0
        
        st.markdown("### 📋 Ficha Técnica de Desempeño")
        v_ficha = st.selectbox("🔎 Buscador Manual de Asesor:", opciones_vendedores, index=idx_defecto)

        if v_ficha != "-- Seleccionar Asesor --":
            v_f = df_9[df_9['Vendedor'] == v_ficha].iloc[0]
            
            st.markdown(f"""
            <div class='perfil-asesor'>
                <h3 style='margin-bottom: 5px; color: #2c3e50;'>{v_f['Vendedor']}</h3>
                <p style='font-size: 15px; margin-bottom: 0px;'>
                    <b>Antigüedad:</b> <span style='color:#e67e22;'>{get_ant(v_f['Fecha_Ingreso'], anio_sel9)}</span> &nbsp;|&nbsp; 
                    <b>Tipo/Canal:</b> {v_f['Canal']} &nbsp;|&nbsp; 
                    <b>Empresa:</b> {v_f['Empresa']} &nbsp;|&nbsp; 
                    <b>Localidad:</b> {v_f['Localidad']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f"<div class='metric-card'><h2>{v_f['X_Axis']:.1f}%</h2><p>RESULTADOS ({sel_p})</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-card'><h2>{v_f['Comp_Total_%']:.1f}%</h2><p>COMPETENCIAS</p></div>", unsafe_allow_html=True)
            with k3:
                q = "MIEMBRO CLAVE 🌟" if v_f['X_Axis'] >= 66.6 and v_f['Comp_Total_%'] >= 66.6 else "EN DESARROLLO 📈"
                color = "#2ecc71" if "CLAVE" in q else "#e67e22"
                st.markdown(f"<div class='metric-card' style='border-top: 5px solid {color};'><h2 style='color:{color};'>{q}</h2><p>ESTADO ACTUAL</p></div>", unsafe_allow_html=True)

            gl, gr = st.columns([1, 1.5])
            with gl:
                st.markdown("**Desglose de Competencias**")
                comp_pcts = [v_f[c] * 20 for c in comp_labels]
                fig_c = px.bar(x=comp_pcts, y=comp_labels, orientation='h', color=comp_labels, text=[f"{val:.1f}%" for val in comp_pcts])
                fig_c.update_layout(showlegend=False, xaxis_range=[0, max(comp_pcts + [100]) + 10], xaxis_title="Nivel (%)", yaxis_title="") 
                st.plotly_chart(fig_c, use_container_width=True)
            with gr:
                st.markdown("**Evolución mensual % alcance de ventas**")
                alcances = [v_f[f"{m}_%"] for m in lista_meses]
                fig_l = px.line(x=lista_meses, y=alcances, markers=True, text=[f"{val:.0f}%" for val in alcances])
                fig_l.update_traces(line_color='#2ecc71', line_width=4, marker=dict(size=10, color='white', line=dict(width=2, color='#2ecc71')))
                fig_l.update_layout(yaxis_range=[0, max(alcances)+20])
                st.plotly_chart(fig_l, use_container_width=True)

except Exception as e:
    st.error(f"Falla de sistema: {e}")
