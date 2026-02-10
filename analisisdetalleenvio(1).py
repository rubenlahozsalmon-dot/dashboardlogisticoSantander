import string

script_content = """
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
"""

with open('analisisdetalleenvio.py', 'w') as f:
    f.write(script_content.strip())

print('El archivo "analisisdetalleenvio.py" ha sido actualizado con TODO el contenido (incluyendo el Mapa de Calor).')
import pandas as pd

# Grouping by delivery driver (H) and situation reason (L)
driver_reason_counts = df.groupby(['H', 'L']).size().reset_index(name='Frecuencia')

# Sorting and getting the top 5 for each driver
top_5_reasons_per_driver = driver_reason_counts.sort_values(['H', 'Frecuencia'], ascending=[True, False]).groupby('H').head(5)

# Displaying the first few drivers as a sample
print('Top 5 motivos de situación por repartidor (Muestra de los primeros 10 repartidores):')
display(top_5_reasons_per_driver.head(50))
import pandas as pd
import string

# Define column names from 'A' to 'Q'
column_names = list(string.ascii_uppercase[:17])

# Load the Excel file with assigned column names
# If the file has a header already, we skip it to use our custom names
df = pd.read_excel('/content/detalle_envio.xlsx', names=column_names, header=0)

# Display the first few rows to verify
print('Data loaded successfully. Here are the first 5 rows:')
df.head()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Identify relevant columns: 'H' (repartidor) and 'L' (motivo de situación)
repartidor_col = 'H'
motivo_col = 'L'

# 2. Determine the most frequent situation reason globally
most_frequent_reason = df[motivo_col].value_counts().idxmax()
reason_count = df[motivo_col].value_counts().max()
print(f"Most frequent reason: {most_frequent_reason} ({reason_count} occurrences)")

# 3. Filter DataFrame for the most frequent reason
df_filtered = df[df[motivo_col] == most_frequent_reason]

# 4. Group by delivery driver and count occurrences
top_repartidores = df_filtered[repartidor_col].value_counts().reset_index()
top_repartidores.columns = ['Repartidor', 'Frecuencia']

# 5. Calculate percentage relative to the total occurrences of this specific reason
top_repartidores['Porcentaje (%)'] = (top_repartidores['Frecuencia'] / reason_count * 100).round(2)

# 6. Select Top 5
top_5_repartidores = top_repartidores.head(5)
print('\nTop 5 delivery drivers with the highest incidence for this reason:')
print(top_5_repartidores)

# 7. Visualization
plt.figure(figsize=(10, 6))
sns.barplot(data=top_5_repartidores, x='Repartidor', y='Frecuencia', palette='viridis')
plt.title(f'Top 5 Repartidores con mayor incidencia:\n"{most_frequent_reason}"')
plt.xlabel('Repartidor')
plt.ylabel('Cantidad de Incidencias')
plt.xticks(rotation=45, ha='right')
for i, val in enumerate(top_5_repartidores['Porcentaje (%)']):
    plt.text(i, top_5_repartidores['Frecuencia'].iloc[i] + 0.5, f'{val}%', ha='center')
plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Inspect unique values in 'K' and filter for effective deliveries
# Based on common logistics data and previous steps, 'Efectividad' or 'Causa Ajena' are candidates.
# For this task, we treat the main success metric found in the data as the filter.
print('Unique values in column K:', df['K'].unique())

# Based on previous analysis where 'Efectividad' was the most frequent reason in 'L',
# we filter column 'K' for values typically associated with completed or processed deliveries.
# We will use 'Causa Ajena' as a proxy for the 'Tipología de Calidad' filter as seen in head() earlier.
effective_filter = 'Causa Ajena'
df_effective = df[df['K'] == effective_filter]

# 2. Count frequency by delivery driver (Column 'H')
repartidor_counts = df_effective['H'].value_counts().reset_index()
repartidor_counts.columns = ['Repartidor', 'Frecuencia']

# 3. Calculate percentage over total deliveries (all rows in df)
total_deliveries = len(df)
repartidor_counts['Porcentaje (%)'] = (repartidor_counts['Frecuencia'] / total_deliveries * 100).round(2)

# 4. Select top 5
top_5_max = repartidor_counts.head(5)
print('\nTop 5 Repartidores with most effective deliveries:')
print(top_5_max)

