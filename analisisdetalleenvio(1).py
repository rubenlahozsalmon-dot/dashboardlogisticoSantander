import streamlit as st
import pandas as pd
import plotly.express as px
import string

# --- 0. CONFIGURACIÓN DEL PANEL ---
st.set_page_config(page_title="Auditoría Logística Last Mile", layout="wide")

st.title("📦 Panel de Control de Calidad de Reparto")
st.markdown("Análisis avanzado de incidencias, entregas y densidad por Código Postal.")

# --- 1. CARGA DE DATOS (CORREGIDO) ---
# Se elimina la ruta fija '/content/' para usar el cargador de archivos de Streamlit
archivo = st.sidebar.file_uploader("Sube tu reporte Excel (.xlsx)", type=['xlsx'])

if archivo:
    # Definimos nombres de columnas estándar (A-Q) para evitar errores de nombres cambiantes
    column_names = list(string.ascii_uppercase[:17])
    
    try:
        # Leemos el archivo cargado directamente
        df = pd.read_excel(archivo, names=column_names, header=0)
        
        # Limpieza de Códigos Postales
        df['O_str'] = df['O'].astype(str).str.replace('.0', '', regex=False)
        
        # --- 2. PROCESAMIENTO: LÓGICA DE ÉXITO (ENTREGADO / EFECTIVIDAD) ---
        # H = Repartidor | L = Motivo de Situación | K = Estatus
        
        # Conteo total de envíos por repartidor
        repartidor_counts = df['H'].value_counts().reset_index()
        repartidor_counts.columns = ['Repartidor', 'Total_Envios']
        
        # Filtro flexible: buscamos 'entregado' O 'efectividad' en la columna L
        # Esto soluciona el problema de que el éxito se llame de dos formas distintas
        exitos_mask = (
            df['L'].astype(str).str.contains('entregado', na=False, case=False) | 
            df['L'].astype(str).str.contains('efectividad', na=False, case=False)
        )
        df_exitos = df[exitos_mask]
        
        exitos_counts = df_exitos['H'].value_counts().reset_index()
        exitos_counts.columns = ['Repartidor', 'Entregas_Exitosas']
        
        # Unión de datos (Merge) y cálculo de Efectividad % (Línea 37 corregida)
        resumen = pd.merge(repartidor_counts, exitos_counts, on='Repartidor', how='left').fillna(0)
        resumen['Efectividad_%'] = (resumen['Entregas_Exitosas'] / resumen['Total_Envios'] * 100).round(2)

        # --- 3. DASHBOARD INTERACTIVO ---
        
        # KPIs Superiores
        c1, c2, c3 = st.columns(3)
        c1.metric("Volumen Total", len(df))
        c2.metric("Total Entregados", int(resumen['Entregas_Exitosas'].sum()))
        c3.metric("Efectividad Media", f"{resumen['Efectividad_%'].mean():.1f}%")

        st.divider()

        # GRÁFICO 1: COMPARATIVA RENDIMIENTO (PLOTLY INTERACTIVO)
        st.subheader("🏎️ Rendimiento por Repartidor")
        fig_repa = px.bar(
            resumen.sort_values('Total_Envios', ascending=False), 
            x='Repartidor', 
            y=['Total_Envios', 'Entregas_Exitosas'],
            barmode='group',
            labels={'value': 'Paquetes', 'variable': 'Categoría'},
            color_discrete_map={'Total_Envios': '#34495e', 'Entregas_Exitosas': '#27ae60'},
            text_auto=True
        )
        st.plotly_chart(fig_repa, use_container_width=True)

        # GRÁFICO 2: MAPA DE CALOR DE INCIDENCIAS
        st.subheader("🔥 Mapa de Incidencias Críticas (Top 15 Repartidores)")
        incidencias = df.groupby(['H', 'L']).size().reset_index(name='Cantidad')
        top_15_drivers = incidencias.groupby('H')['Cantidad'].sum().nlargest(15).index
        heatmap_data = incidencias[incidencias['H'].isin(top_15_drivers)]
        
        fig_heat = px.density_heatmap(
            heatmap_data, x="L", y="H", z="Cantidad",
            color_continuous_scale='YlOrRd', text_auto=True,
            labels={'L': 'Motivo', 'H': 'Repartidor'}
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # TABLA DE DATOS DETALLADA
        with st.expander("📋 Ver Ranking Detallado de Repartidores"):
            st.dataframe(resumen.sort_values('Efectividad_%', ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
else:
    st.info("👋 Sube tu archivo Excel en la barra lateral para comenzar.")
