
import os
import networkx as nx
import shutil
import configFormacion_opt
#import configPaths_opt
import sys

BASE_DIR = sys.argv[1]
RESULTADOS_DIR = sys.argv[2]
DEGRADACION_DIR = sys.argv[3]

def crear_arbol_directorios(ruta):
    try:
        os.makedirs(ruta, exist_ok=True)
        print(f"Directorio '{ruta}' creado (o ya existía).")
    except Exception as e:
        print(f"Error al crear directorios: {e}")

# Ejemplo: un árbol como ./proyecto/src/data/output
for red in configFormacion_opt.RED:
    if red == "anillo":
        nombre_red = "anillo" + str(configFormacion_opt.NODOS_ANILLO)
        tipo_red = 3
    elif red == "malla":
        nombre_red = f"malla{configFormacion_opt.ROWS}x{configFormacion_opt.COLUMNS}"
        tipo_red = 1    
    else:
        print(f" Tipo de red desconocido, saltando: {red}")
        continue   
    for r in configFormacion_opt.REGLAS:
        routing = "x"
        for ruteo in configFormacion_opt.ROUTING:
            if ruteo == "COMPASS-ROUTING":
                routing = "CR"
            elif ruteo == "RANDOM-WALK":
                routing = "RW" 
            elif ruteo == "SHORTEST-PATH":
                routing = "SP"
            else:
                print(f" Algoritmo de ruteo desconocido, saltando: {ruteo}")
                continue

            for long_enlace in configFormacion_opt.LONG_ENLACES:
                ruta =  f"{RESULTADOS_DIR}/{nombre_red}/R{r}/{routing}/D{long_enlace}"
                crear_arbol_directorios(ruta)

# Copio los archivos del experimentos y formacion en la carpeta de resultados
shutil.copy2("individuo.py", BASE_DIR)       # configPaths_opt
shutil.copy2("configDegradacion_opt.py", BASE_DIR)
shutil.copy2("configFormacion_opt.py", BASE_DIR)
shutil.copy2("formacion_opt.py", BASE_DIR)
shutil.copy2("degradacion_opt.py", BASE_DIR)

for nombre_directorio, subdirectorios, ficheros in os.walk(RESULTADOS_DIR):#recorro recursivamente un directorio

    if len(subdirectorios)==0:
        shutil.copy2("complexNetwork.py", nombre_directorio)
        shutil.copy2("encaminamiento.py", nombre_directorio)
        shutil.copy2("enlace.py", nombre_directorio)
        shutil.copy2("event.py", nombre_directorio)
        shutil.copy2("extractData.py", nombre_directorio)
        shutil.copy2("model.py", nombre_directorio)
        shutil.copy2("paquete.py", nombre_directorio)
        shutil.copy2("process.py", nombre_directorio)
        shutil.copy2("simulation.py", nombre_directorio)
        shutil.copy2("simulator.py", nombre_directorio)
        shutil.copy2("main.py", nombre_directorio)
        shutil.copy2("reglas.py", nombre_directorio)
    else:
        print("Los archivos ya habían sido copiado")
