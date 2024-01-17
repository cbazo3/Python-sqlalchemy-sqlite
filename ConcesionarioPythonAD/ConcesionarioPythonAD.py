# -*- coding: utf-8 -*- #caracteres necesarios

#bibliotecas para trabajar con ORM y tkinter para la interfaz grafica
from sqlalchemy import create_engine, Column, Integer, String, Sequence, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from tkinter import Tk, Frame, ttk, Entry, Button, Label, messagebox
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()

class MarcaCoche(Base):
    __tablename__ = 'marcas_coche'
    #columnas tabla
    id = Column(Integer, Sequence('marca_id_seq'), primary_key=True)
    nombre = Column(String(50))
    modelos = relationship("ModeloCoche", back_populates="marca")

class ModeloCoche(Base):
    __tablename__ = 'modelos_coche'
    id = Column(Integer, Sequence('modelo_id_seq'), primary_key=True)
    nombre = Column(String(50))
    marca_id = Column(Integer, ForeignKey('marcas_coche.id'))
    marca = relationship("MarcaCoche", back_populates="modelos")
    coches = relationship("Coche", back_populates="modelo", cascade="all, delete-orphan")

class Coche(Base):
    __tablename__ = 'coches'
    id = Column(Integer, Sequence('coche_id_seq'), primary_key=True)
    modelo_id = Column(Integer, ForeignKey('modelos_coche.id'))
    modelo = relationship("ModeloCoche", back_populates="coches")
    precio = Column(Float)  # Nueva columna para el precio

# Crear el motor de la base de datos
engine = create_engine('sqlite:///concesionario.db', echo=True)

# Crear las tablas
Base.metadata.create_all(engine)

# Crear una sesión para interactuar con la base de datos
Session = sessionmaker(bind=engine)
session = Session()

# Consultar coches
coches = session.query(Coche).all()


# Función para manejar la edición de coches
def editar_coche(session, tree):

    # Obtener el item seleccionado en el Treeview
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showinfo("Advertencia", "Por favor, seleccione un coche.")
        return

    # Obtener los valores del coche seleccionado
    coche_id = tree.item(seleccion, "values")[0]
    coche = session.query(Coche).filter_by(id=coche_id).first()

    # Crear una ventana emergente para la edición
    ventana_edicion = Tk()
    ventana_edicion.title("Editar Coche")
    ventana_edicion.geometry("400x300")

    frame_edicion = Frame(ventana_edicion)
    frame_edicion.pack(expand=True, fill='both')

    # Crear campos de entrada para la edición
    etiquetas = ["Marca", "Modelo", "Precio"]
    entradas = []
    for i, etiqueta in enumerate(etiquetas):
        ttk.Label(frame_edicion, text=etiqueta, font=('Arial', 12, 'bold')).grid(row=i, column=0, padx=5, pady=5, sticky="w")
        entrada = Entry(frame_edicion, font=('Arial', 12))
        entrada.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entradas.append(entrada)


    # Rellenar campos con los valores actuales del coche
    entradas[0].insert(0, coche.modelo.nombre if coche.modelo else "")
    entradas[1].insert(0, coche.modelo.marca.nombre if coche.modelo and coche.modelo.marca else "")
    entradas[2].insert(0, coche.precio if coche.precio else "")  # Precio

    # Función para actualizar el coche en la base de datos
    def actualizar_coche():
        # Obtener o crear la marca
        marca_nombre = entradas[1].get()
        marca = session.query(MarcaCoche).filter_by(nombre=marca_nombre).first()
        if not marca:
            marca = MarcaCoche(nombre=marca_nombre)
            session.add(marca)
            session.commit()
        
        # Obtener o crear el modelo
        modelo_nombre = entradas[0].get()
        modelo = session.query(ModeloCoche).filter_by(nombre=modelo_nombre, marca=marca).first()
        if not modelo:
            modelo = ModeloCoche(nombre=modelo_nombre, marca=marca)
            session.add(modelo)
            session.commit()

        coche.modelo = modelo  # Actualizar el modelo
        coche.precio = float(entradas[2].get())  # Actualizar el precio
        session.commit()
        
        messagebox.showinfo("Éxito", "Coche actualizado correctamente.")
        ventana_edicion.destroy()
        # Actualizar Treeview después de la edición
        actualizar_treeview(tree)

    # Botón para actualizar el coche
    boton_actualizar = Button(frame_edicion, text="Actualizar", command=actualizar_coche, font=('Arial', 12, 'bold'))
    boton_actualizar.grid(row=len(etiquetas), column=0, columnspan=2, pady=10)

    ventana_edicion.mainloop()

