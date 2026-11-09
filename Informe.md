# Adición de Cámara para Y-ROCK

## Indice
1.
2.
3.
4.
5.

# . Sistema de Archivos 
- **func_simulador/camera_driver**:
Funciones de bajo nivel para el control de la cámara (Habrá un driver para OpenCV, y en el caso de alguna cámara con drivers específicos como las Basler)

- **func_simulador/camera_worker**: Funciones de alto nivel que utilizan camera_driver, para que los distintos controladores que necesiten utilizar la cámara tengan acceso

- **util?/image_processing**: Funciones específicas para procesado de imágenes, sean Get_RGB, Get_Grey, Stitch_Images, Remove_Background. 

# . Funciones
## camera_driver

## camera_worker

## image_processing
- get_rgb() -> R,G,B
- get_grey() -> Grey
- stitch_images( Array de Imagenes ) -> Imagen compuesta 