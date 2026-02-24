import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard Enrique Tomás", page_icon="🍖", layout="wide")

# --- DISEÑO UX/UI MEJORADO (CSS) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8fafc; }
        h1, h2, h3, p, div { color: #1e293b; font-family: 'Inter', sans-serif; }
        div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; color: #0f172a !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #64748b !important; font-weight: 600 !important; text-transform: uppercase; }
        .dataframe { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .section-header { padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; margin-bottom: 1rem; margin-top: 2rem; color: #334155; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_numeros(valor):
    """Convierte textos del Excel a números matemáticos."""
    if isinstance(valor, str):
        valor = valor.replace('$', '').replace(',', '').strip()
    try:
        return float(valor)
    except:
        return 0.0

# --- BARRA LATERAL ---
st.sidebar.header("📁 Carga de Reportes")
st.sidebar.markdown("Subí tus Excel exportados de MaxiRest. **(Fila 1 deben ser títulos)**")
file_articulos = st.sidebar.file_uploader("1. Ventas por Artículo", type=["csv", "xlsx", "xls"])
file_concepto = st.sidebar.file_uploader("2. Ventas Mensuales", type=["csv", "xlsx", "xls"])

if file_articulos and file_concepto:
    try:
        # LECTURA DE DATOS
        df_art = pd.read_csv(file_articulos) if file_articulos.name.endswith('.csv') else pd.read_excel(file_articulos)
        df_mes = pd.read_csv(file_concepto) if file_concepto.name.endswith('.csv') else pd.read_excel(file_concepto)

        # LIMPIEZA DE COLUMNAS
        df_art.columns = df_art.columns.astype(str).str.strip().str.lower().str.replace('ó', 'o').str.replace('í', 'i')
        df_mes.columns = df_mes.columns.astype(str).str.strip().str.lower().str.replace('ó', 'o').str.replace('í', 'i')

        if 'nombre' in df_art.columns: df_art.rename(columns={'nombre': 'producto'}, inplace=True)
        if 'venta' in df_art.columns: df_art.rename(columns={'venta': 'ventas'}, inplace=True)
        if 'rubro' not in df_art.columns: df_art['rubro'] = 'S/D'

        if 'fecha' in df_mes.columns: df_mes.rename(columns={'fecha': 'mes'}, inplace=True)
        if 'salón' in df_mes.columns: df_mes.rename(columns={'salón': 'salon'}, inplace=True)
        if 'ventas' in df_mes.columns and 'tickets' not in df_mes.columns: 
            df_mes.rename(columns={'ventas': 'tickets'}, inplace=True)

        # --- TRADUCTOR DE RUBROS INFALIBLE ---
        diccionario_rubros = {
            "1": "Cafetería", "2": "Entradas", "3": "Postres", "4": "Tapas", 
            "5": "Platos Principales", "6": "Sándwiches", "7": "Embutidos", 
            "8": "Combos", "9": "Venta por Kg", "10": "Fiambres", "11": "Sobres",
            "12": "Tablas", "13": "Quesos", "14": "Ensaladas", "15": "Adicionales",
            "16": "Tragos", "17": "Bebidas C/A", "18": "Cervezas", "19": "Bebidas S/A",
            "20": "Conservas", "21": "Tienda", "22": "Vinos Tintos", "23": "Vinos Blancos",
            "24": "Vinos Rosados", "25": "Espumantes", "26": "Vermut", "27": "Raciones"
        }
        # Limpiamos el valor para asegurarnos de que sea puro texto sin decimales
        df_art['rubro_limpio'] = df_art['rubro'].astype(str).str.replace('.0', '', regex=False).str.strip()
        df_art['rubro'] = df_art['rubro_limpio'].map(diccionario_rubros).fillna(df_art['rubro'])

        # Limpiamos los valores numéricos
        df_art['unidades'] = df_art['unidades'].apply(limpiar_numeros)
        df_art['ventas'] = df_art['ventas'].apply(limpiar_numeros)
        df_mes['salon'] = df_mes['salon'].apply(limpiar_numeros)
        df_mes['mostrador'] = df_mes['mostrador'].apply(limpiar_numeros)
        
        if 'tickets' in df_mes.columns:
            df_mes['tickets'] = df_mes['tickets'].apply(limpiar_numeros)
        else:
            df_mes['tickets'] = 1 

        df_art = df_art[df_art['unidades'] > 0].copy()
        df_art['precio_promedio'] = df_art['ventas'] / df_art['unidades']
        
        # CÁLCULOS TOTALES
        facturacion_total = df_art['ventas'].sum()
        unidades_totales = df_art['unidades'].sum()
        total_salon = df_mes['salon'].sum()
        total_mostrador = df_mes['mostrador'].sum()
        tickets_totales = df_mes['tickets'].sum()

        # --- ENCABEZADO Y FACTURACIÓN TOTAL ---
        col_titulo, col_facturacion = st.columns([3, 1])
        with col_titulo:
            st.markdown("<h1 style='color: #0f172a; margin-bottom: 0;'>Reporte Analítico Estratégico 360°</h1>", unsafe_allow_html=True)
            st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>Enrique Tomás - Análisis de Rendimiento Comercial</p>", unsafe_allow_html=True)
        with col_facturacion:
            st.metric("Facturación Total Bruta", f"${facturacion_total:,.2f}")
        
        # --- KPIs ---
        st.markdown("<h3 class='section-header'>Métricas Principales</h3>", unsafe_allow_html=True)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Venta Mostrador", f"${total_mostrador:,.0f}", f"{(total_mostrador/facturacion_total)*100:.1f}%")
        kpi2.metric("Venta Salón", f"${total_salon:,.0f}", f"{(total_salon/facturacion_total)*100:.1f}%")
        
        ticket_prom = (facturacion_total/tickets_totales) if tickets_totales > 0 else 0
        upt = (unidades_totales/tickets_totales) if tickets_totales > 0 else 0
        
        kpi3.metric("Ticket Promedio Anual", f"${ticket_prom:,.0f}", f"{tickets_totales:,.0f} Tickets")
        kpi4.metric("Índice Venta Cruzada (UPT)", f"{upt:.2f}", "Art./Ticket")

        # --- FILA 1 DE GRÁFICOS ---
        st.markdown("<h3 class='section-header'>Evolución Mensual</h3>", unsafe_allow_html=True)
        df_mes['facturacion_mensual'] = df_mes['salon'] + df_mes['mostrador']
        df_mes['ticket_prom_mes'] = df_mes['facturacion_mensual'] / df_mes['tickets'].replace(0, 1)

        col1, col2 = st.columns(2)
        with col1:
            fig_mensual = make_subplots(specs=[[{"secondary_y": True}]])
            fig_mensual.add_trace(go.Bar(x=df_mes['mes'], y=df_mes['facturacion_mensual'], name="Facturación", marker_color='#3B82F6'), secondary_y=False)
            fig_mensual.add_trace(go.Scatter(x=df_mes['mes'], y=df_mes['tickets'], name="Tickets", marker_color='#F59E0B', mode='lines+markers', line=dict(width=3)), secondary_y=True)
            fig_mensual.update_layout(title="Facturación vs Tickets", margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_mensual, use_container_width=True)

        with col2:
            fig_ticket = px.line(df_mes, x='mes', y='ticket_prom_mes', markers=True, title="Ticket Promedio Mensual ($)")
            fig_ticket.update_traces(line_color='#10B981', line_width=3, marker=dict(size=8))
            fig_ticket.update_layout(margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_ticket, use_container_width=True)

        # --- FILA 2 DE GRÁFICOS ---
        st.markdown("<h3 class='section-header'>Análisis de Canales e Inventario ABC</h3>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            df_mes['% Salon'] = (df_mes['salon'] / df_mes['facturacion_mensual'].replace(0, 1)) * 100
            df_mes['% Mostrador'] = (df_mes['mostrador'] / df_mes['facturacion_mensual'].replace(0, 1)) * 100
            fig_canales = go.Figure(data=[
                go.Bar(name='Mostrador', x=df_mes['mes'], y=df_mes['% Mostrador'], marker_color='#8B5CF6'),
                go.Bar(name='Salón', x=df_mes['mes'], y=df_mes['% Salon'], marker_color='#6366F1')
            ])
            fig_canales.update_layout(barmode='stack', title="Mix de Canales (%)", margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_canales, use_container_width=True)

        with col4:
            df_abc = df_art.sort_values(by='ventas', ascending=False).copy()
            df_abc['cumsum'] = df_abc['ventas'].cumsum()
            df_abc['cumperc'] = (df_abc['cumsum'] / facturacion_total) * 100

            def clasificar_abc(perc):
                if perc <= 80: return 'A'
                elif perc <= 95: return 'B'
                else: return 'C'
                
            df_abc['clase'] = df_abc['cumperc'].apply(clasificar_abc)
            resumen_abc = df_abc.groupby('clase').agg(Productos=('producto', 'count'), Facturacion=('ventas', 'sum')).reset_index()

            sub_col_a, sub_col_b = st.columns([1, 1.5])
            with sub_col_a:
                fig_abc = px.pie(resumen_abc, values='Productos', names='clase', hole=0.6, color='clase',
                                 title="Matriz ABC", color_discrete_map={'A':'#10B981', 'B':'#F59E0B', 'C':'#EF4444'})
                fig_abc.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_abc, use_container_width=True)
            with sub_col_b:
                resumen_abc['Clase Info'] = resumen_abc['clase'].map({'A': 'A (80% Ingresos)', 'B': 'B (15% Ingresos)', 'C': 'C (5% Ingresos)'})
                st.dataframe(resumen_abc[['Clase Info', 'Productos', 'Facturacion']].style.format({"Facturacion": "${:,.2f}"}), use_container_width=True, hide_index=True)

        # --- TABLAS DETALLADAS ---
        st.markdown("<h3 class='section-header'>Motores del Negocio: Top 20 Global</h3>", unsafe_allow_html=True)
        top_20 = df_abc[df_abc['clase'] == 'A'].head(20)[['producto', 'rubro', 'unidades', 'precio_promedio', 'ventas']]
        st.dataframe(top_20.style.format({"ventas": "${:,.2f}", "precio_promedio": "${:,.2f}", "unidades": "{:,.1f}"}), use_container_width=True, hide_index=True)

        st.markdown("<h3 class='section-header'>Desglose Profundo: Top 10 por Rubro Principal</h3>", unsafe_allow_html=True)
        top_3_rubros = df_art[df_art['rubro'] != 'S/D'].groupby('rubro')['ventas'].sum().nlargest(3).index.tolist()
        
        cols_rubros = st.columns(3)
        for idx, rubro in enumerate(top_3_rubros):
            with cols_rubros[idx]:
                st.markdown(f"**{idx+1}. {rubro}**")
                df_filtrado = df_art[df_art['rubro'] == rubro].sort_values(by='ventas', ascending=False).head(10)
                st.dataframe(df_filtrado[['producto', 'ventas']].style.format({"ventas": "${:,.0f}"}), use_container_width=True, hide_index=True)

        st.markdown("<h3 class='section-header'>☠️ El 'Cementerio' de Stock (1 Unidad Vendida)</h3>", unsafe_allow_html=True)
        cementerio = df_art[df_art['unidades'] <= 1.0].sort_values(by='ventas', ascending=False)[['producto', 'rubro', 'ventas']]
        st.dataframe(cementerio.head(15).style.format({"ventas": "${:,.2f}"}), use_container_width=True, hide_index=True)

        st.markdown("<h3 class='section-header'>📋 Anexo: Catálogo 'Clase A' Completo</h3>", unsafe_allow_html=True)
        st.markdown("Los productos que sostienen el **80% de tu facturación**. Esta es la mercadería que **nunca debe faltar** en el local.")
        clase_a_completa = df_abc[df_abc['clase'] == 'A'][['producto', 'rubro', 'ventas']]
        st.dataframe(clase_a_completa.style.format({"ventas": "${:,.2f}"}), use_container_width=True, hide_index=True, height=400)

    except Exception as e:
        st.error(f"Error procesando los datos. Verificá que la FILA 1 de tus Excel tenga solo los nombres de las columnas. Detalle técnico: {e}")

else:
    st.info("👋 ¡Hola! Por favor subí tus archivos Excel o CSV en la barra lateral para ver el panel interactivo.")