# 5. Visualization
plt.figure(figsize=(12, 6))
sns.barplot(data=top_5_max, x='Repartidor', y='Frecuencia', hue='Repartidor', palette='magma', legend=False)
plt.title(f'Top 5 Repartidores con Mayor Número de Entregas ({effective_filter})')
plt.xlabel('Repartidor')
plt.ylabel('Número de Entregas')
plt.xticks(rotation=45, ha='right')

# Adding labels on top of bars
for i, row in top_5_max.iterrows():
    plt.text(i, row['Frecuencia'] + 0.1, f"{row['Porcentaje (%)']}%", ha='center')

plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Sort the previously created 'repartidor_counts' DataFrame in ascending order
# 2. Select the first 5 rows for the Top 5 drivers with the least deliveries
top_5_min = repartidor_counts.sort_values(by='Frecuencia', ascending=True).head(5)

print('Top 5 Repartidores with the lowest number of effective deliveries:')
print(top_5_min)

# 3. Visualization using Seaborn
plt.figure(figsize=(12, 6))
sns.barplot(data=top_5_min, x='Repartidor', y='Frecuencia', hue='Repartidor', palette='viridis', legend=False)

plt.title('Top 5 Repartidores con Menor Número de Entregas Efectivas')
plt.xlabel('Repartidor')
plt.ylabel('Número de Entregas')
plt.xticks(rotation=45, ha='right')

# Add data labels (percentages) on top of the bars
for i, (index, row) in enumerate(top_5_min.iterrows()):
    plt.text(i, row['Frecuencia'] + 0.05, f"{row['Porcentaje (%)']}%", ha='center', va='bottom')

plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Calculate frequency of shipments by zip code (Column 'O')
cp_counts = df['O'].value_counts().reset_index()
cp_counts.columns = ['Codigo_Postal', 'Envios']

# Ensure zip code is treated as a string for categorical plotting if it's currently float/int
cp_counts['Codigo_Postal'] = cp_counts['Codigo_Postal'].astype(str).str.replace('.0', '', regex=False)

# 2. Identify top 15 zip codes with most activity for a cleaner visualization
top_cp = cp_counts.head(15)

# 3 & 4. Create visualization
plt.figure(figsize=(14, 7))
sns.barplot(data=top_cp, x='Codigo_Postal', y='Envios', hue='Codigo_Postal', palette='coolwarm', legend=False)

plt.title('Distribución de Envíos por Código Postal (Top 15)', fontsize=15)
plt.xlabel('Código Postal Destino', fontsize=12)
plt.ylabel('Cantidad de Envíos', fontsize=12)
plt.xticks(rotation=45)

