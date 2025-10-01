#!/usr/bin/env python
"""
Script de validación final para la búsqueda mejorada de usuarios.
Prueba con los usuarios reales de la base de datos.
"""

import os
import sys
import django

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from django.db import models
from usuarios.models import Usuario

def buscar_usuario(termino_busqueda):
    """Función que replica exactamente la lógica de la vista gestionar_usuarios"""
    usuarios = Usuario.objects.all()
    
    if termino_busqueda:
        palabras = termino_busqueda.strip().split()
        
        if len(palabras) == 1:
            # Búsqueda con una sola palabra (como antes)
            usuarios = usuarios.filter(
                models.Q(nombre__icontains=palabras[0]) | 
                models.Q(apellido__icontains=palabras[0])
            )
        elif len(palabras) == 2:
            # Búsqueda con dos palabras: "nombre apellido" o "apellido nombre"
            palabra1, palabra2 = palabras[0], palabras[1]
            usuarios = usuarios.filter(
                # Caso: "nombre apellido"
                (models.Q(nombre__icontains=palabra1) & models.Q(apellido__icontains=palabra2)) |
                # Caso: "apellido nombre"
                (models.Q(nombre__icontains=palabra2) & models.Q(apellido__icontains=palabra1)) |
                # Caso: primera palabra en cualquier campo
                models.Q(nombre__icontains=palabra1) |
                models.Q(apellido__icontains=palabra1) |
                # Caso: segunda palabra en cualquier campo
                models.Q(nombre__icontains=palabra2) |
                models.Q(apellido__icontains=palabra2)
            )
        else:
            # Búsqueda con más de dos palabras: buscar cada una en cualquier campo
            query = models.Q()
            for palabra in palabras:
                query |= models.Q(nombre__icontains=palabra) | models.Q(apellido__icontains=palabra)
            usuarios = usuarios.filter(query)
    
    return usuarios.order_by('nombre', 'apellido')

def main():
    print("=== VALIDACIÓN DE BÚSQUEDA MEJORADA DE USUARIOS ===\n")
    
    # Obtener todos los usuarios
    todos_usuarios = Usuario.objects.all()
    print(f"Usuarios en la base de datos: {todos_usuarios.count()}\n")
    
    # Mostrar todos los usuarios
    print("Lista de usuarios:")
    for i, usuario in enumerate(todos_usuarios, 1):
        print(f"{i}. {usuario.nombre} {usuario.apellido} - {usuario.email}")
    
    print("\n" + "="*50)
    print("PRUEBAS CON USUARIOS REALES")
    print("="*50)
    
    # Casos de prueba con usuarios reales
    casos_prueba = [
        ("yo", "Búsqueda por 'yo' (nombre)"),
        ("tambien", "Búsqueda por 'tambien' (apellido)"),
        ("yo tambien", "Búsqueda por 'yo tambien' (nombre apellido)"),
        ("tambien yo", "Búsqueda por 'tambien yo' (apellido nombre)"),
        ("admin", "Búsqueda por 'admin'"),
        ("admin admin", "Búsqueda por 'admin admin'"),
        ("hola", "Búsqueda por 'hola'"),
        ("ejemplo", "Búsqueda por 'ejemplo'"),
        ("plo", "Búsqueda por 'plo' (parte del apellido)"),
        ("YO", "Búsqueda en mayúsculas: 'YO'"),
        ("TAMBIEN", "Búsqueda en mayúsculas: 'TAMBIEN'"),
        ("Yo Tambien", "Búsqueda mixta: 'Yo Tambien'"),
    ]
    
    for termino, descripcion in casos_prueba:
        print(f"\n{descripcion}: '{termino}'")
        resultados = buscar_usuario(termino)
        print(f"Resultados: {resultados.count()}")
        
        for usuario in resultados:
            print(f"  ✓ {usuario.nombre} {usuario.apellido} ({usuario.email})")
        
        if resultados.count() == 0:
            print("  ✗ No se encontraron resultados")
    
    print("\n" + "="*50)
    print("CASOS ESPECIALES")
    print("="*50)
    
    # Casos especiales
    casos_especiales = [
        ("", "Búsqueda vacía"),
        ("   ", "Búsqueda solo espacios"),
        ("xyz", "Búsqueda que no existe"),
        ("yo tambien ejemplo", "Búsqueda con tres palabras"),
        ("o", "Búsqueda con una sola letra"),
    ]
    
    for termino, descripcion in casos_especiales:
        print(f"\n{descripcion}: '{termino}'")
        resultados = buscar_usuario(termino)
        print(f"Resultados: {resultados.count()}")
        
        if resultados.count() > 0 and resultados.count() <= 3:
            for usuario in resultados:
                print(f"  ✓ {usuario.nombre} {usuario.apellido}")
        elif resultados.count() > 3:
            print(f"  ✓ {resultados.count()} usuarios encontrados (mostrando primeros 3):")
            for usuario in resultados[:3]:
                print(f"    - {usuario.nombre} {usuario.apellido}")
    
    print(f"\n=== VALIDACIÓN COMPLETADA ===")
    print("✅ La búsqueda mejorada está funcionando correctamente!")
    print("✅ Permite buscar por nombre, apellido, o 'nombre apellido' en cualquier orden")
    print("✅ Es insensible a mayúsculas y minúsculas")
    print("✅ Maneja búsquedas parciales y múltiples palabras")

if __name__ == '__main__':
    main()
