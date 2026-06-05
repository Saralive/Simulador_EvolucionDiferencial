import subprocess
from pathlib import Path
import os
import shutil
import configFormacion_opt
#import configPaths_opt
import sys
import threading

RESULTADOS_DIR = sys.argv[2]

# Ruta base actual (asegúrate de estar en ResultadosCN1 al ejecutar)
BASE_DIR = Path.cwd()
PYTHON_EXEC = "python"  # Si tu entorno ya responde a 'python'

def generar_script_constantes(nombre_archivo, long_enlace, regla,tipo_red, ruteo):
    constantes = {
        #--------ANILLO------------------
        # Número de nodos del anillo. Colocar 0 si no se usa anillo
        "NODOS_ANILLO":configFormacion_opt.NODOS_ANILLO, 
        #--------MALLA-------------------
        # Filas de la malla. Colocar 0 si no se usa malla
        "ROWS":configFormacion_opt.ROWS,
        # Columnas de la malla                  
        "COLUMNS":configFormacion_opt.COLUMNS,           
        #--------FORMACION-------------
        # Topología sobre la que se desarrollará la simulación: 1 -> "malla" o 3->"anillo"
        "RED":tipo_red,                           
        # Algoritmo de encaminamiento: "CR", "RW", "SP"
        "ROUTING":ruteo, 
        "REGLA":regla,
        "VECTOR_POPULARIDAD":configFormacion_opt.VECTOR_POPULARIDAD,
        "VECTOR_DISTANCIA":configFormacion_opt.VECTOR_DISTANCIA,
        "ALPHA":configFormacion_opt.ALPHA,
        # Divisor de la longitud de enlace dinámico: 1, 2, 4, 8, 16, 32 
        "LONG_ENLACES":long_enlace,        
        #--------EJECUCION---------------
        # Número de ciclos de formación
        "CICLOS":configFormacion_opt.CICLOS,                    
        #--------EXTRAS------------------
        # Número de enlaces dinámicos por nodo
        "ENLACES_DINAMICOS":configFormacion_opt.ENLACES_DINAMICOS,       
        # Número de experimentos a realizar
        "EXPLORADORES":configFormacion_opt.EXPLORADORES,
        # Divisor (con respecto al número de nodos, num_nodos/DIV_CONEXIONES) del máximo número de conexiones permitidas
        "DIV_CONEXIONES":configFormacion_opt.DIV_CONEXIONES         
    }

    with open(nombre_archivo, 'w') as f:
        f.write("# Archivo de constantes generado automáticamente\n\n")
        for nombre, valor in constantes.items():
            if isinstance(valor, str):
                f.write(f'{nombre} = "{valor}"\n')
            else:
                f.write(f"{nombre} = {valor}\n")
    print(f"Archivo '{nombre_archivo}' generado con {len(constantes)} constantes.")

###### F U N C I O N   Q U E   C R E A   L A S  R E D E S   D E  C A D A   S I M U L A C I O N  ######
def formacion(ruta, x):
    hoja = f"{ruta}/{x}"
    os.makedirs(hoja, exist_ok=True)

    print(f"\n Simulación {x} en: {hoja}")

    salida_txt = f"{hoja}/salida_{x}.txt"
    #Creo el archivo log
    log_file = f"{hoja}/log_{x}.txt"
    with open(log_file, "w", encoding="utf-8") as logfile:
        logfile.write(f"Log de la ejecución {x} en {ruta}\n")
    # Ejecuta main.py desde la carpeta CR
    subprocess.run([PYTHON_EXEC, "main.py", log_file], cwd=ruta, stdout=open(salida_txt, "w"))

    # Copia archivos auxiliares
    for archivo in ["extractData.py", "graph.adjlist"]:
        src = f"{ruta}/{archivo}"
        dest = f"{hoja}/{archivo}"
        if os.path.exists(src):
            shutil.copy(src, dest)
        else:
            print(f" No se encontró: {archivo} en {ruta}")

    # Ejecuta extractData.py desde la hoja
    if os.path.exists(hoja+"/extractData.py"):
        print(" Extrayendo datos...")
        subprocess.run([PYTHON_EXEC, "extractData.py", f"salida_{x}.txt", "test"], cwd=hoja)
    else:
        print(" No se puede extraer: falta extractData.py")

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
                ruta = f"{RESULTADOS_DIR}/{nombre_red}/R{r}/{routing}/D{long_enlace}"
                print(f"\n Explorando: {ruta}")

                if not os.path.exists(ruta):
                    print(f" Ruta no encontrada, saltando: {ruta}")
                    continue
                
                # Crea constantes.py en la ruta
                generar_script_constantes(str(ruta)+"/config.py", long_enlace, r, tipo_red,ruteo)

                #############################################################
                #------- I N I C I A M O S   P A R A L I Z A C I O N -------#
                #############################################################
                #-------- (1) CREAR UN HILO POR SIMULACION -----------------#
                pool_hilos = int(configFormacion_opt.EJECUCIONES/2)
                for h in range(2):
                    hilos =[]
                    for i in range(1 + h*pool_hilos, 1 + (h+1)*pool_hilos):
                        t = threading.Thread(target=formacion, args=(ruta,i))
                        hilos.append(t)
                    #-------- (2) INICIAR TODOS LOS HILOS ----------------------#
                    for t in hilos:
                        t.start()
                    #---------(3) ESPERAR QUE TERMINEN TODOS LOS HILOS ---------#
                    for t in hilos:
                        t.join()
