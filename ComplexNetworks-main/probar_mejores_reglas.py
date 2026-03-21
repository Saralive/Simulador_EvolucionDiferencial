import os
import shutil
import subprocess
from individuo import Individuo
import threading
import queue
import csv
########################################################################################
#                       C O N J U N T O   D E   P R U E B A S                          #
#   P A R A   L O S   M E J O R E S   I N D I V I D U O S   D E L   A L G O R I T M O  #
########################################################################################
#--------( P A R A M E T R O S   A   P R O B A R   D E   L A   R E G L A   4 )---------#
pruebas = 10                             # Numero de pruebas por individuo
n = 2                                    # Numero de individuos diferentes a1, ... , an 
a1 = 0.473; vp_1 = [0,0,0,0,0,0,0,1,0,1,1,0,1,0]; vd_1 = [1,0,0,1,1,1,1,0,1,0,1,0,0,0]
a2 = 0.5;   vp_2 = [0,0,0,0,0,0,0,1,1,1,1,1,1,1]; vd_2 = [1,1,1,1,1,1,1,0,0,0,0,0,0,0]
#a3 = 2; vp_3 = [3]; vd_3 = [3]
#a4 = 3; vp_4 = [4]; vd_4 = [4]
#a5 = 4; vp_5 = [5]; vd_5 = [5]
#a6 = 5; vp_6 = [6]; vd_6 = [6]
#lista1 = [a1, a2, a3, a4, a5, a6]
#lista2 = [vp_1, vp_2, vp_3, vp_4, vp_5, vp_6]
#lista3 = [vd_1, vd_2, vd_3, vd_4, vd_5, vd_6]
lista1 = [a1, a2]
lista2 = [vp_1, vp_2]
lista3 = [vd_1, vd_2]
for i in range(n):
    print('\n')
    ALPHA = [lista1[i]]*pruebas
    VECTOR_POPULARIDAD = [lista2[i]]*pruebas
    VECTOR_DISTANCIA = [lista3[i]]*pruebas
    print(f'ALPHA: {ALPHA}')
    print(f'POPULARIDAD: {VECTOR_POPULARIDAD}')
    print(f'DISTANCIA: {VECTOR_DISTANCIA}')
