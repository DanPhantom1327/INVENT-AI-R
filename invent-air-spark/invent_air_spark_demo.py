"""Demostracion INVENT-AI-R con Apache Spark MLlib. Datos sinteticos, no operativos.
Uso: python invent_air_spark_demo.py RUTA_CSV
"""
import os, sys, json
from pathlib import Path
from pyspark.sql import SparkSession, functions as F, Window
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator

ARCHIVO = sys.argv[1] if len(sys.argv)>1 else 'INVENT_AI_R_100000_datos_sinteticos.csv'
SALIDA = Path('salida_spark')
SALIDA.mkdir(exist_ok=True)

spark = (SparkSession.builder.appName('INVENT-AI-R - Prediccion 7 dias')
         .master('local[2]').config('spark.sql.shuffle.partitions','4')
         .getOrCreate())
spark.sparkContext.setLogLevel('ERROR')
try:
    df = spark.read.option('header', True).option('inferSchema', True).option('encoding','UTF-8').csv(ARCHIVO)
    df = df.withColumn('fecha', F.to_date('fecha'))
    print('\n=== PASO 1: EXPLORACION ===')
    print('Registros originales:',df.count())
    df.printSchema()
    df.select('id_registro','fecha','fruta','ventas_actuales_kg','demanda_proximos_7d_kg').show(5,truncate=False)

    # Detectar sin emplear la etiqueta artificial calidad_registro
    requeridas=['ventas_actuales_kg','ventas_7d_previas_kg','stock_pulpa_kg','demanda_proximos_7d_kg']
    tiene_nulos = F.lit(False)
    for c in requeridas:
        tiene_nulos = tiene_nulos | F.col(c).isNull() | F.isnan(F.col(c))
    fuera_rango=(~F.col('ventas_actuales_kg').between(0.000001,999.999999) |
                 ~F.col('stock_fruta_kg').between(0.000001,19999.999999) |
                 ~F.col('precio_venta_cop_kg').between(1000.000001,99999.999999) |
                 ~F.col('merma_pct').between(0,25))
    df = df.withColumn('estado_detectado',F.when(tiene_nulos,'SUCIO_NULO')
                       .when(fuera_rango,'OUTLIER').otherwise('VALIDO'))
    print('\n=== PASO 2: CALIDAD ===')
    df.groupBy('estado_detectado').count().orderBy('estado_detectado').show()
    # Solo para auditar esta simulacion, nunca para aprender/predecir
    df.groupBy('calidad_registro','estado_detectado').count().show()

    limpios = df.filter(F.col('estado_detectado')=='VALIDO').cache()
    n = limpios.count()
    assert n == 80000, f'Se esperaban 80000 registros limpios, se obtuvieron {n}'
    print('Registros depurados:',n)

    # 80/20 exacto y reproducible, ordenados por fecha/id.
    # Advertencia: la frontera puede compartir fecha, y las etiquetas a 7d pueden solaparse.
    ventana = Window.orderBy('fecha','id_registro')
    numerados = limpios.withColumn('fila_orden',F.row_number().over(ventana))
    train = numerados.filter(F.col('fila_orden')<=64000).cache()
    test = numerados.filter(F.col('fila_orden')>64000).cache()
    print('\n=== PASO 3: DIVISION TEMPORAL ===')
    print('Entrenamiento:',train.count(),'Prueba:',test.count())
    print('Fechas limite entrenamiento:', train.agg(F.max('fecha')).first()[0])
    print('Fechas limite prueba:', test.agg(F.min('fecha')).first()[0])

    columnas_numericas=['mes','dia_semana','temporada_alta','temperatura_c',
                        'precio_venta_cop_kg','ventas_actuales_kg','ventas_7d_previas_kg',
                        'compras_fruta_kg','stock_fruta_kg','stock_pulpa_kg',
                        'merma_pct','rendimiento_pulpa_pct','dias_reposicion']
    categoria = StringIndexer(inputCol='fruta',outputCol='fruta_idx',handleInvalid='keep')
    vector = VectorAssembler(inputCols=['fruta_idx']+columnas_numericas,outputCol='features')
    regresor = RandomForestRegressor(featuresCol='features',labelCol='demanda_proximos_7d_kg',
                                    predictionCol='prediction',numTrees=35,maxDepth=9,seed=42)
    pipeline = Pipeline(stages=[categoria,vector,regresor])
    print('\n=== PASO 4: ENTRENAMIENTO SPARK MLLIB ===')
    modelo=pipeline.fit(train)
    pred=modelo.transform(test).withColumn('prediction',F.greatest(F.col('prediction'),F.lit(0.0))).cache()
    pred.count()
    metricas={}
    for nombre,metric in [('MAE_kg','mae'),('RMSE_kg','rmse'),('R2','r2')]:
        metricas[nombre]=round(RegressionEvaluator(labelCol='demanda_proximos_7d_kg',predictionCol='prediction',metricName=metric).evaluate(pred),4)
    print('\n=== PASO 5: EVALUACION ===')
    print(json.dumps(metricas,indent=2,ensure_ascii=False))

    pred=(pred.withColumn('cobertura_dias',F.when(F.col('prediction')>0,7*F.col('stock_pulpa_kg')/F.col('prediction')))
          .withColumn('alerta',F.when(F.col('cobertura_dias')<F.col('dias_reposicion'),'ALERTA').otherwise('NORMAL'))
          .withColumn('error_absoluto_kg',F.abs(F.col('demanda_proximos_7d_kg')-F.col('prediction'))))
    pred.select('fecha','fruta','demanda_proximos_7d_kg','prediction','cobertura_dias','alerta').show(10,False)
    pred.groupBy('alerta').count().show()

    # Exportacion Spark: CSV en directorio con archivo part-*.csv.
    pred.select('id_registro','fecha','fruta','demanda_proximos_7d_kg','prediction',
                'error_absoluto_kg','cobertura_dias','alerta').coalesce(1).write.mode('overwrite').option('header',True).csv(str(SALIDA/'predicciones'))
    limpios.drop('estado_detectado').coalesce(1).write.mode('overwrite').option('header',True).csv(str(SALIDA/'datos_limpios'))
    with open(SALIDA/'metricas_spark.json','w',encoding='utf8') as f:
        json.dump(metricas,f,indent=2,ensure_ascii=False)
    modelo.write().overwrite().save(str(SALIDA/'modelo_spark'))

    # Matplotlib solo visualiza agregados/resultados de Spark
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7,4))
    plt.bar(['Validos','Outliers','Nulos'],[80000,10000,10000])
    plt.title('Calidad de datos INVENT-AI-R'); plt.ylabel('Registros'); plt.tight_layout()
    plt.savefig(SALIDA/'01_calidad.png');plt.close()

    mensual=(limpios.groupBy(F.date_format('fecha','yyyy-MM').alias('mes'))
             .agg(F.avg('demanda_proximos_7d_kg').alias('promedio'))
             .orderBy('mes').collect())
    plt.figure(figsize=(11,4))
    plt.plot([r.mes for r in mensual],[r.promedio for r in mensual]);plt.xticks(rotation=90,fontsize=7)
    plt.ylabel('Demanda promedio futura (kg)');plt.title('Demanda por mes');plt.tight_layout()
    plt.savefig(SALIDA/'02_demanda_mensual.png');plt.close()

    muestra=pred.orderBy('id_registro').select('demanda_proximos_7d_kg','prediction').limit(500).toPandas()
    plt.figure(figsize=(6,5))
    plt.scatter(muestra['demanda_proximos_7d_kg'],muestra['prediction'],s=9,alpha=.45)
    v=max(muestra.max());plt.plot([0,v],[0,v],'--')
    plt.xlabel('Demanda real simulada (kg)');plt.ylabel('Prediccion Spark (kg)')
    plt.title('Real vs predicho (muestra de 500)');plt.tight_layout()
    plt.savefig(SALIDA/'03_real_vs_predicho.png');plt.close()

    plt.figure(figsize=(7,4))
    plt.hist(muestra['prediction']-muestra['demanda_proximos_7d_kg'],bins=30)
    plt.xlabel('Error predicho - real (kg)');plt.ylabel('Frecuencia');plt.title('Distribucion de errores')
    plt.tight_layout();plt.savefig(SALIDA/'04_errores.png');plt.close()

    alertas={r['alerta']:r['count'] for r in pred.groupBy('alerta').count().collect()}
    plt.figure(figsize=(6,4));plt.bar(list(alertas),list(alertas.values()))
    plt.title('Alertas estimadas de desabastecimiento');plt.ylabel('Registros')
    plt.tight_layout();plt.savefig(SALIDA/'05_alertas.png');plt.close()
    print('\nListo. Archivos guardados en:',SALIDA.resolve())
    print('Abre http://localhost:4040 mientras se ejecuta el trabajo para la interfaz Spark UI.')
finally:
    spark.stop()
