import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard Gerencial | Enrique Tomás", page_icon="🍖", layout="wide")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp { background-color: #F3F2F1; }
        html, body, [class*="css"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; }
        div[data-testid="stMetric"] { background-color: #FFFFFF; padding: 15px 15px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); border-left: 5px solid #118DFF; }
        div[data-testid="stMetricLabel"] { color: #605E5C !important; font-size: 13px !important; font-weight: 600 !important; text-transform: uppercase; }
        div[data-testid="stMetricValue"] { color: #252423 !important; font-size: 22px !important; font-weight: 700 !important; }
        div[data-testid="stMetricDelta"] svg { display: none !important; }
        .pbi-title { color: #252423; font-size: 22px; font-weight: 600; margin-top: 35px; margin-bottom: 15px; border-bottom: 2px solid #C8C6C4; padding-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE LIMPIEZA MAESTRA ---
def limpiar_numeros(valor):
    if isinstance(valor, str): valor = valor.replace('$', '').replace(',', '').strip()
    try: return float(valor)
    except: return 0.0

def procesar_archivos(file_articulos, file_concepto, nombre_sucursal):
    """Esta es la 'máquina' que limpia los Excel de cualquier sucursal que le pasemos"""
    df_art = pd.read_csv(file_articulos) if file_articulos.name.endswith('.csv') else pd.read_excel(file_articulos)
    df_mes = pd.read_csv(file_concepto) if file_concepto.name.endswith('.csv') else pd.read_excel(file_concepto)

    df_art.columns = df_art.columns.astype(str).str.strip().str.lower().str.replace('ó', 'o').str.replace('í', 'i')
    df_mes.columns = df_mes.columns.astype(str).str.strip().str.lower().str.replace('ó', 'o').str.replace('í', 'i')

    if 'nombre' in df_art.columns: df_art.rename(columns={'nombre': 'producto'}, inplace=True)
    if 'venta' in df_art.columns: df_art.rename(columns={'venta': 'ventas'}, inplace=True)
    if 'rubro' not in df_art.columns: df_art['rubro'] = 'S/D'

    if 'fecha' in df_mes.columns: df_mes.rename(columns={'fecha': 'mes'}, inplace=True)
    if 'salón' in df_mes.columns: df_mes.rename(columns={'salón': 'salon'}, inplace=True)
    if 'ventas' in df_mes.columns and 'tickets' not in df_mes.columns: df_mes.rename(columns={'ventas': 'tickets'}, inplace=True)

    diccionario_rubros = {
        "1": "Cafetería", "2": "Entradas", "3": "Postres", "4": "Tapas", "5": "Platos Principales", "6": "Sándwiches", 
        "7": "Embutidos", "8": "Combos", "9": "Venta por Kg", "10": "Fiambres", "11": "Sobres", "12": "Tablas", 
        "13": "Quesos", "14": "Ensaladas", "15": "Adicionales", "16": "Tragos", "17": "Bebidas C/A", "18": "Cervezas", 
        "19": "Bebidas S/A", "20": "Conservas", "21": "Tienda", "22": "Vinos Tintos", "23": "Vinos Blancos", "24": "Vinos Rosados", 
        "25": "Espumantes", "26": "Vermut", "27": "Raciones"
    }
    df_art['rubro_limpio'] = df_art['rubro'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_art['rubro'] = df_art['rubro_limpio'].map(diccionario_rubros).fillna(df_art['rubro'])

    df_art['unidades'] = df_art['unidades'].apply(limpiar_numeros)
    df_art['ventas'] = df_art['ventas'].apply(limpiar_numeros)
    df_mes['salon'] = df_mes['salon'].apply(limpiar_numeros)
    df_mes['mostrador'] = df_mes['mostrador'].apply(limpiar_numeros)
    if 'tickets' in df_mes.columns: df_mes['tickets'] = df_mes['tickets'].apply(limpiar_numeros)
    else: df_mes['tickets'] = 1 

    df_art['sucursal'] = nombre_sucursal
    df_mes['sucursal'] = nombre_sucursal
    
    return df_art, df_mes

# --- BARRA LATERAL MULTI-SUCURSAL ---
with st.sidebar:
    st.markdown("### 👁️ Vista de Datos")
    vista_seleccionada = st.radio("Seleccione qué datos visualizar:", ["Consolidado (Ambas)", "Local 1", "Local 2"])
    
    st.markdown("---")
    st.markdown("### 🏪 Local 1")
    file_art_1 = st.file_uploader("Artículos (Local 1)", type=["csv", "xlsx", "xls"], key="a1")
    file_mes_1 = st.file_uploader("Mensuales (Local 1)", type=["csv", "xlsx", "xls"], key="m1")

    st.markdown("---")
    st.markdown("### 🏪 Local 2")
    file_art_2 = st.file_uploader("Artículos (Local 2)", type=["csv", "xlsx", "xls"], key="a2")
    file_mes_2 = st.file_uploader("Mensuales (Local 2)", type=["csv", "xlsx", "xls"], key="m2")

# --- LÓGICA DE FUSIÓN Y FILTRADO ---
dfs_art = []
dfs_mes = []

try:
    # Leemos lo que se haya subido
    if file_art_1 and file_mes_1:
        a1, m1 = procesar_archivos(file_art_1, file_mes_1, "Local 1")
        dfs_art.append(a1)
        dfs_mes.append(m1)

    if file_art_2 and file_mes_2:
        a2, m2 = procesar_archivos(file_art_2, file_mes_2, "Local 2")
        dfs_art.append(a2)
        dfs_mes.append(m2)

    # Si hay al menos un local cargado, empezamos a armar el tablero
    if dfs_art and dfs_mes:
        # Juntamos todo en un "Mega Excel" invisible
        df_art_master = pd.concat(dfs_art, ignore_index=True)
        df_mes_master = pd.concat(dfs_mes, ignore_index=True)

        # Filtramos según lo que eligió el usuario en el botón de opciones
        if vista_seleccionada == "Local 1" and file_art_1:
            df_art = df_art_master[df_art_master['sucursal'] == "Local 1"].copy()
            df_mes = df_mes_master[df_mes_master['sucursal'] == "Local 1"].copy()
            titulo_sucursal = "Local 1"
        
        elif vista_seleccionada == "Local 2" and file_art_2:
            df_art = df_art_master[df_art_master['sucursal'] == "Local 2"].copy()
            df_mes = df_mes_master[df_mes_master['sucursal'] == "Local 2"].copy()
            titulo_sucursal = "Local 2"
        
        elif vista_seleccionada == "Consolidado (Ambas)" and len(dfs_art) == 2:
            # Agrupamos y sumamos matemáticamente ambas sucursales
            df_art = df_art_master.groupby(['producto', 'rubro'], as_index=False)[['unidades', 'ventas']].sum()
            df_mes = df_mes_master.groupby('mes', as_index=False)[['salon', 'mostrador', 'tickets']].sum()
            titulo_sucursal = "Consolidado Global"
        else:
            st.warning("⚠️ Faltan cargar archivos para mostrar la vista seleccionada. Asegúrese de subir los Excel necesarios para esta vista.")
            st.stop()

        # PREPARACIÓN FINAL DE DATOS
        df_art = df_art[df_art['unidades'] > 0].copy()
        df_art['precio_promedio'] = df_art['ventas'] / df_art['unidades']
        
        facturacion_total = df_art['ventas'].sum()
        unidades_totales = df_art['unidades'].sum()
        total_salon = df_mes['salon'].sum()
        total_mostrador = df_mes['mostrador'].sum()
        tickets_totales = df_mes['tickets'].sum()

        # --- RENDERIZADO VISUAL ---
        st.markdown(f"<h1 style='color: #252423; font-size: 32px; font-weight: 700;'>Reporte Ejecutivo: {titulo_sucursal}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #605E5C; margin-top: -15px; margin-bottom: 30px;'>Enrique Tomás - Análisis comercial detallado</p>", unsafe_allow_html=True)
        
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns([1.2, 1.2, 1.2, 0.9, 0.9])
        kpi1.metric("Facturación Bruta", f"${facturacion_total:,.0f}")
        kpi2.metric("Venta Mostrador", f"${total_mostrador:,.0f}", f"{(total_mostrador/facturacion_total)*100:.1f}% del total", delta_color="off")
        kpi3.metric("Venta Salón", f"${total_salon:,.0f}", f"{(total_salon/facturacion_total)*100:.1f}% del total", delta_color="off")
        
        ticket_prom = (facturacion_total/tickets_totales) if tickets_totales > 0 else 0
        upt = (unidades_totales/tickets_totales) if tickets_totales > 0 else 0
        kpi4.metric("Ticket Promedio", f"${ticket_prom:,.0f}", f"{tickets_totales:,.0f} Tks", delta_color="off")
        kpi5.metric("Venta Cruzada (UPT)", f"{upt:.2f}", "Art./Ticket", delta_color="off")

        st.markdown("<div class='pbi-title'>Rendimiento Mensual y Tendencias</div>", unsafe_allow_html=True)
        df_mes['facturacion_mensual'] = df_mes['salon'] + df_mes['mostrador']
        df_mes['ticket_prom_mes'] = df_mes['facturacion_mensual'] / df_mes['tickets'].replace(0, 1)

        col1, col2 = st.columns(2)
        with col1:
            fig_mensual = make_subplots(specs=[[{"secondary_y": True}]])
            fig_mensual.add_trace(go.Bar(x=df_mes['mes'], y=df_mes['facturacion_mensual'], name="Facturación", marker_color='#118DFF'), secondary_y=False)
            fig_mensual.add_trace(go.Scatter(x=df_mes['mes'], y=df_mes['tickets'], name="Tickets", marker_color='#F2C80F', mode='lines+markers', line=dict(width=3)), secondary_y=True)
            fig_mensual.update_layout(title="Facturación vs Cantidad de Tickets", margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_mensual, use_container_width=True)

        with col2:
            fig_ticket = px.line(df_mes, x='mes', y='ticket_prom_mes', markers=True, title="Evolución del Ticket Promedio ($)")
            fig_ticket.update_traces(line_color='#01B8AA', line_width=3, marker=dict(size=8))
            fig_ticket.update_layout(margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_ticket, use_container_width=True)

        st.markdown("<div class='pbi-title'>Composición del Negocio e Inventario ABC</div>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            df_mes['% Salon'] = (df_mes['salon'] / df_mes['facturacion_mensual'].replace(0, 1)) * 100
            df_mes['% Mostrador'] = (df_mes['mostrador'] / df_mes['facturacion_mensual'].replace(0, 1)) * 100
            fig_canales = go.Figure(data=[
                go.Bar(name='Mostrador', x=df_mes['mes'], y=df_mes['% Mostrador'], marker_color='#118DFF'),
                go.Bar(name='Salón', x=df_mes['mes'], y=df_mes['% Salon'], marker_color='#374649')
            ])
            fig_canales.update_layout(barmode='stack', title="Mix de Canales de Venta (%)", margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_canales, use_container_width=True)

        with col4:
            df_abc = df_art.sort_values(by='ventas', ascending=False).copy()
            df_abc['cumsum'] = df_abc['ventas'].cumsum()
            df_abc['cumperc'] = (df_abc['cumsum'] / facturacion_total) * 100
            df_abc['clase'] = df_abc['cumperc'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            resumen_abc = df_abc.groupby('clase').agg(Productos=('producto', 'count'), Facturacion=('ventas', 'sum')).reset_index()

            sub_col_a, sub_col_b = st.columns([1, 1.5])
            with sub_col_a:
                fig_abc = px.pie(resumen_abc, values='Productos', names='clase', hole=0.6, color='clase', color_discrete_map={'A':'#01B8AA', 'B':'#F2C80F', 'C':'#FD625E'})
                fig_abc.update_layout(margin=dict(l=0, r=0, t=40, b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_abc, use_container_width=True)
            with sub_col_b:
                st.markdown("<br><br>", unsafe_allow_html=True)
                resumen_abc['Clasificación'] = resumen_abc['clase'].map({'A': 'A (80% Ingresos)', 'B': 'B (15% Ingresos)', 'C': 'C (5% Ingresos)'})
                st.dataframe(resumen_abc[['Clasificación', 'Productos', 'Facturacion']].style.format({"Facturacion": "${:,.2f}"}), use_container_width=True, hide_index=True)

        st.markdown("<div class='pbi-title'>🏆 Motores del Negocio: Top 20 Global</div>", unsafe_allow_html=True)
        top_20 = df_abc[df_abc['clase'] == 'A'].head(20)[['producto', 'rubro', 'unidades', 'precio_promedio', 'ventas']]
        st.dataframe(top_20.style.format({"ventas": "${:,.2f}", "precio_promedio": "${:,.2f}", "unidades": "{:,.1f}"}), use_container_width=True, hide_index=True)

        st.markdown("<div class='pbi-title'>🔍 Desglose Profundo: Top 10 por Rubro Principal</div>", unsafe_allow_html=True)
        top_3_rubros = df_art[df_art['rubro'] != 'S/D'].groupby('rubro')['ventas'].sum().nlargest(3).index.tolist()
        cols_rubros = st.columns(3)
        for idx, rubro in enumerate(top_3_rubros):
            with cols_rubros[idx]:
                st.markdown(f"**{idx+1}. {rubro}**")
                df_filtrado = df_art[df_art['rubro'] == rubro].sort_values(by='ventas', ascending=False).head(10)
                st.dataframe(df_filtrado[['producto', 'ventas']].style.format({"ventas": "${:,.0f}"}), use_container_width=True, hide_index=True)

        st.markdown("<div class='pbi-title'>☠️ El 'Cementerio' de Stock (1 Unidad o menos vendida)</div>", unsafe_allow_html=True)
        cementerio = df_art[df_art['unidades'] <= 1.0].sort_values(by='ventas', ascending=False)[['producto', 'rubro', 'ventas']]
        st.dataframe(cementerio.head(15).style.format({"ventas": "${:,.2f}"}), use_container_width=True, hide_index=True)

        st.markdown("<div class='pbi-title'>📋 Anexo: Catálogo 'Clase A' Completo</div>", unsafe_allow_html=True)
        clase_a_completa = df_abc[df_abc['clase'] == 'A'][['producto', 'rubro', 'ventas']]
        st.dataframe(clase_a_completa.style.format({"ventas": "${:,.2f}"}), use_container_width=True, hide_index=True, height=400)

except Exception as e:
    st.error(f"Error interno procesando los datos. Asegúrese de cargar los archivos correctos. Detalle técnico: {e}")

if not dfs_art:
    st.info("ℹ️ El panel multi-sucursal está listo. Utilice la barra lateral para cargar los Excel correspondientes.")