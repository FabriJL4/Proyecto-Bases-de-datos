
CREATE SCHEMA prototipo;


-- Configurar el search_path para que las tablas se creen dentro de ese esquema
-- y se busquen ahí automáticamente
SET search_path TO prototipo, public;


-- 1. Usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    fecha_registro DATE DEFAULT CURRENT_DATE NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);


-- 2. Contactos (RF02, RE02, RN02)
CREATE TABLE usuario_telefonos (
    id_usuario INT REFERENCES usuarios(id_usuario),
    telefono VARCHAR(20),
    PRIMARY KEY (id_usuario, telefono)
);


CREATE TABLE usuario_emails (
    id_usuario INT REFERENCES usuarios(id_usuario),
    email VARCHAR(100),
    PRIMARY KEY (id_usuario, email)
);


-- 3. Categorías (RF03, RE05, RN04)
CREATE TABLE categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    id_categoria_padre INT REFERENCES categorias(id_categoria)
    -- NOTA: La raíz tendría id_categoria_padre NULL
);


-- 4. Eventos (RF04, RE04)
CREATE TABLE eventos (
    id_evento SERIAL PRIMARY KEY,
    id_usuario_propietario INT NOT NULL REFERENCES usuarios(id_usuario),
    id_categoria INT NOT NULL REFERENCES categorias(id_categoria),
    titulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    CONSTRAINT check_fechas CHECK (fecha_fin > fecha_inicio)
);


-- 5. Participación (RF05, RE01, RN01, RN05)
CREATE TABLE participaciones (
    id_evento INT REFERENCES eventos(id_evento) ON DELETE CASCADE,
    id_invitado INT REFERENCES usuarios(id_usuario),
    rol VARCHAR(50),
    estado_confirmacion VARCHAR(20) DEFAULT 'pendiente',
    PRIMARY KEY (id_evento, id_invitado)
);


-- 6. Log de Accesos (RF06)
CREATE TABLE log_accesos (
    id_log SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuarios(id_usuario),
    fecha_acceso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Implementación de Cálculos Dinámicos (RF07, RE03, RN03) mediante vistas


-- Vista para Antigüedad
CREATE VIEW vista_antiguedad_usuarios AS
SELECT 
    id_usuario, 
    nombre, 
    fecha_registro,
    age(CURRENT_DATE, fecha_registro) AS antiguedad
FROM usuarios;


-- Vista para Duración de eventos diarios
CREATE VIEW vista_duracion_eventos_diarios AS
SELECT 
    id_usuario_propietario,
    fecha_inicio::DATE AS dia,
    SUM(EXTRACT(EPOCH FROM (fecha_fin - fecha_inicio))/60) AS duracion_total_minutos
FROM eventos
GROUP BY id_usuario_propietario, fecha_inicio::DATE;


--Integridad y Prevención de Ciclos (RE05)
--Para evitar ciclos en la jerarquía de categorías, podemos usar una función 
--que verifique el ancestro antes de insertar o actualizar:


CREATE OR REPLACE FUNCTION evitar_ciclo_categorias()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id_categoria_padre = NEW.id_categoria THEN
        RAISE EXCEPTION 'Una categoría no puede ser padre de sí misma.';
    END IF;
    -- Aquí se podría añadir una consulta recursiva para validar ancestros, 
    -- pero para Postgres 14 es altamente eficiente usar el camino (path) o este chequeo simple.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_evitar_ciclo
BEFORE INSERT OR UPDATE ON categorias
FOR EACH ROW EXECUTE FUNCTION evitar_ciclo_categorias();

-- ============================================================
-- AMPLIACION DEL PROYECTO
-- Modulos seleccionados:
-- 1. Gestion de Ubicaciones
-- 2. Disponibilidad de Usuarios
-- 3. Tareas Asociadas a Eventos
-- ============================================================

-- ============================================================
-- RF-08: Gestion y Registro de Ubicaciones
-- ============================================================

CREATE TABLE prototipo.ubicaciones (
    id_ubicacion SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    capacidad INTEGER NOT NULL,
    CONSTRAINT check_capacidad_ubicacion
        CHECK (capacidad > 0)
);

-- ============================================================
-- RF-09: Asociacion Espacial de Eventos
-- ============================================================

-- Agregar la ubicacion asociada a cada evento

ALTER TABLE prototipo.eventos
ADD COLUMN id_ubicacion INTEGER;

-- Crear la relacion entre eventos y ubicaciones

ALTER TABLE prototipo.eventos
ADD CONSTRAINT fk_eventos_ubicacion
FOREIGN KEY (id_ubicacion)
REFERENCES prototipo.ubicaciones(id_ubicacion);

-- Todo evento debe tener obligatoriamente una ubicacion

ALTER TABLE prototipo.eventos
ALTER COLUMN id_ubicacion SET NOT NULL;

-- Funcion para prevenir traslapes de eventos

CREATE OR REPLACE FUNCTION prototipo.fn_evitar_traslape_ubicacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM prototipo.eventos e
        WHERE e.id_ubicacion = NEW.id_ubicacion
          AND e.id_evento <> COALESCE(NEW.id_evento, -1)
          AND NEW.fecha_inicio < e.fecha_fin
          AND NEW.fecha_fin > e.fecha_inicio
    ) THEN
        RAISE EXCEPTION
            'La ubicacion ya posee un evento programado en ese horario';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger para validar traslapes de ubicacion

