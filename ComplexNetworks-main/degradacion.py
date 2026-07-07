
import subprocess
import os
import shutil
import configuracion
#import configPaths
import glob
import sys
import re
import configGenetico
from multiprocessing import Pool

RESULTADOS_DIR = sys.argv[2]
DEGRADACION_DIR = sys.argv[3]

def ejecutar_degradacion_worker(args):
    degradation_file, ultimo_grafo, carpeta_resultados =args
    
    subprocess.run([
        "python",
        degradation_file,
        os.path.basename(ultimo_grafo),
        str(carpeta_resultados)
    ], cwd=carpeta_resultados)
        
    print(f"\nEjecutando: python {degradation_file} {os.path.basename(ultimo_grafo)} {carpeta_resultados} en {carpeta_resultados}")


def copia_archivos_para_degradacion():
    # Copia los archivos de los grafos a la carpeta de degradacion
    for red in configuracion.RED:
        if red == "anillo":
            nombre_red = "anillo" + str(configuracion.NODOS_ANILLO)
        elif red == "malla":
            nombre_red = f"malla{configuracion.ROWS}x{configuracion.COLUMNS}"
        else:
            print(f" Tipo de red desconocido, saltando: {red}")
            continue   
        for r in configuracion.REGLAS:
            for ruteo in configuracion.ROUTING:
                routing = "x"
                if ruteo == "COMPASS-ROUTING":
                    routing = "CR"
                elif ruteo == "RANDOM-WALK":
                    routing = "RW" 
                elif ruteo == "SHORTEST-PATH":
                    routing = "SP"
                else:
                    print(f" Algoritmo de ruteo desconocido, saltando: {ruteo}")
                    continue
                for long_enlace in configuracion.LONG_ENLACES:
                    for i in range(1, configuracion.EJECUCIONES + 1):
                        for tipo_degradacion in configuracion.TIPO_DEGRADACION:
                            for ind in range(1, configGenetico.N_INDIVIDUOS + 1):
                                individuo = f'Individuo{ind}'
                                ruta_grafo = f"{RESULTADOS_DIR}/{individuo}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
                                if os.path.exists(ruta_grafo):
                                    # Buscar el grafo del último ciclo disponible
                                    grafos = glob.glob(ruta_grafo + "graph_test_*.adjlist")
                                    ultimo_grafo = max(grafos, key=lambda x: int(os.path.splitext(x)[0].split("_")[-1]))
                                    for tipo_degradacion in configuracion.TIPO_DEGRADACION:
                                        if tipo_degradacion=="Fallas":
                                            script_degradacion = "failureDegradation.py"
                                        elif tipo_degradacion=="Ataques":
                                            script_degradacion = "hubDegradation.py"
                                        else:
                                            print(f" Tipo de degradación desconocido, saltando: {tipo_degradacion}")
                                            continue
                                        carpeta_resultados = f"{DEGRADACION_DIR}/{individuo}/{tipo_degradacion}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
                                        archivo_destino = f"{carpeta_resultados}{os.path.basename(ultimo_grafo)}"
                                        #tareas.append((individuo, tipo_degradacion, nombre_red, r, routing, long_enlace, i, ))
                                        os.makedirs(os.path.dirname(archivo_destino), exist_ok=True)
                                        # Copia los scrips de degradación a la carpeta de resultados si no existen
                                        shutil.copy2("configuracion.py", carpeta_resultados)
                                        shutil.copy2(script_degradacion, carpeta_resultados)
                                        shutil.copy2(ultimo_grafo, archivo_destino)
                                else:
                                    print(f" Ruta no encontrada, saltando: {ruta_grafo}")
                                    continue

def ejecutar_degradacion():
    tareas = []
    for red in configuracion.RED:
        if red == "anillo":
            nombre_red = "anillo" + str(configuracion.NODOS_ANILLO)
        elif red == "malla":
            nombre_red = f"malla{configuracion.ROWS}x{configuracion.COLUMNS}"
        else:
            print(f" Tipo de red desconocido, saltando: {red}")
            continue   
        for r in configuracion.REGLAS:
            routing = "x"
            for ruteo in configuracion.ROUTING:
                if ruteo == "COMPASS-ROUTING":
                    routing = "CR"
                elif ruteo == "RANDOM-WALK":
                    routing = "RW" 
                elif ruteo == "SHORTEST-PATH":
                    routing = "SP"
                else:
                    print(f" Algoritmo de ruteo desconocido, saltando: {ruteo}")
                    continue

                for long_enlace in configuracion.LONG_ENLACES:
                    for i in range(1, configuracion.EJECUCIONES + 1):
                        # Ejecutar degradación desde carpeta destino
                        for tipo_degradacion in configuracion.TIPO_DEGRADACION:
                            # Ruta donde están los grafos formados
                            for ind in range(1, configGenetico.N_INDIVIDUOS + 1):
                                individuo = f'Individuo{ind}'
                                ruta_grafo = f"{DEGRADACION_DIR}/{individuo}/{tipo_degradacion}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
                                if os.path.exists(ruta_grafo):
                                    # Buscar el archivo del grafo
                                    grafos = glob.glob(ruta_grafo + "graph_test_*.adjlist")
                                    ultimo_grafo = max(grafos, key=lambda x: int(os.path.splitext(x)[0][-1]))
                                    if tipo_degradacion=="Fallas":
                                        degradation_file = "failureDegradation.py"
                                    elif tipo_degradacion=="Ataques":
                                        degradation_file = "hubDegradation.py"
                                        print(degradation_file)
                                    else:
                                        print(f" Tipo de degradación desconocido, saltando: {tipo_degradacion}")
                                        continue
                                    carpeta_resultados = f"{DEGRADACION_DIR}/{individuo}/{tipo_degradacion}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
                                    tareas.append((degradation_file, ultimo_grafo, carpeta_resultados))
                                else:
                                    print(f" Ruta no encontrada, saltando: {ruta_grafo}")
                                    continue

    num_workers = getattr(configuracion, "NUM_WORKERS", 4)
    print(f'Ejecutando {len(tareas)} degradaciones en paralelo usando {num_workers} workers...')

    with Pool(processes=num_workers) as pool:
        pool.map(ejecutar_degradacion_worker, tareas)

if __name__=="__main__":
    copia_archivos_para_degradacion()
    ejecutar_degradacion()