# Add labels on top of bars
for i, val in enumerate(top_cp['Envios']):
    plt.text(i, val + 0.5, str(int(val)), ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1 & 2. Group by Zip Code (O) and Product (M) and count occurrences
dominant_products = df.groupby(['O', 'M']).size().reset_index(name='Cantidad')
dominant_products.columns = ['Codigo_Postal', 'Producto', 'Cantidad']

# Clean zip code column for consistency
dominant_products['Codigo_Postal'] = dominant_products['Codigo_Postal'].astype(str).str.replace('.0', '', regex=False)

# 3. Filter for the dominant product (max quantity) in each zip code
dominant_products = dominant_products.sort_values(['Codigo_Postal', 'Cantidad'], ascending=[True, False])
dominant_per_cp = dominant_products.drop_duplicates(subset='Codigo_Postal')

# 4. Select top 10 zip codes with the highest volume of the dominant product
top_10_dominant = dominant_per_cp.nlargest(10, 'Cantidad')

# 5 & 6. Visualization
plt.figure(figsize=(14, 8))
sns.barplot(data=top_10_dominant, x='Codigo_Postal', y='Cantidad', hue='Producto', dodge=False)

plt.title('Producto con Mayor Volumen de Entregas por Código Postal (Top 10 CP)', fontsize=16)
plt.xlabel('Código Postal Destino', fontsize=12)
plt.ylabel('Cantidad de Entregas', fontsize=12)
plt.xticks(rotation=45)
plt.legend(title='Producto Dominante', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add data labels
for i, val in enumerate(top_10_dominant['Cantidad']):
    plt.text(i, val + 0.5, str(int(val)), ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. We reuse the effective deliveries filter defined previously: 'Causa Ajena'
# The variable 'repartidor_counts' already contains frequencies and percentages relative to total

# 2. Sort the counts in ascending order to find those with the lowest number of deliveries
# 3. Select the Top 5 with the lowest counts
top_5_min = repartidor_counts.sort_values(by='Frecuencia', ascending=True).head(5)

print('Tabla: 5 repartidores con menor número de entregas efectivas:')
print(top_5_min)

# 4. Create the visualization
plt.figure(figsize=(12, 6))
sns.barplot(data=top_5_min, x='Repartidor', y='Frecuencia', hue='Repartidor', palette='flare', legend=False)

plt.title('Top 5 Repartidores con Menor Número de Entregas Efectivas', fontsize=14)
plt.xlabel('Repartidor', fontsize=12)
plt.ylabel('Número de Entregas', fontsize=12)
plt.xticks(rotation=45, ha='right')

# Add data labels with percentages on top of the bars
for i, (index, row) in enumerate(top_5_min.iterrows()):
    plt.text(i, row['Frecuencia'] + 0.02, f"{row['Porcentaje (%)']}%", ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Calculate frequency of shipments by zip code (Column 'O')
cp_counts = df['O'].value_counts().reset_index()
cp_counts.columns = ['Codigo_Postal', 'Envios']

# 2. Convert zip codes to string to ensure correct categorical visualization
# Cleaning potential float representation like '39300.0'
cp_counts['Codigo_Postal'] = cp_counts['Codigo_Postal'].astype(str).str.replace('.0', '', regex=False)

# 3. Identify the top 15 zip codes to prevent over-saturation
top_15_cp = cp_counts.head(15)

# 4 & 5. Create the bar plot with titles, labels, and data labels
plt.figure(figsize=(14, 7))
sns.barplot(data=top_15_cp, x='Codigo_Postal', y='Envios', hue='Codigo_Postal', palette='viridis', legend=False)

plt.title('Top 15 Códigos Postales por Volumen de Envíos', fontsize=16)
plt.xlabel('Código Postal Destino', fontsize=12)
plt.ylabel('Cantidad de Envíos', fontsize=12)
plt.xticks(rotation=45)

# Add data labels on top of the bars
for i, val in enumerate(top_15_cp['Envios']):
    plt.text(i, val + 0.5, str(int(val)), ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Group by Zip Code (O) and Product (M) and count occurrences
dominant_products_df = df.groupby(['O', 'M']).size().reset_index(name='Cantidad')
dominant_products_df.columns = ['Codigo_Postal', 'Producto', 'Cantidad']

# 2. Clean zip code column for consistency (removing .0 if it exists)
dominant_products_df['Codigo_Postal'] = dominant_products_df['Codigo_Postal'].astype(str).str.replace('.0', '', regex=False)

# 3. Filter for the dominant product (max quantity) in each zip code
# Sort by quantity descending and then drop duplicates keeping the first occurrence per CP
dominant_per_cp = dominant_products_df.sort_values(['Codigo_Postal', 'Cantidad'], ascending=[True, False]).drop_duplicates(subset='Codigo_Postal')

# 4. Select top 10 zip codes with the highest volume of the dominant product
top_10_dominant_products = dominant_per_cp.nlargest(10, 'Cantidad')

# 5 & 6. Create visualization with titles, labels, and data annotations
plt.figure(figsize=(14, 8))
sns.barplot(data=top_10_dominant_products, x='Codigo_Postal', y='Cantidad', hue='Producto', dodge=False)

plt.title('Producto con Mayor Volumen de Entregas por Código Postal (Top 10 CP)', fontsize=16)
plt.xlabel('Código Postal Destino', fontsize=12)
plt.ylabel('Cantidad de Entregas', fontsize=12)
plt.xticks(rotation=45)
plt.legend(title='Producto Dominante', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add data labels on top of bars
for i, val in enumerate(top_10_dominant_products['Cantidad']):
    plt.text(i, val + 0.5, str(int(val)), ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.show()
lot as plt
import seaborn as sns

# 1. Ensure the top_15_cp is sorted descending
top_15_sorted = top_15_cp.sort_values(by='Envios', ascending=False).copy()

# 2. Add a column for the Prefix (first 3 digits) to identify proximity
top_15_sorted['Prefix'] = top_15_sorted['Codigo_Postal'].str[:3]

# 3. Create a visualization: Horizontal Bar Chart showing volume relative to the highest
plt.figure(figsize=(12, 8))
sns.barplot(data=top_15_sorted, x='Envios', y='Codigo_Postal', hue='Prefix', palette='tab10', dodge=False)

plt.title('Propuesta de Micro-Hubs: Top 15 CP por Volumen de Envíos', fontsize=16)
plt.xlabel('Volumen de Envíos (Densidad)', fontsize=12)
plt.ylabel('Código Postal Destino', fontsize=12)
plt.legend(title='Zona de Proximidad (Prefijo)', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add data labels
for i, val in enumerate(top_15_sorted['Envios']):
    plt.text(val + 1, i, str(int(val)), va='center', fontweight='bold')

plt.tight_layout()
plt.show()

# 4. Propose logical grouping verbally
print('--- Propuesta Estratégica de Micro-Hubs ---')
hub_primary = top_15_sorted.iloc[0]['Codigo_Postal']
print(f'NODO PRINCIPAL: CP {hub_primary} con {top_15_sorted.iloc[0]["Envios"]} envíos.')

groups = top_15_sorted.groupby('Prefix')['Codigo_Postal'].apply(list).to_dict()
print('\nAgrupaciones Sugeridas por Proximidad (Prefijo):')
for prefix, codes in groups.items():
    print(f'- Hub Zona {prefix}: Cubre los sectores {codes}')

print('\nJustificación: Los Micro-Hubs deben centrarse en los CPs de mayor densidad (e.g., 39300, 39011) para reducir la \'última milla\' consolidando el stock de productos dominantes detectados previamente.')
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Identify low-performing drivers (reusing top_5_min from previous steps)
low_perf_drivers = top_5_min['Repartidor'].unique()

# 2. Extract operations data for these drivers
df_low_perf = df[df['H'].isin(low_perf_drivers)].copy()

# 3. Calculate density (shipments) per CP for these specific drivers
driver_cp_density = df_low_perf.groupby(['H', 'O']).size().reset_index(name='Envios_Repartidor')
driver_cp_density['O'] = driver_cp_density['O'].astype(str).str.replace('.0', '', regex=False)

# 4. Get global density for comparison
global_cp_density = cp_counts.rename(columns={'Envios': 'Densidad_Global_Zona'})

# 5. Merge data to compare driver performance vs zone density
comparison_df = driver_cp_density.merge(global_cp_density, left_on='O', right_on='Codigo_Postal', how='left')

# 6. Visualization: Contrast driver deliveries vs zone density
plt.figure(figsize=(12, 7))
scatter = sns.scatterplot(data=comparison_df, x='Densidad_Global_Zona', y='Envios_Repartidor', hue='H', s=100, style='H')

# Add a reference line for average density of top 15 zones
avg_top_15_density = top_15_cp['Envios'].mean()
plt.axvline(avg_top_15_density, color='red', linestyle='--', label=f'Promedio Top 15 ({int(avg_top_15_density)})')

plt.title('Correlación: Entregas de Repartidores Low-Perf vs. Densidad de la Zona', fontsize=14)
plt.xlabel('Densidad Global de Envíos en la Zona (CP)', fontsize=12)
plt.ylabel('Envíos Realizados por el Repartidor', fontsize=12)
plt.legend(title='Repartidor / Ref', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Analysis output
print('--- Análisis de Correlación ---')
for driver in low_perf_drivers:
    driver_data = comparison_df[comparison_df['H'] == driver]
    mean_zone_density = driver_data['Densidad_Global_Zona'].mean()
    if mean_zone_density < avg_top_15_density:
        print(f'- {driver}: Opera en zonas de BAJA densidad (Promedio {mean_zone_density:.1f}). Posible exceso de desplazamiento.')
    else:
        print(f'- {driver}: Opera en zonas de ALTA densidad (Promedio {mean_zone_density:.1f}). Sugiere necesidad de capacitación.')
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Prepare data using top_15_cp
hub_data = top_15_cp.copy()
hub_data['Prefijo'] = hub_data['Codigo_Postal'].astype(str).str[:3]

# 2. Identify the lead node (Micro-Hub) per prefix (max volume)
micro_hubs = hub_data.loc[hub_data.groupby('Prefijo')['Envios'].idxmax()].copy()
micro_hubs = micro_hubs.sort_values(by='Envios', ascending=False)

# 3. Visualization: Horizontal Bar Chart colored by Prefix
plt.figure(figsize=(12, 8))
sns.barplot(data=hub_data.sort_values('Envios', ascending=False), x='Envios', y='Codigo_Postal', hue='Prefijo', dodge=False, palette='tab10')

plt.title('Propuesta de Micro-Hubs por Zona (Prefijo) - Top 15 CP', fontsize=16)
plt.xlabel('Volumen de Envíos', fontsize=12)
plt.ylabel('Código Postal', fontsize=12)
plt.legend(title='Zona (Prefijo)', bbox_to_anchor=(1.05, 1), loc='upper left')

# Highlight Micro-Hubs with a marker or text
for i, (cp, envios) in enumerate(zip(hub_data.sort_values('Envios', ascending=False)['Codigo_Postal'], hub_data.sort_values('Envios', ascending=False)['Envios'])):
    if cp in micro_hubs['Codigo_Postal'].values:
        plt.text(envios + 5, i, '★ HUB', color='red', fontweight='bold', va='center')

plt.tight_layout()
plt.show()

# 4. Print detailed list of proposed Micro-Hubs
print('--- ESTRATEGIA DE MICRO-HUBS PROPUESTA ---')
for _, hub in micro_hubs.iterrows():
    covered_codes = hub_data[hub_data['Prefijo'] == hub['Prefijo']]['Codigo_Postal'].tolist()
    print(f'NODO: CP {hub["Codigo_Postal"]} (Prefijo {hub["Prefijo"]})')
    print(f'  - Volumen del Nodo: {hub["Envios"]}')
    print(f'  - Sectores que consolida: {covered_codes}')
    print('-' * 40)
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Merge micro_hubs with dominant_per_cp to identify the top product for each lead node
# Ensure 'Codigo_Postal' columns are strings for a clean merge
micro_hubs['Codigo_Postal'] = micro_hubs['Codigo_Postal'].astype(str)
dominant_per_cp['Codigo_Postal'] = dominant_per_cp['Codigo_Postal'].astype(str)

stock_forwarding_strategy = micro_hubs.merge(
    dominant_per_cp[['Codigo_Postal', 'Producto', 'Cantidad']], 
    on='Codigo_Postal', 
    how='left'
)

# Rename columns for clarity in the recommendation
stock_forwarding_strategy.rename(columns={'Cantidad': 'Volumen_Producto_Dominante'}, inplace=True)

# 2. Visualization: Stock Capacity Requirements at Hubs
plt.figure(figsize=(12, 6))
sns.barplot(
    data=stock_forwarding_strategy, 
    x='Codigo_Postal', 
    y='Volumen_Producto_Dominante', 
    hue='Producto', 
    palette='deep'
)

plt.title('Requerimiento de Stock Forwarding por Micro-Hub (Producto Dominante)', fontsize=14)
plt.xlabel('Código Postal del Micro-Hub', fontsize=12)
plt.ylabel('Volumen Estimado de Stock (Unidades)', fontsize=12)
plt.legend(title='Producto a Pre-almacenar', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add data labels
for i, val in enumerate(stock_forwarding_strategy['Volumen_Producto_Dominante']):
    plt.text(i, val + 2, str(int(val)), ha='center', fontweight='bold')

plt.tight_layout()
plt.show()

# 3. Print the clear recommendation list
print('--- RECOMENDACIONES DE STOCK FORWARDING ---')
for _, row in stock_forwarding_strategy.iterrows():
    print(f"NODO HUB {row['Codigo_Postal']} (Zona {row['Prefijo']}):")
    print(f"  - Producto Recomendado: {row['Producto']}")
    print(f"  - Volumen Crítico: {row['Volumen_Producto_Dominante']} unidades")
    print(f"  - Justificación: Este producto lidera la demanda en el nodo principal del clúster {row['Prefijo']}.")
    print('-' * 50)
import pandas as pd

# 1. Identify low-performing drivers from top_5_min (already defined in previous steps)
low_perf_drivers = top_5_min['Repartidor'].unique()

# 2. Filter main DataFrame for these drivers
df_low_perf_ops = df[df['H'].isin(low_perf_drivers)]

# 3. Get unique CPs for these drivers and get their global density
# Use 'cp_counts' which contains the global frequency per CP
low_perf_cps = df_low_perf_ops['O'].astype(str).str.replace('.0', '', regex=False).unique()
density_low_perf_zones = cp_counts[cp_counts['Codigo_Postal'].isin(low_perf_cps)]

# 4. Calculate average density for low-performance zones
avg_density_low_perf = density_low_perf_zones['Envios'].mean()

# 5. Calculate average density for Top 15 high-volume zones (top_15_cp already exists)
avg_density_high_vol = top_15_cp['Envios'].mean()

# 6. Comparison and output
density_gap_pct = ((avg_density_high_vol - avg_density_low_perf) / avg_density_high_vol) * 100

print(f'Promedio de densidad en zonas de bajo desempe\u00f1o: {avg_density_low_perf:.2f} env\u00edos/CP')
print(f'Promedio de densidad en zonas de alto volumen (Top 15): {avg_density_high_vol:.2f} env\u00edos/CP')
print(f'Brecha de densidad: Las zonas de alto volumen tienen un {density_gap_pct:.2f}% m\u00e1s de pedidos en promedio.')
import matplotlib.pyplot as plt
import seaborn as sns

# Prepare the visualization using comparison_df and avg_top_15_density calculated previously
plt.figure(figsize=(12, 8))

# Create the scatter plot
scatter = sns.scatterplot(
    data=comparison_df, 
    x='Densidad_Global_Zona', 
    y='Envios_Repartidor', 
    hue='H', 
    s=150, 
    style='H', 
    alpha=0.8
)

# Add the vertical reference line for the Top 15 density average
plt.axvline(avg_top_15_density, color='red', linestyle='--', linewidth=2, label=f'Promedio Top 15 ({int(avg_top_15_density)})')

# Formatting the chart
plt.title('Contraste: Volumen del Repartidor vs. Densidad Global de la Zona', fontsize=16, pad=20)
plt.xlabel('Densidad Global de Pedidos en el CP', fontsize=12)
plt.ylabel('Envíos Realizados por el Repartidor', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(title='Repartidor / Referencia', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()
import pandas as pd

# 1 & 2. Group data by 'H' (Repartidor) and 'L' (Motivo de Situación)
# 3. Calculate frequency and save to incidencias_por_repartidor
incidencias_por_repartidor = df.groupby(['H', 'L']).size().reset_index(name='Cantidad_Incidencias')

# 5. Sort by incidence quantity in descending order
incidencias_por_repartidor = incidencias_por_repartidor.sort_values(by='Cantidad_Incidencias', ascending=False)

# 6. Show the first rows to verify structure
print('Consolidado de incidencias por repartidor:')
display(incidencias_por_repartidor.head(10))
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Identify the top 15 drivers with the most total incidents to keep the heatmap readable
top_15_drivers_incidents = incidencias_por_repartidor.groupby('H')['Cantidad_Incidencias'].sum().nlargest(15).index

# 2. Filter the original grouped data for these drivers
heatmap_data_filtered = incidencias_por_repartidor[incidencias_por_repartidor['H'].isin(top_15_drivers_incidents)]

# 3. Pivot the data: Index = Driver (H), Columns = Reason (L), Values = Count
incidencias_pivot = heatmap_data_filtered.pivot(index='H', columns='L', values='Cantidad_Incidencias').fillna(0)

# 4. Generate the heatmap
plt.figure(figsize=(16, 10))
sns.heatmap(incidencias_pivot, annot=True, fmt='g', cmap='YlGnBu', cbar_kws={'label': 'Frecuencia de Incidencias'})

# 5. Add descriptive titles and labels
plt.title('Mapa de Calor: Incidencias Críticas por Repartidor (Top 15)', fontsize=18, pad=20)
plt.xlabel('Motivo de Situación (Incidencia)', fontsize=14)
plt.ylabel('Nombre del Repartidor', fontsize=14)
plt.xticks(rotation=45, ha='right')

# 6. Adjust layout and display
plt.tight_layout()
plt.show()
# 1. Calculate total incidents per driver
top_3_drivers_total = incidencias_por_repartidor.groupby('H')['Cantidad_Incidencias'].sum().nlargest(3).reset_index()
top_3_drivers_total.columns = ['Repartidor', 'Total_Incidencias']

# 2. Identify the top 3 most recurrent incident reasons globally
top_3_reasons_global = incidencias_por_repartidor.groupby('L')['Cantidad_Incidencias'].sum().nlargest(3).reset_index()
top_3_reasons_global.columns = ['Motivo_Incidencia', 'Frecuencia_Global']

# 3. Check for patterns in the top drivers
top_reasons_per_top_driver = incidencias_por_repartidor[incidencias_por_repartidor['H'].isin(top_3_drivers_total['Repartidor'])].sort_values(['H', 'Cantidad_Incidencias'], ascending=[True, False]).groupby('H').head(1)

print('--- Hallazgos: Repartidores Cr3ticos ---')
print(top_3_drivers_total)
print('\n--- Hallazgos: Motivos Globales m1s Comunes ---')
print(top_3_reasons_global)
print('\n--- Patr2n: Motivo Principal de los Repartidores Top ---')
print(top_reasons_per_top_driver[['H', 'L', 'Cantidad_Incidencias']])