CREATE TRIGGER trg_evitar_traslape_ubicacion
BEFORE INSERT OR UPDATE
ON prototipo.eventos
FOR EACH ROW
EXECUTE FUNCTION prototipo.fn_evitar_traslape_ubicacion();

-- ============================================================
-- RF-10: Reporte Analitico de Ocupacion y Demanda
-- ============================================================

CREATE OR REPLACE VIEW prototipo.vista_ranking_ubicaciones AS
SELECT
    u.id_ubicacion,
    u.nombre,
    u.ciudad,
    COUNT(e.id_evento) AS cantidad_eventos
FROM prototipo.ubicaciones u
LEFT JOIN prototipo.eventos e
    ON u.id_ubicacion = e.id_ubicacion
GROUP BY
    u.id_ubicacion,
    u.nombre,
    u.ciudad;

-- ============================================================
-- RF-11: Registro y Control de Disponibilidades
-- ============================================================

-- Tabla tipos_disponibilidad

CREATE TABLE prototipo.tipos_disponibilidad (
    id_tipo_disponibilidad SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL,
    CONSTRAINT uq_tipo_disponibilidad_nombre
        UNIQUE (nombre)
);

-- Tabla disponibilidades

CREATE TABLE prototipo.disponibilidades (
    id_disponibilidad SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL,
    id_tipo_disponibilidad INTEGER NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,

    CONSTRAINT fk_disponibilidad_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES prototipo.usuarios(id_usuario),

    CONSTRAINT fk_disponibilidad_tipo
        FOREIGN KEY (id_tipo_disponibilidad)
        REFERENCES prototipo.tipos_disponibilidad(id_tipo_disponibilidad),

    CONSTRAINT check_horas_disponibilidad
        CHECK (hora_fin > hora_inicio)
);

-- Datos del catálogo

INSERT INTO prototipo.tipos_disponibilidad (nombre)
VALUES
('Disponible'),
('Ocupado'),
('No disponible');

-- ============================================================
-- RF-12: Analisis de Solapamientos e Intervalos de Tiempo
-- ============================================================

CREATE OR REPLACE FUNCTION prototipo.fn_usuarios_disponibles(
    p_fecha DATE,
    p_hora_inicio TIME,
    p_hora_fin TIME
)
RETURNS TABLE (
    id_usuario INTEGER,
    nombre VARCHAR(50),
    apellido VARCHAR(50)
)
LANGUAGE plpgsql
AS $$
BEGIN

    IF p_hora_fin <= p_hora_inicio THEN
        RAISE EXCEPTION
            'La hora final debe ser posterior a la hora inicial';
    END IF;

    RETURN QUERY
    SELECT DISTINCT
        u.id_usuario,
        u.nombre,
        u.apellido
    FROM prototipo.usuarios u
    JOIN prototipo.disponibilidades d
        ON d.id_usuario = u.id_usuario
    JOIN prototipo.tipos_disponibilidad td
        ON td.id_tipo_disponibilidad = d.id_tipo_disponibilidad
    WHERE u.activo = TRUE
      AND d.fecha = p_fecha
      AND td.nombre = 'Disponible'

      -- El horario solicitado debe estar dentro
      -- de una franja declarada como disponible
      AND d.hora_inicio <= p_hora_inicio
      AND d.hora_fin >= p_hora_fin

      -- No puede tener una franja ocupada o no disponible
      -- que se traslape con el horario solicitado
      AND NOT EXISTS (
          SELECT 1
          FROM prototipo.disponibilidades d2
          JOIN prototipo.tipos_disponibilidad td2
              ON td2.id_tipo_disponibilidad = d2.id_tipo_disponibilidad
          WHERE d2.id_usuario = u.id_usuario
            AND d2.fecha = p_fecha
            AND td2.nombre IN ('Ocupado', 'No disponible')
            AND d2.hora_inicio < p_hora_fin
            AND d2.hora_fin > p_hora_inicio
      )

      -- No puede tener un evento propio en ese horario
      AND NOT EXISTS (
          SELECT 1
          FROM prototipo.eventos e
          WHERE e.id_usuario_propietario = u.id_usuario
            AND e.fecha_inicio < (p_fecha + p_hora_fin)
            AND e.fecha_fin > (p_fecha + p_hora_inicio)
      )

      -- No puede participar como invitado en otro evento,
      -- excepto si rechazó la invitación
      AND NOT EXISTS (
          SELECT 1
          FROM prototipo.participaciones p
          JOIN prototipo.eventos e
              ON e.id_evento = p.id_evento
          WHERE p.id_invitado = u.id_usuario
            AND p.estado_confirmacion <> 'rechazado'
            AND e.fecha_inicio < (p_fecha + p_hora_fin)
            AND e.fecha_fin > (p_fecha + p_hora_inicio)
      );

