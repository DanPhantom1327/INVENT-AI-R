-- =========================================================
-- INVENT-AI-R: convertir columnas TIMESTAMP a TIMESTAMPTZ
--
-- Motivo: Django (USE_TZ=True) escribe las fechas en UTC. Con columnas
-- TIMESTAMP (sin zona) las lee como si fueran hora local y las muestra
-- corridas 5 horas. Para agrupar ventas por dia eso es un error real:
-- una venta de las 20:00 en Bogota caeria en el dia siguiente.
--
-- Es seguro correrlo mas de una vez: si ya esta convertido, no hace nada.
-- =========================================================
DO $$
BEGIN
    IF (SELECT data_type
          FROM information_schema.columns
         WHERE table_schema = 'ventas_schema'
           AND table_name   = 'ventas'
           AND column_name  = 'fecha') = 'timestamp without time zone' THEN

        ALTER TABLE auth_schema.usuarios
            ALTER COLUMN fecha_creacion TYPE TIMESTAMPTZ USING fecha_creacion AT TIME ZONE 'UTC',
            ALTER COLUMN last_login     TYPE TIMESTAMPTZ USING last_login     AT TIME ZONE 'UTC';

        ALTER TABLE inventario_schema.items_inventario
            ALTER COLUMN fecha_creacion TYPE TIMESTAMPTZ USING fecha_creacion AT TIME ZONE 'UTC';

        ALTER TABLE inventario_schema.movimientos_inventario
            ALTER COLUMN fecha TYPE TIMESTAMPTZ USING fecha AT TIME ZONE 'UTC';

        ALTER TABLE ventas_schema.ventas
            ALTER COLUMN fecha TYPE TIMESTAMPTZ USING fecha AT TIME ZONE 'UTC';

        ALTER TABLE compras_schema.compras
            ALTER COLUMN fecha TYPE TIMESTAMPTZ USING fecha AT TIME ZONE 'UTC';

        ALTER TABLE analisis_schema.proyecciones
            ALTER COLUMN fecha_generacion TYPE TIMESTAMPTZ USING fecha_generacion AT TIME ZONE 'UTC';

        ALTER TABLE analisis_schema.cobertura_stock
            ALTER COLUMN fecha_calculo TYPE TIMESTAMPTZ USING fecha_calculo AT TIME ZONE 'UTC';

        ALTER TABLE analisis_schema.alertas
            ALTER COLUMN fecha_generacion TYPE TIMESTAMPTZ USING fecha_generacion AT TIME ZONE 'UTC',
            ALTER COLUMN fecha_resolucion TYPE TIMESTAMPTZ USING fecha_resolucion AT TIME ZONE 'UTC';

        RAISE NOTICE 'Columnas convertidas a TIMESTAMPTZ.';
    ELSE
        RAISE NOTICE 'Las columnas ya eran TIMESTAMPTZ; no se hizo nada.';
    END IF;
END
$$;
