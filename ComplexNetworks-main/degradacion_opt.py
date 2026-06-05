import subprocess
import os
import shutil
import configFormacion_opt
import configDegradacion_opt
#import configPaths_opt
import glob
import sys
import threading

RESULTADOS_DIR = sys.argv[2]
DEGRADACION_DIR = sys.argv[3]

### F U N C I O N   Q U E   D E G R A D A   L A S  R E D E S   D E  C A D A   S I M U L A C I O N  ######
def degradacion(i, nombre_red, r , routing, long_enlace):
    # Ejecutar degradación desde carpeta destino
    for tipo_degradacion in configDegradacion_opt.TIPO_DEGRADACION:
        # Ruta donde están los grafos formados
        ruta_grafo = f"{DEGRADACION_DIR}/{tipo_degradacion}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
        if os.path.exists(ruta_grafo):
            # Buscar el archivo del grafo
            grafos = glob.glob(ruta_grafo + "graph_test_*.adjlist")
            ultimo_grafo = max(grafos, key=lambda x: int(os.path.splitext(x)[0][-1]))
            
            degradation_file = ""
            carpeta_resultados = f"{DEGRADACION_DIR}/{tipo_degradacion}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
            if tipo_degradacion=="Fallas":
                degradation_file = "failureDegradation_opt.py"
            elif tipo_degradacion=="Ataques":
                degradation_file = "hubDegradation_opt.py"
            else:
                print(f" Tipo de degradación desconocido, saltando: {tipo_degradacion}")
                continue
            
            subprocess.run([
                "python",
                degradation_file,
                os.path.basename(ultimo_grafo),
                str(carpeta_resultados)
            ], cwd=carpeta_resultados)
            
            print(f"\nEjecutando: python {degradation_file} {os.path.basename(ultimo_grafo)} {carpeta_resultados} en {carpeta_resultados}")
        else:
            print(f" Ruta no encontrada, saltando: {ruta_grafo}")
            continue

def copia_archivos_para_degradacion():
    # Copia los archivos de los grafos a la carpeta de degradacion
    for red in configFormacion_opt.RED:
        if red == "anillo":
            nombre_red = "anillo" + str(configFormacion_opt.NODOS_ANILLO)
        elif red == "malla":
            nombre_red = f"malla{configFormacion_opt.ROWS}x{configFormacion_opt.COLUMNS}"
        else:
            print(f" Tipo de red desconocido, saltando: {red}")
            continue   
        for r in configFormacion_opt.REGLAS:
            for ruteo in configFormacion_opt.ROUTING:
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

                for long_enlace in configFormacion_opt.LONG_ENLACES:
                    for i in range(1, configFormacion_opt.EJECUCIONES + 1):
                        # Ruta donde están los grafos formados
                        ruta_grafo = f"{RESULTADOS_DIR}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
                        if os.path.exists(ruta_grafo):
                            # Buscar el grafo del último ciclo disponible
                            grafos = glob.glob(ruta_grafo + "graph_test_*.adjlist")
                            ultimo_grafo = max(grafos, key=lambda x: int(os.path.splitext(x)[0].split("_")[-1]))
                            #ultimo_grafo = max(grafos, key=lambda x: int(os.path.splitext(x)[0][-1]))
                            for tipo_degradacion in configDegradacion_opt.TIPO_DEGRADACION:
                                if tipo_degradacion=="Fallas":
                                    script_degradacion = "failureDegradation_opt.py"
                                elif tipo_degradacion=="Ataques":
                                    script_degradacion = "hubDegradation_opt.py"
                                else:
                                    print(f" Tipo de degradación desconocido, saltando: {tipo_degradacion}")
                                    continue
                                carpeta_resultados = f"{DEGRADACION_DIR}/{tipo_degradacion}/{nombre_red}/R{r}/{routing}/D{long_enlace}/{i}/"
                                archivo_destino = f"{carpeta_resultados}{os.path.basename(ultimo_grafo)}"
                                # Crear directorios intermedios si no existen
                                os.makedirs(os.path.dirname(archivo_destino), exist_ok=True)
                                # Copia los scrips de degradación a la carpeta de resultados si no existen
                                shutil.copy2("configDegradacion_opt.py", carpeta_resultados)
                                shutil.copy2(script_degradacion, carpeta_resultados)
                                shutil.copy2(ultimo_grafo, archivo_destino)
                                #print(f"\nCopiando: {ultimo_grafo}")
                                #print(f"\na: {archivo_destino}")
                        else:
                            print(f" Ruta no encontrada, saltando: {ruta_grafo}")
                            continue

def ejecutar_degradacion():
    for red in configFormacion_opt.RED:
        if red == "anillo":
            nombre_red = "anillo" + str(configFormacion_opt.NODOS_ANILLO)
        elif red == "malla":
            nombre_red = f"malla{configFormacion_opt.ROWS}x{configFormacion_opt.COLUMNS}"
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
                    #############################################################
                    #------- I N I C I A M O S   P A R A L I Z A C I O N -------#
                    #############################################################
                    pool_hilos = int(configFormacion_opt.EJECUCIONES/2)
                    for h in range(2):
                        hilos =[]
                        #-------- (1) CREAR UN HILO POR SIMULACION -----------------#
                        for i in range(1 + h*pool_hilos, 1 + (h+1)/pool_hilos):
                            t=threading.Thread(target=degradacion, args=(i, nombre_red, r, routing, long_enlace))
                            hilos.append(t)
                        #-------- (2) INICIAR TODOS LOS HILOS ---------------------#
                        for t in hilos:
                            t.start()
                        #-------- (3) ESPERAR TODOS LOS HILOS ---------------------#
                        for t in hilos:
                            t.join()

# Primero, copiar los archivos necesarios para la degradación
copia_archivos_para_degradacion()
# Ejecutar la degradación en los grafos copiados
ejecutar_degradacion()