# Función para borrar un coche
def borrar_coche(tree):
    # Obtener el item seleccionado en el Treeview
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showinfo("Advertencia", "Por favor, seleccione un coche.")
        return

    # Obtener el ID del coche seleccionado
    coche_id = tree.item(seleccion, "values")[0]

    # Confirmar la eliminación con un cuadro de diálogo
    respuesta = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas borrar este coche?")

    if respuesta:
        # Borrar el coche de la base de datos
        coche = session.query(Coche).filter_by(id=coche_id).first()
        session.delete(coche)
        session.commit()
        
        # Eliminar el coche del Treeview
        tree.delete(seleccion)
        messagebox.showinfo("Éxito", "Coche borrado correctamente.")
        # Actualizar Treeview después de la eliminación
        actualizar_treeview(tree)

# Función para filtrar coches
def filtrar_coches(tree, filtro_marca, filtro_modelo, filtro_precio, filtro_precio_opcion):
    # Limpiar todos los elementos actuales en el Treeview
    for item in tree.get_children():
        tree.delete(item)

    # Consultar coches filtrados
    if filtro_precio_opcion == "MayorIgual":
        coches_filtrados = session.query(Coche).join(ModeloCoche).join(MarcaCoche).filter(
            MarcaCoche.nombre.ilike(filtro_marca + '%'),
            ModeloCoche.nombre.ilike(filtro_modelo + '%'),
            Coche.precio >= float(filtro_precio) if filtro_precio else True
        ).all()
    elif filtro_precio_opcion == "MenorIgual":
        coches_filtrados = session.query(Coche).join(ModeloCoche).join(MarcaCoche).filter(
            MarcaCoche.nombre.ilike(filtro_marca + '%'),
            ModeloCoche.nombre.ilike(filtro_modelo + '%'),
            Coche.precio <= float(filtro_precio) if filtro_precio else True
        ).all()
    else:
        coches_filtrados = session.query(Coche).join(ModeloCoche).join(MarcaCoche).filter(
            MarcaCoche.nombre.ilike(filtro_marca + '%'),
            ModeloCoche.nombre.ilike(filtro_modelo + '%'),
            Coche.precio == float(filtro_precio) if filtro_precio else True
        ).all()

    # Insertar datos filtrados en el Treeview
    for coche in coches_filtrados:
        tree.insert("", "end", values=(coche.id,
                                       coche.modelo.marca.nombre if coche.modelo and coche.modelo.marca else "",
                                       coche.modelo.nombre if coche.modelo else "",
                                       coche.precio if coche.precio else ""))

# Función para actualizar el Treeview después de la edición
def actualizar_treeview(tree):
    # Limpiar todos los elementos actuales en el Treeview
    for item in tree.get_children():
        tree.delete(item)

    # Consultar coches actualizados
    coches_actualizados = session.query(Coche).all()

    # Insertar datos actualizados en el Treeview
    for coche in coches_actualizados:
        tree.insert("", "end", values=(coche.id,
                                       coche.modelo.marca.nombre if coche.modelo and coche.modelo.marca else "",
                                       coche.modelo.nombre if coche.modelo else "",
                                       coche.precio if coche.precio else ""))

# Función para insertar un nuevo coche
def insertar_coche(tree):
    # Crear una ventana emergente para la inserción
    ventana_insercion = Tk()
    ventana_insercion.title("Insertar Coche")
    ventana_insercion.geometry("400x300")

    frame_insercion = Frame(ventana_insercion, padx=20, pady=10)
    frame_insercion.pack(expand=True, fill='both')

    # Crear campos de entrada para la inserción
    etiquetas = ["Marca", "Modelo", "Precio"]
    entradas = []
    for i, etiqueta in enumerate(etiquetas):
        Label(frame_insercion, text=etiqueta, font=('Arial', 12, 'bold')).grid(row=i, column=0, padx=5, pady=5, sticky="w")
        entrada = Entry(frame_insercion, font=('Arial', 12))
        entrada.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entradas.append(entrada)

    # Función para guardar el nuevo coche en la base de datos
    def guardar_coche():
        modelo_nombre = entradas[0].get()
        marca_nombre = entradas[1].get()
        precio = entradas[2].get()

        # Buscar o crear la marca
        marca = session.query(MarcaCoche).filter_by(nombre=marca_nombre).first()
        if not marca:
            marca = MarcaCoche(nombre=marca_nombre)
            session.add(marca)
            session.commit()

        # Buscar o crear el modelo
        modelo = session.query(ModeloCoche).filter_by(nombre=modelo_nombre, marca=marca).first()
        if not modelo:
            modelo = ModeloCoche(nombre=modelo_nombre, marca=marca)
            session.add(modelo)
            session.commit()

        # Crear el nuevo coche
        coche = Coche(modelo=modelo, precio=precio)  # Incluir precio
        session.add(coche)
        session.commit()

        messagebox.showinfo("Éxito", "Coche agregado correctamente.")
        ventana_insercion.destroy()
        # Actualizar Treeview después de la inserción
        actualizar_treeview(tree)

    # Botón para guardar el nuevo coche
    boton_guardar = Button(frame_insercion, text="Guardar", command=guardar_coche)
    boton_guardar.grid(row=len(etiquetas), columnspan=2, pady=10)

    ventana_insercion.mainloop()