END;
$$;

-- ============================================================
-- RF-15: Gestion de Tareas Asociadas a Eventos
-- ============================================================

CREATE TABLE prototipo.tareas (
    id_tarea SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    prioridad VARCHAR(20) NOT NULL,
    fecha_limite TIMESTAMP NOT NULL,
    estado VARCHAR(20) NOT NULL,
    id_evento INTEGER NOT NULL,
    id_responsable INTEGER NOT NULL,

    CONSTRAINT fk_tarea_evento
        FOREIGN KEY (id_evento)
        REFERENCES prototipo.eventos(id_evento),

    CONSTRAINT fk_tarea_responsable
        FOREIGN KEY (id_responsable)
        REFERENCES prototipo.usuarios(id_usuario),

    CONSTRAINT check_prioridad_tarea
        CHECK (prioridad IN ('Baja', 'Media', 'Alta')),

    CONSTRAINT check_estado_tarea
        CHECK (
            estado IN (
                'Pendiente',
                'En progreso',
                'Completada',
                'Cancelada'
            )
        )
);

-- ============================================================
-- RF-16: Consultas de Tareas Pendientes y Vencidas
-- ============================================================

CREATE OR REPLACE VIEW prototipo.vista_carga_trabajo AS
SELECT
    u.id_usuario,
    u.nombre,
    u.apellido,

    COUNT(t.id_tarea) FILTER (
        WHERE t.estado = 'Pendiente'
    ) AS tareas_pendientes,

    COUNT(t.id_tarea) FILTER (
        WHERE t.fecha_limite < CURRENT_TIMESTAMP
          AND t.estado IN ('Pendiente', 'En progreso')
    ) AS tareas_vencidas

FROM prototipo.usuarios u

LEFT JOIN prototipo.tareas t
    ON t.id_responsable = u.id_usuario

GROUP BY
    u.id_usuario,
    u.nombre,
    u.apellido;

CREATE OR REPLACE VIEW prototipo.vista_eventos_con_vencidas AS
SELECT
    e.id_evento,
    e.titulo AS titulo_evento,
    COUNT(t.id_tarea) AS cantidad_tareas_vencidas
FROM prototipo.eventos e
JOIN prototipo.tareas t
    ON t.id_evento = e.id_evento
WHERE t.fecha_limite < CURRENT_TIMESTAMP
  AND t.estado IN ('Pendiente', 'En progreso')
GROUP BY
    e.id_evento,
    e.titulo;

-- ============================================================
-- RF-17: Reporte de Tareas por Miembro del Equipo
-- ============================================================

CREATE OR REPLACE VIEW prototipo.vista_reporte_tareas_usuario AS
SELECT
    u.id_usuario,
    u.nombre,
    u.apellido,

    COUNT(t.id_tarea) FILTER (
        WHERE t.estado = 'Pendiente'
    ) AS tareas_pendientes,

    COUNT(t.id_tarea) FILTER (
        WHERE t.estado = 'En progreso'
    ) AS tareas_en_progreso,

    COUNT(t.id_tarea) FILTER (
        WHERE t.estado IN ('Pendiente', 'En progreso')
    ) AS tareas_activas,

    COUNT(t.id_tarea) FILTER (
        WHERE t.fecha_limite < CURRENT_TIMESTAMP
          AND t.estado IN ('Pendiente', 'En progreso')
    ) AS tareas_vencidas

FROM prototipo.usuarios u

LEFT JOIN prototipo.tareas t
    ON t.id_responsable = u.id_usuario

GROUP BY
    u.id_usuario,
    u.nombre,
    u.apellido;