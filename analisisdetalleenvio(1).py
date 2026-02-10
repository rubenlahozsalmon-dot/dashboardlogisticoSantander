import streamlit as st
import pandas as pd
import plotly.express as px
import string

# --- CONFIGURACIÓN DEL PANEL ---
st.set_page_config(page_title="Auditoría Logística Last Mile", layout="wide")

st.title("📦 Panel de Control de Calidad de Reparto")
st.markdown("Análisis avanzado de incidencias, entregas y densidad por Código Postal.")

# --- 1. CARGA DE DATOS ---
archivo = st.sidebar.file_uploader("Sube tu reporte Excel (.xlsx)", type=['xlsx'])

if archivo:
    # Definimos nombres de columnas estándar (A-Q)
    column_names = list(string.ascii_uppercase[:17])
    
    try:
        # Leemos el archivo cargado directamente (Sin rutas de Colab)
        df = pd.read_excel(archivo, names=column_names, header=0)
        
        # Limpieza de datos
        df['O_str'] = df['O'].astype(str).str.replace('.0', '', regex=False)
        
        # --- 2. PROCESAMIENTO: LÓGICA DE ÉXITO (ENTREGADO / EFECTIVIDAD) ---
        # Conteo total por repartidor (Columna H)
        repartidor_counts = df['H'].value_counts().reset_index()
        repartidor_counts.columns = ['Repartidor', 'Total_Envios']
        
        # Filtro flexible para Entregas Exitosas (Columna L)
        # Busca ambas palabras sin importar mayúsculas o espacios
        exitos_mask = (
            df['L'].astype(str).str.contains('entregado', na=False, case=False) | 
            df['L'].astype(str).str.contains('efectividad', na=False, case=False)
        )
        df_exitos = df[exitos_mask]
        
        exitos_counts = df_exitos['H'].value_counts().reset_index()
        exitos_counts.columns = ['Repartidor', 'Entregas_Exitosas']
        
        # Unimos las métricas
        resumen = pd.merge(repartidor_counts, exitos_counts, on='Repartidor', how='left').fillna(0)
        resumen['Efectividad_%'] = (resumen['Entregas_Exitosas'] / resumen['Total_Envios'] * 100).round(2)

        # --- 3. DASHBOARD INTERACTIVO ---
        
        # KPIs Superiores
        c1, c2, c3 = st.columns(3)
        c1.metric("Volumen Total", len(df))
        c2.metric("Total Entregados", int(resumen['Entregas_Exitosas'].sum()))
        c3.metric("Efectividad Media", f"{resumen['Efectividad_%'].mean():.1f}%")

        st.divider()

        # GRÁFICO 1: COMPARATIVA VOLUMEN VS ÉXITO
        st.subheader("🏎️ Rendimiento por Repartidor")
        fig_repa = px.bar(
            resumen.sort_values('Total_Envios', ascending=False), 
            x='Repartidor', 
            y=['Total_Envios', 'Entregas_Exitosas'],
            barmode='group',
            color_discrete_map={'Total_Envios': '#34495e', 'Entregas_Exitosas': '#27ae60'},
            text_auto=True
        )
        st.plotly_chart(fig_repa, use_container_width=True)

        # GRÁFICO 2: MAPA DE CALOR DE INCIDENCIAS
        st.subheader("🔥 Mapa de Incidencias (Top 15 Repartidores)")
        incidencias = df.groupby(['H', 'L']).size().reset_index(name='Cantidad')
        top_15 = incidencias.groupby('H')['Cantidad'].sum().nlargest(15).index
        heatmap_data = incidencias[incidencias['H'].isin(top_15)]
        
        fig_heat = px.density_heatmap(
            heatmap_data, x="L", y="H", z="Cantidad",
            color_continuous_scale='YlOrRd', text_auto=True
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # GRÁFICO 3: CORRELACIÓN DENSIDAD
        st.subheader("📍 Correlación: Envíos por Zona vs Repartidor")
        cp_vol = df['O_str'].value_counts().reset_index()
        cp_vol.columns = ['O_str', 'Total_Zona']
        
        corr_data = df.groupby(['H', 'O_str']).size().reset_index(name='Envios_Repa').merge(cp_vol, on='O_str')
        
        fig_corr = px.scatter(
            corr_data, x='Total_Zona', y='Envios_Repa', color='H',
            hover_data=['O_str'], size='Envios_Repa'
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        # TABLA DE DATOS
        with st.expander("Ver Ranking Detallado"):
            st.dataframe(resumen.sort_values('Efectividad_%', ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
        st.info("Revisa que el Excel no tenga filas vacías al principio.")

else:
    st.info("👋 Sube tu archivo Excel en el menú lateral para generar la auditoría.")
