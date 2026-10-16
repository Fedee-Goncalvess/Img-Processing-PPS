# Procesamiento de Imágenes para Cutting y Corona
---

El siguiente repositorio es la prueba, e implementación de algoritmos de procesamiento de imágenes pensado para imágenes de perforaciones de cutting y corona.
El trabajo forma parte de una Práctica Profesional Supervisada junto a la cátedra LEICI de la UNLP de la facultad de ingeniería.
Se busca utilizar distintas librerías de procesamiento de imágenes, y definir una para la implementación final.

## Objetivos

- Tomar fotos por software con cámaras de visión por computadora
- Ajustar la cámara por software
- Eliminación de fondo de imágenes seleccionadas
- Stitching de imágenes seleccionadas
- Análisis de colorimetría y grises de imágenes seleccionadas

## Estructura de archivos
Para facilitar las pruebas e implementación de este trabajo, se divide la estructura de archivos de la siguiente manera:

### input
Las imágenes que sean capturadas en una secuencia se guardan aquí y se utilizan para generar un output.
También se pueden agregar manualmente para facilitar pruebas.

### output 
Las imágenes generadas en base a las que están en input luego de pasar por un procesamiento (Quitar fondo, stitching, etc).

### src
Aquí se encuentra el código principal y los algoritmos

- **main.py** - Máquina de estados finitos para controlar el flujo del programa
- **config.py** - Archivo de configuración global
- **mod_pre_ensayo.py** - Etapa 1 (Usa abstracción de visión) 
- **mod_posicionamiento.py** - Etapa 2 (Con driver CNC)
- **mod_capturas.py** - Etapa 3 
- **mod_generar_output.py** - Etapa 4 (Usa abstracción para stitching, rgb, etc.)

#### vision
Carpeta dedicada a la abstracción de la librería utilizada para procesamiento de imágenes. 

- **init.py** - Lee config.py y selecciona la librería a utilizar.
- **base_vision.py** - Clase abstracta que define solo las funciones a implementar
- **backend_opencv.py** - Implementación usando OpenCV

De esta manera, solo es necesario crear otro backend con otra libreria y aclarar en el config.py.

#### drivers
Simula las funciones de un CNC con el que se comunicará este sistema

#### utils
Refacción unificado de código reutilizable como HUD, para modularizar.