############## F U N C I O N   Q U E   E J E C U T A   C A D A   E X P E R I M E N T O  #################
#  S E   P A R A L E L I Z A    C O N   H I L O S   L A   E J E C U C I O N   D E L   S I M U L A D O R #
def ejecutar_experimento(i, ruta_experimento, retornar, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA):
    ruta_individuo = os.path.join(ruta_experimento,f'Experimento{i}')     # Ruta completa de cada carpeta
    os.makedirs(ruta_individuo, exist_ok=True)                            # Creación de carpeta Individuo

    #-------(1) CREAR UN OBJETO DE INDIVIDUO PARA CADA RED ---------------------------------------------#
    regla = Individuo(ruta_individuo,                         
                    ALPHA = ALPHA[i-1],
                    VECTOR_POPULARIDAD = VECTOR_POPULARIDAD[i-1],
                    VECTOR_DISTANCIA = VECTOR_DISTANCIA[i-1],
                    DEGRADACION = degradacion)  
    
    #-------(2) COPIAR SIMULADOR PARA EL INDIVIDUO -----------------------------------------------------#
    subprocess.run(['python', os.path.join(ruta_actual,'0creaCopiaSimulador_opt.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])

    #-------(3) AGREGAR PARAMETROS EN ARCHIVO DE CONFIGURACION -----------------------------------------#
    ruta_configFormacion = os.path.join(regla.INDIVIDUO_DIR,'configFormacion_opt.py')
    with open(ruta_configFormacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nALPHA = {regla.ALPHA}')
        f.write(f'\nVECTOR_POPULARIDAD = {regla.VECTOR_POPULARIDAD}')
        f.write(f'\nVECTOR_DISTANCIA = {regla.VECTOR_DISTANCIA}')

    #-------(4) AGREGAR TIPO DE DEGRADACION EN ARCHIVO DE CONFIGURACION --------------------------------#
    ruta_configDegradacion = os.path.join(regla.INDIVIDUO_DIR,'configDegradacion_opt.py')
    with open(ruta_configDegradacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nTIPO_DEGRADACION=["{degradacion}"]')

    #-------(5) EXPERIMENTOS DE FORMACION DE REDES -----------------------------------------------------#
    ruta_formacion = os.path.join(regla.INDIVIDUO_DIR,'formacion_opt.py')
    subprocess.run(['python',ruta_formacion,
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)],
                    cwd = regla.FORMACION_DIR)
    
    subprocess.run(['python', os.path.join(ruta_actual,'1creaPromediosFormacion_opt.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    #-------(6) EXPERIMENTOS DE DEGRADACION DE REDES ---------------------------------------------------#
    ruta_degradacion = os.path.join(regla.INDIVIDUO_DIR,'degradacion_opt.py')
    subprocess.run(['python', ruta_degradacion,
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    subprocess.run(['python', os.path.join(ruta_actual,'6creaPromediosDegradacion_opt.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    #--------------------( A Q U I   T E R M I N A   E L   E X P E R I M E N T O )----------------------#

    #--------(7) APTITUD DEL INDIVIDUO ----------------------------------------------------------------#
    regla.robustez()                                                   # Calcula la resistencia de la red
    retornar.put([regla, i])                                           # Objeto y el id del individuo

#-----------------E J E C U T A R   P R U E B A S   D E   C A D A   I N D I V I D U O---------------------#
def generacion_individuos(individuo, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, ruta_pruebas, pool_hilos):
    individuo = str(individuo)
    #-----------(1) RUTAS --------------------------------------------------------------------------------#
    os.makedirs(ruta_pruebas, exist_ok=True)
    #-----------(2) CREAR LA CARPETA DEL INDIVIDUO -------------------------------------------------------#
    ruta_experimento = os.path.join(ruta_pruebas,f'Individuo{individuo}')
    os.makedirs(ruta_experimento, exist_ok=True)
    #-----------(3) CREAR UNA CARPETA POR EXPERIMENTO DEL INDIVIDUO --------------------------------------#
    experimentos = [0]*pruebas                                       # Lista de experimentos por individuo
    #-----------( P O O L S   D E   H I L O S )-----------------------------------------------------------#
    #(pool_hilos) como parametro de entrada de esta funcion   # Numero de hilos que soporta la maquina (15)
    total_pools =int(pruebas/pool_hilos)                      # Dividir entre el numero de hilos de la maquina
    for h in range(total_pools):                              # Numero de equipos de hilos a lanzar
        hilos = []                                            # Llevar un conteo del equipo de los hilos
        retornar = queue.Queue()                              # Obtener lo que retorna la funcion
        #-----------(4) CREAR UN HILO POR CADA INDIVIDUO -------------------------------------------------#
        for i in range(1 + h*pool_hilos, 1 + (h+1)*pool_hilos):
            #print(f'i: {i}')
            t = threading.Thread(target=ejecutar_experimento, args=(i, ruta_experimento, retornar, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA ))
            hilos.append(t)
        #-----------(5) INICIAR TODOS LOS HILOS ----------------------------------------------------------#
        for t in hilos:
            t.start()                                         # Ejecución del hilo
        #-----------(6) ESPERAR QUE TERMINEN TODOS LOS HILOS ---------------------------------------------#
        for t in hilos:
            t.join()                                          # Esperar que terminen cada hilo
        #-----------(7) GUARDAR LOS RESULTADOS DE CADA HILO DONDE CORRESPONDE ----------------------------#
        while not retornar.empty():
            regla , id = retornar.get()                       # Retorna el objeto individuo y el id del individuo
            experimentos[id-1] = regla                        # Guarda las configuraciones de cada individuo 
        return experimentos                                   # Retorna una lista de objetos
#-----------( A R R A N C A R   E L   C O N J U N T O   D E   P R U E B A S )-----------------------------#
pool_hilos = 10 
degradacion = 'Ataques'
ruta_actual = os.getcwd()                                                 # Obtener la ruta actual
ruta_pruebas = os.path.abspath(os.path.join(ruta_actual,'..','..'))
ruta_pruebas = os.path.join(ruta_pruebas, f'Probar_mejores')             # Ruta de la configuracion
lista_pruebas = []
for i in range(n):
    ALPHA = [lista1[i]]*pruebas
    VECTOR_POPULARIDAD = [lista2[i]]*pruebas
    VECTOR_DISTANCIA = [lista3[i]]*pruebas
    objeto_pruebas = generacion_individuos(i, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, ruta_pruebas, pool_hilos)
    lista_pruebas.append(objeto_pruebas)
    print(f'objeto_pruebas: {objeto_pruebas}')
    # ---------- Eliminar capetas de las corridas de cada configuracion ----------#
    #ruta_individuo = os.path.join(ruta_pruebas,f'Individuo{i}')
    #shutil.rmtree(ruta_individuo)
print(f'lista_pruebas: {lista_pruebas}')
#----( R E G I S T R A R   L A S   1 0   P R U E B A S   D E   C A D A   I N D I V I D U O )---#
ruta_actual = os.getcwd()
base_dir = os.path.abspath(os.path.join(ruta_actual, '..', '..'))
csv_dir = os.path.join(base_dir, 'Probar_mejores')
os.makedirs(csv_dir, exist_ok=True)

ruta_csv = os.path.join(csv_dir, 'resultados.csv')

with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'ALPHA',
        'VECTOR_POPULARIDAD',
        'VECTOR_DISTANCIA',
        'R_COMUNICACION',
        'PUNTO_CRITICO',
        'R_CONECTIVIDAD',
        'PROMEDIO'
    ])

    for t in lista_pruebas:
        for obj in t:
            if obj is None:  # safety in case some experiments failed
                continue
            print(f"Guardando: {obj.ALPHA} ...")  # optional
            writer.writerow([
                obj.ALPHA,
                ','.join(map(str, obj.VECTOR_POPULARIDAD)),
                ','.join(map(str, obj.VECTOR_DISTANCIA)),
                obj.R_COMUNICACION,
                obj.PUNTO_CRITICO,
                obj.R_CONECTIVIDAD,
                obj.PROMEDIO
            ])
print(f"Resultados guardados correctamente en:\n  {ruta_csv}")
