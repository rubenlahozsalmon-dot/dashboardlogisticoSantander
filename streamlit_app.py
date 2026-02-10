import streamlit as st
import pandas as pd
import string
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title='Dashboard Logístico', layout='wide')
st.title('📊 Dashboard de Auditoría Logística')

# --- CARGA DE ARCHIVO Y FILTROS ---
st.sidebar.header('Configuración')
uploaded_file = st.sidebar.file_uploader('Cargar archivo Excel (detalle_envio.xlsx)', type=['xlsx'])

# Filtro de cantidad para los rankings
top_n = st.sidebar.slider('Seleccionar Top para Rankings', min_value=3, max_value=20, value=5)

if uploaded_file is not None:
    # 1. Preparación de datos
    column_names = list(string.ascii_uppercase[:17])
    df = pd.read_excel(uploaded_file, names=column_names, header=0)
    
    # Limpieza robusta de CP (Columna O)
    df['CP_Limpio'] = df['O'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    # Filtro flexible de éxito
    mask_exito = (df['L'].astype(str).str.contains('entregado', case=False, na=False) | 
                  df['L'].astype(str).str.contains('efectividad', case=False, na=False))
    
    # --- MÉTRICAS GLOBALES ---
    total_envios = len(df)
    total_exitos = len(df[mask_exito])
    efectividad_global = (total_exitos / total_envios * 100) if total_envios > 0 else 0

    st.markdown('### 📈 Resumen Operativo Global')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Envíos', f"{total_envios} env.")
    c2.metric('Envíos Entregados', f"{total_exitos} env.")
    c3.metric('Efectividad Global', f"{efectividad_global:.1f}%")
    st.progress(efectividad_global / 100)
    st.divider()

    tab1, tab2, tab3 = st.tabs(['🚚 Repartidores', '📍 Geografía (CP)', '⚠️ Incidencias'])

    with tab1:
        st.subheader('Rendimiento por Repartidor')
        rep_total = df['H'].value_counts().reset_index()
        rep_total.columns = ['Repartidor', 'Total']
        rep_exitos = df[mask_exito]['H'].value_counts().reset_index()
        rep_exitos.columns = ['Repartidor', 'Exitos']
        resumen_repa = pd.merge(rep_total, rep_exitos, on='Repartidor', how='left').fillna(0)
        resumen_repa['% Efectividad'] = (resumen_repa['Exitos'] / resumen_repa['Total'] * 100).round(1)
        resumen_repa['% Incidencias'] = (100 - resumen_repa['% Efectividad']).round(1)
        st.dataframe(resumen_repa.sort_values('% Efectividad', ascending=False), use_container_width=True)

    with tab2:
        st.subheader('📍 Distribución de Envíos por CP')
        # Arreglo del conteo de CP
        cp_df = df['CP_Limpio'].value_counts().reset_index()
        cp_df.columns = ['CP', 'Cantidad']
        
        # Cálculo de porcentaje sobre el total
        cp_df['Porcentaje'] = (cp_df['Cantidad'] / total_envios * 100).round(1)
        
        # Usamos el filtro 'top_n' también para los CP para que sea coherente
        cp_plot_data = cp_df.head(top_n)

        # Gráfico de Plotly arreglado
        fig_cp = px.bar(
            cp_plot_data, 
            x='CP', 
            y='Cantidad',
            text=cp_plot_data['Porcentaje'].apply(lambda x: f'{x}%'),
            color='Cantidad',
            color_continuous_scale='Blues',
            labels={'CP': 'Código Postal', 'Cantidad': 'Nº de Envíos'}
        )
        
        fig_cp.update_traces(textposition='outside')
        fig_cp.update_layout(xaxis_type='category') # Asegura que el CP se vea como etiqueta
        
        st.plotly_chart(fig_cp, use_container_width=True)
        st.write(f"Mostrando los {top_n} códigos postales con más actividad.")

    with tab3:
        st.subheader(f'🔥 Análisis de Extremos (Top {top_n})')
        inc_data = df.groupby(['H', 'L']).size().reset_index(name='Count')
        pivot_inc = inc_data.pivot(index='H', columns='L', values='Count').fillna(0)
        col_exito = next((c for c in pivot_inc.columns if "entregado" in str(c).lower() or "efectividad" in str(c).lower()), None)
        rep_stats = resumen_repa.set_index('Repartidor')[['% Efectividad', '% Incidencias']]
        full_pivot = pivot_inc.merge(rep_stats, left_index=True, right_index=True, how='left').fillna(0)
        
        cols_verdes = ['% Efectividad'] + ([col_exito] if col_exito else [])
        cols_rojas = ['% Incidencias'] + [c for c in pivot_inc.columns if c != col_exito]
        inc_reales = [c for c in pivot_inc.columns if c != col_exito]
        full_pivot['Total_Inc_Count'] = full_pivot[inc_reales].sum(axis=1)
        orden_final_cols = cols_verdes + cols_rojas
        
        col_peores, col_mejores = st.columns(2)
        def draw_split_heatmap(data, title, ax):
            sns.heatmap(data[cols_rojas], annot=True, fmt='g', cmap='YlOrRd', ax=ax, cbar=False, linewidths=.5)
            sns.heatmap(data[cols_verdes], annot=True, fmt='g', cmap='Greens', ax=ax, cbar=False, linewidths=.5)
            ax.set_title(title)
            plt.xticks(rotation=45, ha='right')

        with col_peores:
            peores_df = full_pivot.sort_values('Total_Inc_Count', ascending=False).head(top_n)[orden_final_cols]
            fig_p, ax_p = plt.subplots(figsize=(10, 6))
            draw_split_heatmap(peores_df, f"Top {top_n} MÁS Incidencias", ax_p)
            st.pyplot(fig_p)

        with col_mejores:
            mejores_df = full_pivot.sort_values('Total_Inc_Count', ascending=True).head(top_n)[orden_final_cols]
            fig_m, ax_m = plt.subplots(figsize=(10, 6))
            draw_split_heatmap(mejores_df, f"Top {top_n} MENOS Incidencias", ax_m)
            st.pyplot(fig_m)

else:
    st.info('👋 Sube el archivo Excel para activar la herramienta.')

