import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string

# 1. CARGA Y PREPARACIÓN DE DATOS
column_names = list(string.ascii_uppercase[:17])
df = pd.read_excel('/content/detalle_envio.xlsx', names=column_names, header=0)
df['O_str'] = df['O'].astype(str).str.replace('.0', '', regex=False)

# 2. ANÁLISIS DE REPARTIDORES (MAYORES/MENORES ENTREGAS)
effective_filter = 'Causa Ajena'
df_effective = df[df['K'] == effective_filter]
repartidor_counts = df_effective['H'].value_counts().reset_index()
repartidor_counts.columns = ['Repartidor', 'Frecuencia']
repartidor_counts['Porcentaje (%)'] = (repartidor_counts['Frecuencia'] / len(df) * 100).round(2)

top_5_max = repartidor_counts.head(5)
top_5_min = repartidor_counts.sort_values(by='Frecuencia', ascending=True).head(5)

# 3. MAPA DE CALOR DE INCIDENCIAS (LO QUE FALTABA)
incidencias_por_repartidor = df.groupby(['H', 'L']).size().reset_index(name='Cantidad_Incidencias')
top_15_drivers = incidencias_por_repartidor.groupby('H')['Cantidad_Incidencias'].sum().nlargest(15).index
heatmap_data = incidencias_por_repartidor[incidencias_por_repartidor['H'].isin(top_15_drivers)]
pivot_heatmap = heatmap_data.pivot(index='H', columns='L', values='Cantidad_Incidencias').fillna(0)

plt.figure(figsize=(16, 10))
sns.heatmap(pivot_heatmap, annot=True, fmt='g', cmap='YlGnBu')
plt.title('Mapa de Calor: Incidencias por Repartidor')
plt.tight_layout()
plt.savefig('heatmap_incidencias.png')

# 4. CORRELACIÓN VOLUMEN VS DENSIDAD
cp_counts = df['O_str'].value_counts().reset_index()
cp_counts.columns = ['Codigo_Postal', 'Envios']
low_perf_drivers = top_5_min['Repartidor'].unique()
df_low_perf = df[df['H'].isin(low_perf_drivers)]
driver_density = df_low_perf.groupby(['H', 'O_str']).size().reset_index(name='Envios_Repartidor')
comparison_df = driver_density.merge(cp_counts, left_on='O_str', right_on='Codigo_Postal', how='left')

plt.figure(figsize=(10, 6))
sns.scatterplot(data=comparison_df, x='Envios', y='Envios_Repartidor', hue='H')
plt.title('Correlación: Volumen vs Densidad de Zona')
plt.savefig('correlacion_densidad.png')

# 5. PRODUCTO DOMINANTE POR CP
dominant_products = df.groupby(['O_str', 'M']).size().reset_index(name='Cantidad')
dominant_per_cp = dominant_products.sort_values(['O_str', 'Cantidad'], ascending=[True, False]).drop_duplicates(subset='O_str')

print('Script completo generado. Se han guardado también los gráficos como imágenes PNG.')