# Crear ventana de tkinter
# Crear ventana de tkinter
ventana = Tk()
ventana.title("CONCESIONARIO")
ventana.geometry("800x600")

# Añadir un título arriba del Treeview
etiqueta_titulo = ttk.Label(ventana, text="CONCESIONARIO", font=('Arial', 16, 'bold'))
etiqueta_titulo.pack(pady=10)

# Frame principal
frame_principal = Frame(ventana)
frame_principal.pack(padx=20, pady=20, fill="both", expand=True)

# Utilizando el estilo de ttk para mejorar la apariencia del Treeview
style = ttk.Style()
style.theme_use("clam")  # Puedes cambiar "clam" a "default" o "alt" según tus preferencias
style.configure("Treeview.Heading", font=("Arial", 12, "bold"))

# Treeview
tree = ttk.Treeview(frame_principal, columns=("ID", "Modelo", "Marca", "Precio"), show="headings", style="Treeview")
tree.heading("ID", text="ID")
tree.heading("Modelo", text="Modelo")
tree.heading("Marca", text="Marca")
tree.heading("Precio", text="Precio")

# Insertar datos en el Treeview
for coche in coches:
    tree.insert("", "end", values=(coche.id, coche.modelo.nombre,
                                   coche.modelo.marca.nombre, coche.precio))

# Estableciendo colores alternados para las filas
tree.tag_configure("oddrow", background="#f1f1f1")

# Configuración de pesos para expansión
frame_principal.grid_rowconfigure(0, weight=1)
frame_principal.grid_columnconfigure(0, weight=3)
frame_principal.grid_columnconfigure(1, weight=1)
# Agregar Treeview al frame
tree.grid(row=0, column=0, sticky="nsew")

# Frame de filtros
frame_filtros = Frame(frame_principal)
frame_filtros.grid(row=0, column=1, sticky="nsew", padx=20)

etiqueta_filtro_marca = ttk.Label(frame_filtros, text="Filtrar por Modelo:")
etiqueta_filtro_marca.grid(row=0, column=0, pady=5)
entrada_filtro_marca = Entry(frame_filtros)
entrada_filtro_marca.grid(row=0, column=1, pady=5)

etiqueta_filtro_modelo = ttk.Label(frame_filtros, text="Filtrar por Marca:")
etiqueta_filtro_modelo.grid(row=1, column=0, pady=5)
entrada_filtro_modelo = Entry(frame_filtros)
entrada_filtro_modelo.grid(row=1, column=1, pady=5)

etiqueta_filtro_precio = ttk.Label(frame_filtros, text="Filtrar por Precio:")
etiqueta_filtro_precio.grid(row=2, column=0, pady=5)
entrada_filtro_precio = Entry(frame_filtros)
entrada_filtro_precio.grid(row=2, column=1, pady=5)

# Combobox para seleccionar opción de filtro de precio
opcion_filtro_precio = ttk.Combobox(frame_filtros, values=["Igual", "MayorIgual", "MenorIgual"])
opcion_filtro_precio.set("Igual")
opcion_filtro_precio.grid(row=3, column=0, columnspan=2, pady=5)

# Botón para aplicar los filtros
boton_filtrar = Button(frame_filtros, text="Filtrar", command=lambda: filtrar_coches(tree,
                                                      entrada_filtro_marca.get(),
                                                      entrada_filtro_modelo.get(),
                                                      entrada_filtro_precio.get(),
                                                      opcion_filtro_precio.get()))
boton_filtrar.grid(row=4, column=0, columnspan=2, pady=10)

# Función para borrar los filtros
def borrar_filtros():
    entrada_filtro_marca.delete(0, 'end')
    entrada_filtro_modelo.delete(0, 'end')
    entrada_filtro_precio.delete(0, 'end')
    opcion_filtro_precio.set("Igual")

# Frame para botones
frame_botones = Frame(frame_principal)
frame_botones.grid(row=1, column=0, columnspan=2, pady=20)

# Botón para editar coches
boton_editar = Button(frame_botones, text="Editar", command=lambda: editar_coche(session, tree))
boton_editar.grid(row=0, column=0, padx=5)

# Botón para borrar coches
boton_borrar = Button(frame_botones, text="Borrar", command=lambda: borrar_coche(tree))
boton_borrar.grid(row=0, column=1, padx=5)

# Botón para insertar coches
boton_insertar = Button(frame_botones, text="Insertar", command=lambda: insertar_coche(tree))
boton_insertar.grid(row=0, column=2, padx=5)

# Botón para borrar los filtros
boton_borrar_filtros = Button(frame_botones, text="Borrar Filtros", command=borrar_filtros)
boton_borrar_filtros.grid(row=0, column=3, padx=5)

# Iniciar la interfaz gráfica
ventana.mainloop()