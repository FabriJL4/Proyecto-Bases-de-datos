import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

import customtkinter as ctk
import psycopg2

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppAgenda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agenda 3 Patitos")
        self.geometry("1280x760")
        self.minsize(1050, 650)

        self.conn_params = {
            "dbname": "agenda",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": "5432",
        }

        self.usuarios_combo = {}
        self.categorias_combo = {}
        self.categorias_padre_combo = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.crear_sidebar()
        self.crear_area_principal()
        self.configurar_estilos()

        self.actualizar_todas_las_tablas()

        if DateEntry is None:
            self.after(500, lambda: messagebox.showwarning(
                "Calendario no instalado",
                "Para usar los selectores de fecha instala:\n\npip install tkcalendar"
            ))

    # -------------------- INFRAESTRUCTURA --------------------

    def obtener_conexion(self):
        conn = psycopg2.connect(**self.conn_params)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO prototipo, public;")
        return conn

    def ejecutar_consulta(self, sql, params=None, fetch=False):
        conn = None
        try:
            conn = self.obtener_conexion()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else None
            conn.commit()
            return rows
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def crear_treeview(self, parent, columnas, widths):
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        tree = ttk.Treeview(contenedor, columns=columnas, show="headings")
        for col, width in zip(columnas, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        return tree

    def seleccionar_modulo(self, nombre):
        self.tabview.set(nombre)
        for modulo, boton in self.botones_nav.items():
            boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=235, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="📅 AGENDA 🦆🦆🦆",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(28, 5), sticky="w")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Gestión de usuarios, categorías y eventos",
            font=ctk.CTkFont(size=11),
            wraplength=190,
            justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        self.botones_nav = {}
        for i, (nombre, icono) in enumerate([
            ("Usuarios", "👥"),
            ("Categorías", "📁"),
            ("Eventos", "🗓️"),
            ("Ubicaciones", "📍"),
            ("Disponibilidad", "⏰"),
            ("Tareas", "✅"),
        ], start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"{icono}  {nombre}",
                anchor="w", fg_color="transparent",
                command=lambda n=nombre: self.seleccionar_modulo(n)
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.botones_nav[nombre] = btn

        ctk.CTkButton(
            self.sidebar_frame,
            text="🔄  Recargar datos",
            command=self.actualizar_todas_las_tablas
        ).grid(row=9, column=0, padx=15, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="APARIENCIA", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=11, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.option_mode = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Dark", "Light"],
            command=ctk.set_appearance_mode
        )
        self.option_mode.set("System")
        self.option_mode.grid(row=12, column=0, padx=15, pady=(0, 25), sticky="ew")

    def crear_area_principal(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_container, command=self.al_cambiar_pestana)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_usuarios = self.tabview.add("Usuarios")
        self.tab_categorias = self.tabview.add("Categorías")
        self.tab_eventos = self.tabview.add("Eventos")
        self.tab_ubicaciones = self.tabview.add("Ubicaciones")
        self.tab_disponibilidad = self.tabview.add("Disponibilidad")
        self.tab_tareas = self.tabview.add("Tareas")

        self.configurar_pestana_usuarios()
        self.configurar_pestana_categorias()
        self.configurar_pestana_eventos()
        self.configurar_pestana_ubicaciones()
        self.configurar_pestana_disponibilidad()
        self.configurar_pestana_tareas()
        self.seleccionar_modulo("Usuarios")

    def al_cambiar_pestana(self):
        nombre = self.tabview.get()
        if nombre in self.botones_nav:
            for modulo, boton in self.botones_nav.items():
                boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_encabezado(self, parent, titulo, descripcion):
        ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 0)
        )
        ctk.CTkLabel(parent, text=descripcion, font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=15, pady=(0, 12)
        )

    # -------------------- USUARIOS --------------------

    def configurar_pestana_usuarios(self):
        self.crear_encabezado(self.tab_usuarios, "Usuarios", "Registra, consulta y administra los usuarios de la agenda.")

        cuerpo = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=300)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_usuarios = self.crear_treeview(
            tabla_frame, ("ID", "Nombre", "Apellido", "Registro", "Activo"),
            (70, 160, 160, 160, 80)
        )
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.cargar_usuario_seleccionado)

        ctk.CTkLabel(form, text="Formulario de usuario", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre")
        self.entry_nombre.pack(fill="x", padx=10, pady=6)
        self.entry_apellido = ctk.CTkEntry(form, placeholder_text="Apellido")
        self.entry_apellido.pack(fill="x", padx=10, pady=6)

        self.switch_usuario_activo = ctk.CTkSwitch(form, text="Usuario activo")
        self.switch_usuario_activo.select()
        self.switch_usuario_activo.pack(anchor="w", padx=12, pady=10)

        ctk.CTkButton(form, text="➕ Registrar usuario", command=self.agregar_usuario).pack(fill="x", padx=10, pady=(12, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_usuario).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_usuario, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_usuario, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def usuario_seleccionado_id(self):
        sel = self.tree_usuarios.selection()
        return self.tree_usuarios.item(sel[0])["values"][0] if sel else None

    def cargar_usuario_seleccionado(self, _=None):
        sel = self.tree_usuarios.selection()
        if not sel:
            return
        vals = self.tree_usuarios.item(sel[0])["values"]
        self.entry_nombre.delete(0, tk.END); self.entry_nombre.insert(0, vals[1])
        self.entry_apellido.delete(0, tk.END); self.entry_apellido.insert(0, vals[2])
        if vals[4]:
            self.switch_usuario_activo.select()
        else:
            self.switch_usuario_activo.deselect()

    def limpiar_form_usuario(self):
        self.tree_usuarios.selection_remove(self.tree_usuarios.selection())
        self.entry_nombre.delete(0, tk.END)
        self.entry_apellido.delete(0, tk.END)
        self.switch_usuario_activo.select()

    def agregar_usuario(self):
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("INSERT INTO usuarios (nombre, apellido, activo) VALUES (%s, %s, %s)",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario para actualizar.")
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("UPDATE usuarios SET nombre=%s, apellido=%s, activo=%s WHERE id_usuario=%s",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1, uid))
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario actualizado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el usuario seleccionado?"):
            return
        try:
            self.ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=%s", (uid,))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Usuario eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_usuarios(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_usuario, nombre, apellido, fecha_registro, activo FROM usuarios ORDER BY nombre, apellido",
                fetch=True
            )
            for item in self.tree_usuarios.get_children(): self.tree_usuarios.delete(item)
            self.usuarios_combo = {}
            for row in rows:
                registro = row[3].strftime("%Y-%m-%d %H:%M") if hasattr(row[3], "strftime") else row[3]
                self.tree_usuarios.insert("", "end", values=(row[0], row[1], row[2], registro, "Sí" if row[4] else "No"))
                etiqueta = f"{row[1]} {row[2]} — #{row[0]}"
                self.usuarios_combo[etiqueta] = row[0]
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    # -------------------- CATEGORÍAS --------------------

    def configurar_pestana_categorias(self):
        self.crear_encabezado(self.tab_categorias, "Categorías", "Organiza los eventos mediante categorías y subcategorías.")

        cuerpo = ctk.CTkFrame(self.tab_categorias, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=320); form.grid(row=0, column=1, sticky="nsew")

        self.tree_categorias = self.crear_treeview(tabla, ("ID", "Categoría", "Categoría padre"), (80, 230, 230))
        self.tree_categorias.bind("<<TreeviewSelect>>", self.cargar_categoria_seleccionada)

        ctk.CTkLabel(form, text="Formulario de categoría", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_cat_nombre = ctk.CTkEntry(form, placeholder_text="Nombre de la categoría")
        self.entry_cat_nombre.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Categoría padre").pack(anchor="w", padx=10, pady=(10, 2))
        self.combo_cat_padre = ctk.CTkComboBox(form, values=["Sin categoría padre"], state="readonly")
        self.combo_cat_padre.set("Sin categoría padre")
        self.combo_cat_padre.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(form, text="➕ Crear categoría", command=self.agregar_categoria).pack(fill="x", padx=10, pady=(15, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionada", command=self.actualizar_categoria).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nueva / Limpiar", command=self.limpiar_form_categoria, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionada", command=self.eliminar_categoria, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def categoria_seleccionada_id(self):
        sel = self.tree_categorias.selection()
        return self.tree_categorias.item(sel[0])["values"][0] if sel else None

    def cargar_categoria_seleccionada(self, _=None):
        sel = self.tree_categorias.selection()
        if not sel: return
        vals = self.tree_categorias.item(sel[0])["values"]
        self.entry_cat_nombre.delete(0, tk.END); self.entry_cat_nombre.insert(0, vals[1])
        padre = vals[2]
        self.combo_cat_padre.set(padre if padre in self.categorias_padre_combo else "Sin categoría padre")

    def limpiar_form_categoria(self):
        self.tree_categorias.selection_remove(self.tree_categorias.selection())
        self.entry_cat_nombre.delete(0, tk.END); self.combo_cat_padre.set("Sin categoría padre")

    def _padre_id_actual(self):
        valor = self.combo_cat_padre.get()
        return None if valor == "Sin categoría padre" else self.categorias_padre_combo.get(valor)

    def agregar_categoria(self):
        nombre = self.entry_cat_nombre.get().strip()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre de la categoría.")
        try:
            self.ejecutar_consulta("INSERT INTO categorias (nombre, id_categoria_padre) VALUES (%s, %s)",
                                   (nombre, self._padre_id_actual()))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Categoría creada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        nombre = self.entry_cat_nombre.get().strip(); padre = self._padre_id_actual()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre.")
        if padre == cid: return messagebox.showwarning("Relación inválida", "Una categoría no puede ser su propia categoría padre.")
        try:
            self.ejecutar_consulta("UPDATE categorias SET nombre=%s, id_categoria_padre=%s WHERE id_categoria=%s",
                                   (nombre, padre, cid))
            self.actualizar_todas_las_tablas(); messagebox.showinfo("Éxito", "Categoría actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la categoría seleccionada?"): return
        try:
            self.ejecutar_consulta("DELETE FROM categorias WHERE id_categoria=%s", (cid,))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Categoría eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_categorias(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT c.id_categoria, c.nombre, p.nombre
                FROM categorias c
                LEFT JOIN categorias p ON p.id_categoria = c.id_categoria_padre
                ORDER BY c.nombre
            """, fetch=True)
            ids = self.ejecutar_consulta("SELECT id_categoria, nombre FROM categorias ORDER BY nombre", fetch=True)

            for item in self.tree_categorias.get_children(): self.tree_categorias.delete(item)
            self.categorias_combo = {}
            self.categorias_padre_combo = {}
            for cid, nombre in ids:
                etiqueta = f"{nombre} — #{cid}"
                self.categorias_combo[etiqueta] = cid
                self.categorias_padre_combo[etiqueta] = cid
            for row in rows:
                padre = "Sin categoría padre"
                if row[2] is not None:
                    # Buscar etiqueta completa del padre
                    for etiqueta, cid in self.categorias_padre_combo.items():
                        if etiqueta.startswith(f"{row[2]} —"):
                            padre = etiqueta; break
                self.tree_categorias.insert("", "end", values=(row[0], row[1], padre))

            valores_padre = ["Sin categoría padre"] + list(self.categorias_padre_combo.keys())
            self.combo_cat_padre.configure(values=valores_padre)
            if self.combo_cat_padre.get() not in valores_padre:
                self.combo_cat_padre.set("Sin categoría padre")
        except Exception as e:
            print(f"Error cargando categorías: {e}")

    # -------------------- EVENTOS --------------------

    def configurar_pestana_eventos(self):
        self.crear_encabezado(self.tab_eventos, "Eventos", "Programa eventos seleccionando usuarios, categorías, fechas y horas.")

        cuerpo = ctk.CTkFrame(self.tab_eventos, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=350); form.grid(row=0, column=1, sticky="nsew")

        self.tree_eventos = self.crear_treeview(
            tabla,
            ("ID", "Propietario", "Categoría", "Ubicación", "Título", "Inicio", "Fin"),
            (70, 170, 150, 170, 220, 150, 150)
        )
        self.tree_eventos.bind("<<TreeviewSelect>>", self.cargar_evento_seleccionado)

        ctk.CTkLabel(form, text="Formulario de evento", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 12))

        self.entry_ev_titulo = ctk.CTkEntry(form, placeholder_text="Título del evento")
        self.entry_ev_titulo.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Propietario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_usuario = ctk.CTkComboBox(form, values=["Seleccione un usuario"], state="readonly")
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Categoría").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_categoria = ctk.CTkComboBox(form, values=["Seleccione una categoría"], state="readonly")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_categoria.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Ubicación").pack(anchor="w", padx=10, pady=(8, 2))

        self.combo_ev_ubicacion = ctk.CTkComboBox(
            form,
            values=["Seleccione una ubicación"],
            state="readonly"
        )

        self.combo_ev_ubicacion.set("Seleccione una ubicación")
        self.combo_ev_ubicacion.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Inicio").pack(anchor="w", padx=10, pady=(10, 2))
        fila_inicio = ctk.CTkFrame(form, fg_color="transparent"); fila_inicio.pack(fill="x", padx=10)
        self.fecha_inicio = self.crear_selector_fecha(fila_inicio)
        self.fecha_inicio.pack(side="left", fill="x", expand=True)
        self.hora_inicio = ctk.CTkEntry(fila_inicio, placeholder_text="HH:MM", width=75)
        self.hora_inicio.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form, text="Fin").pack(anchor="w", padx=10, pady=(10, 2))
        fila_fin = ctk.CTkFrame(form, fg_color="transparent"); fila_fin.pack(fill="x", padx=10)
        self.fecha_fin = self.crear_selector_fecha(fila_fin)
        self.fecha_fin.pack(side="left", fill="x", expand=True)
        self.hora_fin = ctk.CTkEntry(fila_fin, placeholder_text="HH:MM", width=75)
        self.hora_fin.pack(side="left", padx=(6, 0))

        ctk.CTkButton(form, text="➕ Crear evento", command=self.agregar_evento).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_evento).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_evento, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_evento, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_evento()

    def crear_selector_fecha(self, parent):
        if DateEntry is not None:
            return DateEntry(parent, date_pattern="yyyy-mm-dd", font=("Arial", 10))
        return ttk.Entry(parent)

    def obtener_fecha(self, widget):
        if DateEntry is not None:
            return widget.get_date().strftime("%Y-%m-%d")
        return widget.get().strip()

    def establecer_fecha(self, widget, valor):
        fecha = valor.date() if hasattr(valor, "date") else datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
        if DateEntry is not None:
            widget.set_date(fecha)
        else:
            widget.delete(0, tk.END); widget.insert(0, fecha.strftime("%Y-%m-%d"))

    def evento_seleccionado_id(self):
        sel = self.tree_eventos.selection()
        return self.tree_eventos.item(sel[0])["values"][0] if sel else None

    def cargar_evento_seleccionado(self, _=None):
        sel = self.tree_eventos.selection()

        if not sel:
            return

        vals = self.tree_eventos.item(sel[0])["values"]

        self.entry_ev_titulo.delete(0, tk.END)
        self.entry_ev_titulo.insert(0, vals[4])

        self.combo_ev_usuario.set(vals[1])
        self.combo_ev_categoria.set(vals[2])
        self.combo_ev_ubicacion.set(vals[3])

        try:
            ini = datetime.strptime(
                str(vals[5]),
                "%Y-%m-%d %H:%M"
            )

            fin = datetime.strptime(
                str(vals[6]),
                "%Y-%m-%d %H:%M"
            )

            self.establecer_fecha(self.fecha_inicio, ini)
            self.establecer_fecha(self.fecha_fin, fin)

            self.hora_inicio.delete(0, tk.END)
            self.hora_inicio.insert(0, ini.strftime("%H:%M"))

            self.hora_fin.delete(0, tk.END)
            self.hora_fin.insert(0, fin.strftime("%H:%M"))

        except ValueError:
            pass

    def limpiar_form_evento(self):
        self.tree_eventos.selection_remove(self.tree_eventos.selection())
        self.entry_ev_titulo.delete(0, tk.END)
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_ubicacion.set("Seleccione una ubicación")
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_inicio, hoy); self.establecer_fecha(self.fecha_fin, hoy)
        self.hora_inicio.delete(0, tk.END); self.hora_inicio.insert(0, "09:00")
        self.hora_fin.delete(0, tk.END); self.hora_fin.insert(0, "10:00")

    def datos_evento_formulario(self):
        titulo = self.entry_ev_titulo.get().strip()

        usuario = self.usuarios_combo.get(
            self.combo_ev_usuario.get()
        )

        categoria = self.categorias_combo.get(
            self.combo_ev_categoria.get()
        )

        ubicacion = self.ubicaciones_combo.get(
            self.combo_ev_ubicacion.get()
        )

        try:
            inicio = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_inicio)} "
                f"{self.hora_inicio.get().strip()}",
                "%Y-%m-%d %H:%M"
            )

            fin = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_fin)} "
                f"{self.hora_fin.get().strip()}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:
            raise ValueError(
                "La hora debe tener formato HH:MM, por ejemplo 09:30."
            )

        if (
            not titulo
            or usuario is None
            or categoria is None
            or ubicacion is None
        ):
            raise ValueError(
                "Completa título, propietario, categoría y ubicación."
            )

        if fin <= inicio:
            raise ValueError(
                "La fecha y hora de finalización deben ser posteriores al inicio."
            )

        return usuario, categoria, ubicacion, titulo, inicio, fin

    def agregar_evento(self):
        try:
            datos = self.datos_evento_formulario()

            self.ejecutar_consulta(
                """
                INSERT INTO eventos (
                    id_usuario_propietario,
                    id_categoria,
                    id_ubicacion,
                    titulo,
                    fecha_inicio,
                    fecha_fin
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                datos
            )

            self.limpiar_form_evento()
            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Evento creado correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo crear el evento",
                str(e)
            )

    def actualizar_evento(self):
        eid = self.evento_seleccionado_id()

        if eid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona un evento."
            )

        try:
            usuario, categoria, ubicacion, titulo, inicio, fin = (
                self.datos_evento_formulario()
            )

            self.ejecutar_consulta(
                """
                UPDATE eventos
                SET id_usuario_propietario=%s,
                    id_categoria=%s,
                    id_ubicacion=%s,
                    titulo=%s,
                    fecha_inicio=%s,
                    fecha_fin=%s
                WHERE id_evento=%s
                """,
                (
                    usuario,
                    categoria,
                    ubicacion,
                    titulo,
                    inicio,
                    fin,
                    eid
                )
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Evento actualizado."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo actualizar",
                str(e)
            )

    def eliminar_evento(self):
        eid = self.evento_seleccionado_id()

        if eid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona un evento."
            )

        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar el evento seleccionado?"
        ):
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM eventos WHERE id_evento=%s",
                (eid,)
            )

            self.limpiar_form_evento()
            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Eliminado",
                "Evento eliminado."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def cargar_datos_eventos(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT
                    e.id_evento,
                    u.id_usuario,
                    u.nombre,
                    u.apellido,
                    c.id_categoria,
                    c.nombre,
                    ub.id_ubicacion,
                    ub.nombre,
                    e.titulo,
                    e.fecha_inicio,
                    e.fecha_fin
                FROM eventos e
                JOIN usuarios u
                    ON u.id_usuario = e.id_usuario_propietario
                JOIN categorias c
                    ON c.id_categoria = e.id_categoria
                JOIN ubicaciones ub
                    ON ub.id_ubicacion = e.id_ubicacion
                ORDER BY e.fecha_inicio DESC
            """, fetch=True)

            for item in self.tree_eventos.get_children():
                self.tree_eventos.delete(item)

            for row in rows:
                usuario = f"{row[2]} {row[3]} — #{row[1]}"
                categoria = f"{row[5]} — #{row[4]}"
                ubicacion = f"{row[7]} — #{row[6]}"

                inicio = (
                    row[9].strftime("%Y-%m-%d %H:%M")
                    if hasattr(row[9], "strftime")
                    else row[9]
                )

                fin = (
                    row[10].strftime("%Y-%m-%d %H:%M")
                    if hasattr(row[10], "strftime")
                    else row[10]
                )

                self.tree_eventos.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        usuario,
                        categoria,
                        ubicacion,
                        row[8],
                        inicio,
                        fin
                    )
                )

            valores_u = ["Seleccione un usuario"] + list(
                self.usuarios_combo.keys()
            )

            valores_c = ["Seleccione una categoría"] + list(
                self.categorias_combo.keys()
            )

            valores_ub = ["Seleccione una ubicación"] + list(
                self.ubicaciones_combo.keys()
            )

            self.combo_ev_usuario.configure(values=valores_u)
            self.combo_ev_categoria.configure(values=valores_c)
            self.combo_ev_ubicacion.configure(values=valores_ub)

        except Exception as e:
            print(f"Error cargando eventos: {e}")

    # -------------------- UBICACIONES --------------------

    def configurar_pestana_ubicaciones(self):
        self.crear_encabezado(
            self.tab_ubicaciones,
            "Ubicaciones",
            "Registra, consulta y administra las ubicaciones físicas de los eventos."
        )

        cuerpo = ctk.CTkFrame(self.tab_ubicaciones, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkScrollableFrame(cuerpo, width=300)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_ubicaciones = self.crear_treeview(
            tabla_frame,
            ("ID", "Nombre", "Dirección", "Ciudad", "Capacidad"),
            (70, 180, 220, 150, 100)
        )

        self.tree_ubicaciones.bind(
            "<<TreeviewSelect>>",
            self.cargar_ubicacion_seleccionada
    )

        ctk.CTkLabel(
            form,
            text="Formulario de ubicación",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        self.entry_ubicacion_nombre = ctk.CTkEntry(
            form,
            placeholder_text="Nombre"
        )
        self.entry_ubicacion_nombre.pack(fill="x", padx=10, pady=6)

        self.entry_ubicacion_direccion = ctk.CTkEntry(
            form,
            placeholder_text="Dirección"
        )
        self.entry_ubicacion_direccion.pack(fill="x", padx=10, pady=6)

        self.entry_ubicacion_ciudad = ctk.CTkEntry(
            form,
            placeholder_text="Ciudad"
        )
        self.entry_ubicacion_ciudad.pack(fill="x", padx=10, pady=6)

        self.entry_ubicacion_capacidad = ctk.CTkEntry(
            form,
            placeholder_text="Capacidad"
        )
        self.entry_ubicacion_capacidad.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(
            form,
            text="➕ Registrar ubicación",
            command=self.agregar_ubicacion
        ).pack(fill="x", padx=10, pady=(12, 5))

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionado",
            command=self.actualizar_ubicacion
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🧹 Nuevo / Limpiar",
            command=self.limpiar_form_ubicacion,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionado",
            command=self.eliminar_ubicacion,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="📊 Ver ranking de ubicaciones",
            command=self.mostrar_ranking_ubicaciones
        ).pack(fill="x", padx=10, pady=(20, 5))

    def ubicacion_seleccionada_id(self):
        sel = self.tree_ubicaciones.selection()

        if not sel:
            return None

        return self.tree_ubicaciones.item(sel[0])["values"][0]


    def cargar_ubicacion_seleccionada(self, _=None):
        sel = self.tree_ubicaciones.selection()

        if not sel:
            return

        vals = self.tree_ubicaciones.item(sel[0])["values"]

        self.entry_ubicacion_nombre.delete(0, tk.END)
        self.entry_ubicacion_nombre.insert(0, vals[1])

        self.entry_ubicacion_direccion.delete(0, tk.END)
        self.entry_ubicacion_direccion.insert(0, vals[2])

        self.entry_ubicacion_ciudad.delete(0, tk.END)
        self.entry_ubicacion_ciudad.insert(0, vals[3])

        self.entry_ubicacion_capacidad.delete(0, tk.END)
        self.entry_ubicacion_capacidad.insert(0, vals[4])

    def agregar_ubicacion(self):
        nombre = self.entry_ubicacion_nombre.get().strip()
        direccion = self.entry_ubicacion_direccion.get().strip()
        ciudad = self.entry_ubicacion_ciudad.get().strip()
        capacidad = self.entry_ubicacion_capacidad.get().strip()

        if not nombre or not direccion or not ciudad or not capacidad:
            return messagebox.showwarning(
                "Campos incompletos",
                "Completa todos los campos de la ubicación."
            )

        try:
            capacidad = int(capacidad)

            if capacidad <= 0:
                return messagebox.showwarning(
                    "Capacidad inválida",
                    "La capacidad debe ser mayor que cero."
                )

        except ValueError:
            return messagebox.showwarning(
                "Capacidad inválida",
                "La capacidad debe ser un número entero."
            )

        try:
            self.ejecutar_consulta(
                """
                INSERT INTO ubicaciones (
                    nombre,
                    direccion,
                    ciudad,
                    capacidad
                )
                VALUES (%s, %s, %s, %s)
                """,
                (nombre, direccion, ciudad, capacidad)
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Ubicación registrada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "Error de base de datos",
                str(e)
            )

    def actualizar_ubicacion(self):
        uid = self.ubicacion_seleccionada_id()

        if uid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una ubicación para actualizar."
            )

        nombre = self.entry_ubicacion_nombre.get().strip()
        direccion = self.entry_ubicacion_direccion.get().strip()
        ciudad = self.entry_ubicacion_ciudad.get().strip()
        capacidad = self.entry_ubicacion_capacidad.get().strip()

        if not nombre or not direccion or not ciudad or not capacidad:
            return messagebox.showwarning(
                "Campos incompletos",
                "Completa todos los campos de la ubicación."
            )

        try:
            capacidad = int(capacidad)

            if capacidad <= 0:
                return messagebox.showwarning(
                    "Capacidad inválida",
                    "La capacidad debe ser mayor que cero."
                )

        except ValueError:
            return messagebox.showwarning(
                "Capacidad inválida",
                "La capacidad debe ser un número entero."
            )

        try:
            self.ejecutar_consulta(
                """
                UPDATE ubicaciones
                SET nombre=%s,
                    direccion=%s,
                    ciudad=%s,
                    capacidad=%s
                WHERE id_ubicacion=%s
                """,
                (nombre, direccion, ciudad, capacidad, uid)
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Ubicación actualizada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "Error de base de datos",
                str(e)
            )

    def limpiar_form_ubicacion(self):
        self.tree_ubicaciones.selection_remove(
            self.tree_ubicaciones.selection()
        )

        self.entry_ubicacion_nombre.delete(0, tk.END)
        self.entry_ubicacion_direccion.delete(0, tk.END)
        self.entry_ubicacion_ciudad.delete(0, tk.END)
        self.entry_ubicacion_capacidad.delete(0, tk.END)

    def eliminar_ubicacion(self):
        uid = self.ubicacion_seleccionada_id()

        if uid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una ubicación para eliminar."
            )

        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la ubicación seleccionada?"
        ):
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM ubicaciones WHERE id_ubicacion=%s",
                (uid,)
            )

            self.limpiar_form_ubicacion()
            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Eliminado",
                "Ubicación eliminada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def mostrar_ranking_ubicaciones(self):
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT
                    id_ubicacion,
                    nombre,
                    ciudad,
                    cantidad_eventos
                FROM vista_ranking_ubicaciones
                ORDER BY cantidad_eventos DESC, nombre
                """,
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Ranking de Ubicaciones")
            ventana.geometry("700x450")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana,
                text="Ranking de Ubicaciones",
                font=ctk.CTkFont(size=22, weight="bold")
            ).pack(anchor="w", padx=20, pady=(20, 5))

            ctk.CTkLabel(
                ventana,
                text="Cantidad de eventos registrados por ubicación."
            ).pack(anchor="w", padx=20, pady=(0, 15))

            tabla_frame = ctk.CTkFrame(ventana)
            tabla_frame.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=(0, 20)
            )

            tree = self.crear_treeview(
                tabla_frame,
                ("ID", "Ubicación", "Ciudad", "Eventos"),
                (70, 220, 180, 100)
            )

            for row in rows:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        row[3]
                    )
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    def cargar_datos_ubicaciones(self):
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT
                    id_ubicacion,
                    nombre,
                    direccion,
                    ciudad,
                    capacidad
                FROM ubicaciones
                ORDER BY nombre
                """,
                fetch=True
            )

            for item in self.tree_ubicaciones.get_children():
                self.tree_ubicaciones.delete(item)

            self.ubicaciones_combo = {}

            for row in rows:
                self.tree_ubicaciones.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        row[4]
                    )
                )
                etiqueta = f"{row[1]} — #{row[0]}"
                self.ubicaciones_combo[etiqueta] = row[0]
                
            valores = ["Seleccione una ubicación"] + list(self.ubicaciones_combo.keys())
            self.combo_ev_ubicacion.configure(values=valores)

        except Exception as e:
            print(f"Error cargando ubicaciones: {e}")

    # -------------------- DISPONIBILIDAD --------------------
    
    def configurar_pestana_disponibilidad(self):
        self.crear_encabezado(
            self.tab_disponibilidad,
            "Disponibilidad de Usuarios",
            "Registra y administra los intervalos de disponibilidad de cada usuario."
        )

        cuerpo = ctk.CTkFrame(
            self.tab_disponibilidad,
            fg_color="transparent"
        )
        cuerpo.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5 
        )

        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        form = ctk.CTkScrollableFrame(
            cuerpo,
            width=320
        )
        form.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.tree_disponibilidades = self.crear_treeview(
            tabla_frame,
            (
                "ID",
                "Usuario",
                "Tipo",
                "Fecha",
                "Inicio",
                "Fin"
            ),
            (
                70,
                190,
                130,
                110,
                90,
                90
            )
        )

        self.tree_disponibilidades.bind(
            "<<TreeviewSelect>>",
            self.cargar_disponibilidad_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de disponibilidad",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).pack(
            pady=(10, 15)
        )

        ctk.CTkLabel(
            form,
            text="Usuario"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_disp_usuario = ctk.CTkComboBox(
            form,
            values=["Seleccione un usuario"],
            state="readonly"
        )
        self.combo_disp_usuario.set(
            "Seleccione un usuario"
        )
        self.combo_disp_usuario.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Tipo de disponibilidad"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_disp_tipo = ctk.CTkComboBox(
            form,
            values=["Seleccione un tipo"],
            state="readonly"
        )
        self.combo_disp_tipo.set(
            "Seleccione un tipo"
        )
        self.combo_disp_tipo.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Fecha"
        ).pack(
            anchor="w",
            padx=10,
            pady=(10, 2)
        )

        self.fecha_disponibilidad = self.crear_selector_fecha(form)
        self.fecha_disponibilidad.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Hora de inicio"
        ).pack(
            anchor="w",
            padx=10,
            pady=(10, 2)
        )

        self.entry_disp_inicio = ctk.CTkEntry(
            form,
            placeholder_text="HH:MM"
        )
        self.entry_disp_inicio.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Hora de fin"
        ).pack(
            anchor="w",
            padx=10,
            pady=(10, 2)
        )

        self.entry_disp_fin = ctk.CTkEntry(
            form,
            placeholder_text="HH:MM"
        )
        self.entry_disp_fin.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkButton(
            form,
            text="➕ Registrar disponibilidad",
            command=self.agregar_disponibilidad
        ).pack(
            fill="x",
            padx=10,
            pady=(16, 5)
        )

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionado",
            command=self.actualizar_disponibilidad
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🧹 Nuevo / Limpiar",
            command=self.limpiar_form_disponibilidad,
            fg_color="gray"
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionado",
            command=self.eliminar_disponibilidad,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🔎 Consultar usuarios disponibles",
            command=self.consultar_usuarios_disponibles
        ).pack(
            fill="x",
            padx=10,
            pady=(20, 5)
       )

    def cargar_datos_disponibilidades(self):
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT
                    d.id_disponibilidad,
                    u.id_usuario,
                    u.nombre,
                    u.apellido,
                    td.id_tipo_disponibilidad,
                    td.nombre,
                    d.fecha,
                    d.hora_inicio,
                    d.hora_fin
                FROM disponibilidades d
                JOIN usuarios u
                    ON u.id_usuario = d.id_usuario
                JOIN tipos_disponibilidad td
                    ON td.id_tipo_disponibilidad = d.id_tipo_disponibilidad
                ORDER BY d.fecha, d.hora_inicio
                """,
                fetch=True
            )

            for item in self.tree_disponibilidades.get_children():
                self.tree_disponibilidades.delete(item)

            for row in rows:
                usuario = f"{row[2]} {row[3]} — #{row[1]}"
                tipo = f"{row[5]} — #{row[4]}"

                fecha = (
                    row[6].strftime("%Y-%m-%d")
                    if hasattr(row[6], "strftime")
                    else row[6]
                )

                inicio = (
                    row[7].strftime("%H:%M")
                    if hasattr(row[7], "strftime")
                    else row[7]
                )

                fin = (
                    row[8].strftime("%H:%M")
                    if hasattr(row[8], "strftime")
                    else row[8]
                )

                self.tree_disponibilidades.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        usuario,
                        tipo,
                        fecha,
                        inicio,
                        fin
                    )
                )

            # Usuarios
            valores_usuarios = (
                ["Seleccione un usuario"]
                + list(self.usuarios_combo.keys())
            )

            self.combo_disp_usuario.configure(
                values=valores_usuarios
            )

            # Tipos de disponibilidad
            tipos = self.ejecutar_consulta(
                """
                SELECT
                    id_tipo_disponibilidad,
                    nombre
                FROM tipos_disponibilidad
                ORDER BY id_tipo_disponibilidad
                """,
                fetch=True
            )

            self.tipos_disponibilidad_combo = {}

            for tipo in tipos:
                etiqueta = f"{tipo[1]} — #{tipo[0]}"
                self.tipos_disponibilidad_combo[etiqueta] = tipo[0]

            valores_tipos = (
                ["Seleccione un tipo"]
                + list(self.tipos_disponibilidad_combo.keys())
            )

            self.combo_disp_tipo.configure(
                values=valores_tipos
            )

        except Exception as e:
            print(f"Error cargando disponibilidades: {e}")

    def disponibilidad_seleccionada_id(self):
        sel = self.tree_disponibilidades.selection()

        if not sel:
            return None

        return self.tree_disponibilidades.item(sel[0])["values"][0]


    def cargar_disponibilidad_seleccionada(self, _=None):
        sel = self.tree_disponibilidades.selection()

        if not sel:
            return

        vals = self.tree_disponibilidades.item(sel[0])["values"]

        self.combo_disp_usuario.set(vals[1])
        self.combo_disp_tipo.set(vals[2])

        try:
            fecha = datetime.strptime(
                str(vals[3]),
                "%Y-%m-%d"
            )

            self.establecer_fecha(
                self.fecha_disponibilidad,
                fecha
            )

        except ValueError:
            pass

        self.entry_disp_inicio.delete(0, tk.END)
        self.entry_disp_inicio.insert(0, vals[4])

        self.entry_disp_fin.delete(0, tk.END)
        self.entry_disp_fin.insert(0, vals[5])        

    def agregar_disponibilidad(self):
        usuario = self.usuarios_combo.get(
            self.combo_disp_usuario.get()
        )

        tipo = self.tipos_disponibilidad_combo.get(
            self.combo_disp_tipo.get()
        )

        fecha = self.obtener_fecha(
            self.fecha_disponibilidad
        )

        hora_inicio = self.entry_disp_inicio.get().strip()
        hora_fin = self.entry_disp_fin.get().strip()

        if usuario is None or tipo is None:
            return messagebox.showwarning(
                "Campos incompletos",
                "Selecciona un usuario y un tipo de disponibilidad."
            )

        if not hora_inicio or not hora_fin:
            return messagebox.showwarning(
                "Campos incompletos",
                "Indica la hora de inicio y la hora de fin."
            )

        try:
            inicio = datetime.strptime(
                hora_inicio,
                "%H:%M"
            ).time()

            fin = datetime.strptime(
                hora_fin,
                "%H:%M"
            ).time()

        except ValueError:
            return messagebox.showwarning(
                "Hora inválida",
                "La hora debe tener formato HH:MM, por ejemplo 09:30."
            )

        if fin <= inicio:
            return messagebox.showwarning(
                "Intervalo inválido",
                "La hora final debe ser posterior a la hora inicial."
            )

        try:
            self.ejecutar_consulta(
                """
                INSERT INTO disponibilidades (
                    id_usuario,
                    id_tipo_disponibilidad,
                    fecha,
                    hora_inicio,
                    hora_fin
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    usuario,
                    tipo,
                    fecha,
                    inicio,
                    fin
                )
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Disponibilidad registrada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo registrar",
                str(e)
            )

    def actualizar_disponibilidad(self):
        did = self.disponibilidad_seleccionada_id()

        if did is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una disponibilidad para actualizar."
            )

        usuario = self.usuarios_combo.get(
            self.combo_disp_usuario.get()
        )

        tipo = self.tipos_disponibilidad_combo.get(
            self.combo_disp_tipo.get()
        )

        fecha = self.obtener_fecha(
            self.fecha_disponibilidad
        )

        hora_inicio = self.entry_disp_inicio.get().strip()
        hora_fin = self.entry_disp_fin.get().strip()

        if usuario is None or tipo is None:
            return messagebox.showwarning(
                "Campos incompletos",
                "Selecciona un usuario y un tipo de disponibilidad."
            )

        if not hora_inicio or not hora_fin:
            return messagebox.showwarning(
                "Campos incompletos",
                "Indica la hora de inicio y la hora de fin."
            )

        try:
            inicio = datetime.strptime(
                hora_inicio,
                "%H:%M"
            ).time()

            fin = datetime.strptime(
                hora_fin,
                "%H:%M"
            ).time()

        except ValueError:
            return messagebox.showwarning(
                "Hora inválida",
                "La hora debe tener formato HH:MM, por ejemplo 09:30."
            )

        if fin <= inicio:
            return messagebox.showwarning(
                "Intervalo inválido",
                "La hora final debe ser posterior a la hora inicial."
            )

        try:
            self.ejecutar_consulta(
                """
                UPDATE disponibilidades
                SET id_usuario=%s,
                    id_tipo_disponibilidad=%s,
                    fecha=%s,
                    hora_inicio=%s,
                    hora_fin=%s
                WHERE id_disponibilidad=%s
                """,
                (
                    usuario,
                    tipo,
                    fecha,
                    inicio,
                    fin,
                    did
                )
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Disponibilidad actualizada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo actualizar",
                str(e)
            )

    def limpiar_form_disponibilidad(self):
        self.tree_disponibilidades.selection_remove(
            self.tree_disponibilidades.selection()
        )

        self.tree_disponibilidades.focus("")

        self.combo_disp_usuario.set(
            "Seleccione un usuario"
        )

        self.combo_disp_tipo.set(
            "Seleccione un tipo"
        )

        hoy = datetime.now()

        self.establecer_fecha(
            self.fecha_disponibilidad,
            hoy
        )

        self.entry_disp_inicio.delete(0, tk.END)
        self.entry_disp_inicio.insert(0, "09:00")

        self.entry_disp_fin.delete(0, tk.END)
        self.entry_disp_fin.insert(0, "10:00")

    def eliminar_disponibilidad(self):
        did = self.disponibilidad_seleccionada_id()

        if did is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una disponibilidad para eliminar."
            )

        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la disponibilidad seleccionada?"
        ):
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM disponibilidades WHERE id_disponibilidad=%s",
                (did,)
            )

            self.limpiar_form_disponibilidad()
            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Eliminado",
                "Disponibilidad eliminada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def consultar_usuarios_disponibles(self):
        fecha = self.obtener_fecha(
            self.fecha_disponibilidad
        )

        hora_inicio = self.entry_disp_inicio.get().strip()
        hora_fin = self.entry_disp_fin.get().strip()

        try:
            inicio = datetime.strptime(
                hora_inicio,
                "%H:%M"
            ).time()

            fin = datetime.strptime(
                hora_fin,
                "%H:%M"
            ).time()

        except ValueError:
            return messagebox.showwarning(
                "Hora inválida",
                "La hora debe tener formato HH:MM, por ejemplo 09:30."
            )

        if fin <= inicio:
            return messagebox.showwarning(
                "Intervalo inválido",
                "La hora final debe ser posterior a la hora inicial."
            )

        try:
            rows = self.ejecutar_consulta(
                """
                SELECT
                    id_usuario,
                    nombre,
                    apellido
                FROM fn_usuarios_disponibles(
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    fecha,
                    inicio,
                    fin
                ),
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Usuarios disponibles")
            ventana.geometry("600x400")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana,
                text="Usuarios disponibles",
                font=ctk.CTkFont(
                    size=22,
                    weight="bold"
                )
            ).pack(
                anchor="w",
                padx=20,
                pady=(20, 5)
            )

            ctk.CTkLabel(
                ventana,
                text=f"{fecha}  |  {hora_inicio} - {hora_fin}"
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 15)
            )

            tabla_frame = ctk.CTkFrame(ventana)
            tabla_frame.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=(0, 20)
            )

            tree = self.crear_treeview(
                tabla_frame,
                (
                    "ID",
                    "Nombre",
                    "Apellido"
                ),
                (
                    80,
                    200,
                    200
                )
            )

            for row in rows:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2]
                    )
                )

            if not rows:
                messagebox.showinfo(
                    "Sin resultados",
                    "No hay usuarios disponibles para ese horario."
                )

        except Exception as e:
            messagebox.showerror(
                "No se pudo realizar la consulta",
                str(e)
            )

    # -------------------- TAREAS ---------------------

    def configurar_pestana_tareas(self):
        self.crear_encabezado(
            self.tab_tareas,
            "Tareas",
            "Gestiona tareas asociadas a eventos, responsables, prioridades y estados."
        )

        cuerpo = ctk.CTkFrame(
            self.tab_tareas,
            fg_color="transparent"
        )
        cuerpo.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        form = ctk.CTkScrollableFrame(
            cuerpo,
            width=340
        )
        form.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.tree_tareas = self.crear_treeview(
            tabla_frame,
            (
                "ID",
                "Título",
                "Prioridad",
                "Estado",
                "Vencimiento",
                "Evento",
                "Responsable"
            ),
            (
                60,
                180,
                90,
                110,
                150,
                180,
                180
            )
        )

        
        self.tree_tareas.bind(
            "<<TreeviewSelect>>",
            self.cargar_tarea_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de tarea",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).pack(
            pady=(10, 15)
        )

        self.entry_tarea_titulo = ctk.CTkEntry(
            form,
            placeholder_text="Título de la tarea"
        )
        self.entry_tarea_titulo.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.entry_tarea_descripcion = ctk.CTkEntry(
            form,
            placeholder_text="Descripción"
        )
        self.entry_tarea_descripcion.pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkLabel(
            form,
            text="Prioridad"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_tarea_prioridad = ctk.CTkComboBox(
            form,
            values=["Baja", "Media", "Alta"],
            state="readonly"
        )
        self.combo_tarea_prioridad.set("Media")
        self.combo_tarea_prioridad.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Estado"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_tarea_estado = ctk.CTkComboBox(
            form,
            values=[
                "Pendiente",
                "En progreso",
                "Completada",
                "Cancelada"
            ],
            state="readonly"
        )
        self.combo_tarea_estado.set("Pendiente")
        self.combo_tarea_estado.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Evento"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_tarea_evento = ctk.CTkComboBox(
            form,
            values=["Seleccione un evento"],
            state="readonly"
        )
        self.combo_tarea_evento.set("Seleccione un evento")
        self.combo_tarea_evento.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Responsable"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_tarea_responsable = ctk.CTkComboBox(
            form,
            values=["Seleccione un usuario"],
            state="readonly"
        )
        self.combo_tarea_responsable.set("Seleccione un usuario")
        self.combo_tarea_responsable.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Fecha límite"
        ).pack(
            anchor="w",
            padx=10,
            pady=(10, 2)
        )

        self.fecha_tarea_limite = self.crear_selector_fecha(form)
        self.fecha_tarea_limite.pack(
            fill="x",
            padx=10,
            pady=4
        )

        self.entry_tarea_hora_limite = ctk.CTkEntry(
            form,
            placeholder_text="HH:MM"
        )
        self.entry_tarea_hora_limite.insert(0, "17:00")
        self.entry_tarea_hora_limite.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkButton(
            form,
            text="➕ Registrar tarea",
            command=self.agregar_tarea
        ).pack(
            fill="x",
            padx=10,
            pady=(16, 5)
        )

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionado",
            command=self.actualizar_tarea
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🧹 Nuevo / Limpiar",
            command=self.limpiar_form_tarea,
            fg_color="gray"
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionado",
            command=self.eliminar_tarea,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="📊 Ver tareas pendientes y vencidas",
            command=self.mostrar_reporte_tareas
        ).pack(
            fill="x",
            padx=10,
            pady=(20, 5)
        )

        ctk.CTkButton(
            form,
            text="📈 Ver carga del equipo",
            command=self.mostrar_carga_equipo
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

    def cargar_datos_tareas(self):
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT
                    t.id_tarea,
                    t.titulo,
                    t.descripcion,
                    t.prioridad,
                    t.estado,
                    t.fecha_limite,
                    e.id_evento,
                    e.titulo,
                    u.id_usuario,
                    u.nombre,
                    u.apellido
                FROM tareas t
                JOIN eventos e
                    ON e.id_evento = t.id_evento
                JOIN usuarios u
                    ON u.id_usuario = t.id_responsable
                ORDER BY t.fecha_limite
                """,
                fetch=True
            )

            for item in self.tree_tareas.get_children():
                self.tree_tareas.delete(item)

            for row in rows:
                evento = f"{row[7]} — #{row[6]}"
                responsable = f"{row[9]} {row[10]} — #{row[8]}"

                fecha_limite = (
                    row[5].strftime("%Y-%m-%d %H:%M")
                    if hasattr(row[5], "strftime")
                    else row[5]
                )

                self.tree_tareas.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[3],
                        row[4],
                        fecha_limite,
                        evento,
                        responsable
                    )
                )

            eventos = self.ejecutar_consulta(
                """
                SELECT
                    id_evento,
                    titulo
                FROM eventos
                ORDER BY titulo
                """,
                fetch=True
            )

            self.eventos_combo = {}

            for evento in eventos:
                etiqueta = f"{evento[1]} — #{evento[0]}"
                self.eventos_combo[etiqueta] = evento[0]

            valores_eventos = (
                ["Seleccione un evento"]
                + list(self.eventos_combo.keys())
            )

            self.combo_tarea_evento.configure(
                values=valores_eventos
            )

            valores_usuarios = (
                ["Seleccione un usuario"]
                + list(self.usuarios_combo.keys())
            )

            self.combo_tarea_responsable.configure(
                values=valores_usuarios
            )

        except Exception as e:
            print(f"Error cargando tareas: {e}")

    def tarea_seleccionada_id(self):
        sel = self.tree_tareas.selection()

        if not sel:
            return None

        return self.tree_tareas.item(sel[0])["values"][0]


    def cargar_tarea_seleccionada(self, _=None):
        sel = self.tree_tareas.selection()

        if not sel:
            return

        vals = self.tree_tareas.item(sel[0])["values"]

        self.entry_tarea_titulo.delete(0, tk.END)
        self.entry_tarea_titulo.insert(0, vals[1])

        self.combo_tarea_prioridad.set(vals[2])
        self.combo_tarea_estado.set(vals[3])

        try:
            limite = datetime.strptime(
                str(vals[4]),
                "%Y-%m-%d %H:%M"
            )

            self.establecer_fecha(
                self.fecha_tarea_limite,
                limite
            )

            self.entry_tarea_hora_limite.delete(0, tk.END)
            self.entry_tarea_hora_limite.insert(
                0,
                limite.strftime("%H:%M")
            )

        except ValueError:
            pass

        self.combo_tarea_evento.set(vals[5])
        self.combo_tarea_responsable.set(vals[6])

        # Cargar descripción directamente desde la BD
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT descripcion
                FROM tareas
                WHERE id_tarea=%s
                """,
                (vals[0],),
                fetch=True
            )

            self.entry_tarea_descripcion.delete(0, tk.END)

            if rows and rows[0][0]:
                self.entry_tarea_descripcion.insert(
                    0,
                    rows[0][0]
                )

        except Exception as e:
            print(f"Error cargando descripción de tarea: {e}")

    def agregar_tarea(self):
        titulo = self.entry_tarea_titulo.get().strip()
        descripcion = self.entry_tarea_descripcion.get().strip()

        prioridad = self.combo_tarea_prioridad.get()
        estado = self.combo_tarea_estado.get()

        evento = self.eventos_combo.get(
            self.combo_tarea_evento.get()
        )

        responsable = self.usuarios_combo.get(
            self.combo_tarea_responsable.get()
        )

        hora_limite = self.entry_tarea_hora_limite.get().strip()

        if not titulo:
            return messagebox.showwarning(
                "Campos incompletos",
                "Indica el título de la tarea."
            )

        if evento is None or responsable is None:
            return messagebox.showwarning(
                "Campos incompletos",
                "Selecciona un evento y un responsable."
            )

        try:
            fecha_limite = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_tarea_limite)} {hora_limite}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:
            return messagebox.showwarning(
                "Fecha u hora inválida",
                "La hora debe tener formato HH:MM, por ejemplo 17:00."
            )

        try:
            self.ejecutar_consulta(
                """
                INSERT INTO tareas (
                    titulo,
                    descripcion,
                    prioridad,
                    fecha_limite,
                    estado,
                    id_evento,
                    id_responsable
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    titulo,
                    descripcion,
                    prioridad,
                    fecha_limite,
                    estado,
                    evento,
                    responsable
                )
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Tarea registrada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo registrar",
                str(e)
            )

    def actualizar_tarea(self):
        tid = self.tarea_seleccionada_id()

        if tid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una tarea para actualizar."
            )

        titulo = self.entry_tarea_titulo.get().strip()
        descripcion = self.entry_tarea_descripcion.get().strip()

        prioridad = self.combo_tarea_prioridad.get()
        estado = self.combo_tarea_estado.get()

        evento = self.eventos_combo.get(
            self.combo_tarea_evento.get()
        )

        responsable = self.usuarios_combo.get(
            self.combo_tarea_responsable.get()
        )

        hora_limite = self.entry_tarea_hora_limite.get().strip()

        if not titulo:
            return messagebox.showwarning(
                "Campos incompletos",
                "Indica el título de la tarea."
            )

        if evento is None or responsable is None:
            return messagebox.showwarning(
                "Campos incompletos",
                "Selecciona un evento y un responsable."
            )

        try:
            fecha_limite = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_tarea_limite)} {hora_limite}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:
            return messagebox.showwarning(
                "Fecha u hora inválida",
                "La hora debe tener formato HH:MM."
            )

        try:
            self.ejecutar_consulta(
                """
                UPDATE tareas
                SET titulo=%s,
                    descripcion=%s,
                    prioridad=%s,
                    fecha_limite=%s,
                    estado=%s,
                    id_evento=%s,
                    id_responsable=%s
                WHERE id_tarea=%s
                """,
                (
                    titulo,
                    descripcion,
                    prioridad,
                    fecha_limite,
                    estado,
                    evento,
                    responsable,
                    tid
                )
            )

            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Éxito",
                "Tarea actualizada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo actualizar",
                str(e)
            )

    def limpiar_form_tarea(self):
        self.tree_tareas.selection_remove(
            self.tree_tareas.selection()
        )

        self.tree_tareas.focus("")

        self.entry_tarea_titulo.delete(0, tk.END)
        self.entry_tarea_descripcion.delete(0, tk.END)

        self.combo_tarea_prioridad.set("Media")
        self.combo_tarea_estado.set("Pendiente")

        self.combo_tarea_evento.set(
            "Seleccione un evento"
        )

        self.combo_tarea_responsable.set(
            "Seleccione un usuario"
        )

        hoy = datetime.now()

        self.establecer_fecha(
            self.fecha_tarea_limite,
            hoy
        )

        self.entry_tarea_hora_limite.delete(0, tk.END)
        self.entry_tarea_hora_limite.insert(0, "17:00")

    def eliminar_tarea(self):
        tid = self.tarea_seleccionada_id()

        if tid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una tarea para eliminar."
            )

        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la tarea seleccionada?"
        ):
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM tareas WHERE id_tarea=%s",
                (tid,)
            )

            self.limpiar_form_tarea()
            self.actualizar_todas_las_tablas()

            messagebox.showinfo(
                "Eliminado",
                "Tarea eliminada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def mostrar_reporte_tareas(self):
        try:
            carga = self.ejecutar_consulta(
                """
                SELECT
                    id_usuario,
                    nombre,
                    apellido,
                    tareas_pendientes,
                    tareas_vencidas
                FROM vista_carga_trabajo
                ORDER BY tareas_vencidas DESC,
                         tareas_pendientes DESC,
                         nombre
                """,
                fetch=True
            )

            eventos = self.ejecutar_consulta(
                """
                SELECT
                    id_evento,
                    titulo_evento,
                    cantidad_tareas_vencidas
                FROM vista_eventos_con_vencidas
                ORDER BY cantidad_tareas_vencidas DESC,
                         titulo_evento
                """,
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Reporte de Tareas")
            ventana.geometry("850x650")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana,
                text="Tareas pendientes y vencidas",
                font=ctk.CTkFont(size=22, weight="bold")
            ).pack(
                anchor="w",
                padx=20,
                pady=(20, 10)
            )

            # ----------------------------------------------------
            # Carga de trabajo por usuario
            # ----------------------------------------------------

            ctk.CTkLabel(
                ventana,
                text="Carga de trabajo por usuario",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(
                anchor="w",
                padx=20,
                pady=(5, 5)
            )

            frame_usuarios = ctk.CTkFrame(ventana)
            frame_usuarios.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=(0, 15)
            )

            tree_usuarios = self.crear_treeview(
                frame_usuarios,
                (
                    "ID",
                    "Usuario",
                    "Pendientes",
                    "Vencidas"
                ),
                (
                    70,
                    250,
                    120,
                    120
                )
            )

            for row in carga:
                usuario = f"{row[1]} {row[2]}"

                tree_usuarios.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        usuario,
                        row[3],
                        row[4]
                    )
                )

            # ----------------------------------------------------
            # Eventos con tareas vencidas
            # ----------------------------------------------------

            ctk.CTkLabel(
                ventana,
                text="Eventos con tareas vencidas",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(
                anchor="w",
                padx=20,
                pady=(5, 5)
            )

            frame_eventos = ctk.CTkFrame(ventana)
            frame_eventos.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=(0, 20)
            )

            tree_eventos = self.crear_treeview(
                frame_eventos,
                (
                    "ID",
                    "Evento",
                    "Tareas vencidas"
                ),
                (
                    70,
                    350,
                    140
                )
            )

            for row in eventos:
                tree_eventos.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2]
                    )
                )

        except Exception as e:
            messagebox.showerror(
                "No se pudo generar el reporte",
                str(e)
            )

    def mostrar_carga_equipo(self):
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT
                    id_usuario,
                    nombre,
                    apellido,
                    tareas_pendientes,
                    tareas_en_progreso,
                    tareas_activas,
                    tareas_vencidas
                FROM vista_reporte_tareas_usuario
                ORDER BY tareas_activas DESC,
                         tareas_vencidas DESC,
                         nombre
                """,
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Carga de Trabajo del Equipo")
            ventana.geometry("950x500")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana,
                text="Carga de Trabajo por Miembro del Equipo",
                font=ctk.CTkFont(
                    size=22,
                    weight="bold"
                )
            ).pack(
                anchor="w",
                padx=20,
                pady=(20, 5)
            )

            ctk.CTkLabel(
                ventana,
                text="Permite identificar tareas activas, vencimientos y posibles cuellos de botella."
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 15)
            )

            tabla_frame = ctk.CTkFrame(ventana)
            tabla_frame.pack(
                fill="both",
                expand=True,
                padx=20,
                pady=(0, 20)
            )

            tree = self.crear_treeview(
                tabla_frame,
                (
                    "ID",
                    "Usuario",
                    "Pendientes",
                    "En progreso",
                    "Activas",
                    "Vencidas",
                    "Alerta"
                ),
                (
                    60,
                    220,
                    100,
                    110,
                    90,
                    90,
                    180
                )
            )

            max_activas = max(
                (row[5] for row in rows),
                default=0
            )

            for row in rows:
                alerta = ""

                if row[6] > 0:
                    alerta = f"⚠ {row[6]} vencida(s)"

                if row[5] == max_activas and max_activas > 0:
                    if alerta:
                        alerta += " | "

                    alerta += "Mayor carga"

                usuario = f"{row[1]} {row[2]}"

                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        usuario,
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        alerta
                    )
                )

        except Exception as e:
            messagebox.showerror(
                "No se pudo generar el reporte",
                str(e)
            )
    # -------------------- REFRESCO GENERAL --------------------

    def actualizar_todas_las_tablas(self):
        self.cargar_datos_usuarios()
        self.cargar_datos_disponibilidades()
        self.cargar_datos_categorias()
        self.cargar_datos_eventos()
        self.cargar_datos_ubicaciones()
        self.cargar_datos_tareas()
        
if __name__ == "__main__":
    app = AppAgenda()
    app.mainloop()

