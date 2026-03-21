import os
import csv
import numpy as np
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from individuo import Individuo
import threading
import queue
import time
import shutil

############## F U N C I O N   Q U E   E J E C U T A   C A D A   E X P E R I M E N T O  #################
#  S E   P A R A L E L I Z A    C O N   H I L O S   L A   E J E C U C I O N   D E L   S I M U L A D O R #
def ejecutar_experimento(i, ruta_experimento, retornar, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA):
    ruta_individuo = os.path.join(ruta_experimento,f'Individuo{i}')       # Ruta completa de cada carpeta
    os.makedirs(ruta_individuo, exist_ok=True)                            # Creación de carpeta Individuo

    #-------(4) CREAR UN OBJETO DE INDIVIDUO PARA CADA RED ---------------------------------------------#
    regla = Individuo(ruta_individuo,                         
                    ALPHA = ALPHA[i-1],
                    VECTOR_POPULARIDAD = VECTOR_POPULARIDAD[i-1],
                    VECTOR_DISTANCIA = VECTOR_DISTANCIA[i-1],
                    DEGRADACION = degradacion)  
    
    #-------(5) COPIAR SIMULADOR PARA EL INDIVIDUO -----------------------------------------------------#
    subprocess.run(['python', os.path.join(ruta_actual,'0creaCopiaSimulador_opt.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    #-------(6) AGREGAR PARAMETROS EN ARCHIVO DE CONFIGURACION -----------------------------------------#
    ruta_configFormacion = os.path.join(regla.INDIVIDUO_DIR,'configFormacion_opt.py')
    with open(ruta_configFormacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nALPHA = {regla.ALPHA}')
        f.write(f'\nVECTOR_POPULARIDAD = {regla.VECTOR_POPULARIDAD}')
        f.write(f'\nVECTOR_DISTANCIA = {regla.VECTOR_DISTANCIA}')

    #-----------(7) AGREGAR TIPO DE DEGRADACION EN ARCHIVO DE CONFIGURACION ----------------------------#
    ruta_configDegradacion = os.path.join(regla.INDIVIDUO_DIR,'configDegradacion_opt.py')
    with open(ruta_configDegradacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nTIPO_DEGRADACION=["{degradacion}"]')

    #-------(8) EXPERIMENTOS DE FORMACION DE REDES -----------------------------------------------------#
    ruta_formacion = os.path.join(regla.INDIVIDUO_DIR,'formacion_opt.py')
    subprocess.run(['python',ruta_formacion,
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)],
                    cwd = regla.FORMACION_DIR)
    
    subprocess.run(['python', os.path.join(ruta_actual,'1creaPromediosFormacion_opt.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    #-------(9) EXPERIMENTOS DE DEGRADACION DE REDES ---------------------------------------------------#
    ruta_degradacion = os.path.join(regla.INDIVIDUO_DIR,'degradacion_opt.py')
    subprocess.run(['python', ruta_degradacion,
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    subprocess.run(['python', os.path.join(ruta_actual,'6creaPromediosDegradacion_opt.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    #--------------------( A Q U I   T E R M I N A   E L   E X P E R I M E N T O )----------------------#

    #--------(10) APTITUD DEL INDIVIDUO ----------------------------------------------------------------#
    regla.robustez()                                                   # Calcula la resistencia de la red
    retornar.put([regla, i])                                               # Objeto y el id del individuo

###########################  G E N E R A C I Ó N   D E   I N D I V I D U O S  ################################
def generacion_individuos(configuracion,corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA):
    configuracion = str(configuracion)
    corrida = str(corrida)
    experimento = str(experimento)
    #-----------(1) RUTAS ----------------------------------------------------------------------------------#
    ruta_actual = os.getcwd()                                                 # Obtener la ruta actual
    ruta_configuracion = os.path.abspath(os.path.join(ruta_actual,'..','..'))
    ruta_configuracion = os.path.join(ruta_configuracion, f'Configuracion_{configuracion}') # Ruta de la configuracion
    ruta_corrida = os.path.join(ruta_configuracion,f'Corrida{corrida}')         # Ruta de la carpeta Corrida
    os.makedirs(ruta_corrida, exist_ok=True)

    #-----------(2) CREAR LA CARPETA EXPERIMENTO -----------------------------------------------------------#
    ruta_experimento = os.path.join(ruta_corrida,f'Experimento{experimento}')
    os.makedirs(ruta_experimento, exist_ok=True)

    #-----------(3) CREAR UNA CARPETA POR INDIVIDUO DEL EXPERIMENTO ----------------------------------------#
    individuos = [0]*n_individuos                                             # Lista de individuos
    #-----------(4) CREAR UN HILO POR CADA INDIVIDUO -------------------------------------------------------#
    hilos = []                                                                # Llevar un conteo de los hilos
    retornar = queue.Queue()                                                  # Obtener lo que retorna la funcion
    for i in range(1, n_individuos + 1):
        t = threading.Thread(target=ejecutar_experimento, args=(i, ruta_experimento, retornar, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA ))
        hilos.append(t)
    #-----------(5) INICIAR TODOS LOS HILOS ----------------------------------------------------------------#
    for t in hilos:
        t.start()                                                             # Ejecución del hilo
    #-----------(6) ESPERAR QUE TERMINEN TODOS LOS HILOS ---------------------------------------------------#
    for t in hilos:
        t.join()                                                              # Esperar que terminen cada hilo
    #-----------(7) GUARDAR LOS RESULTADOS DE CADA HILO DONDE CORRESPONDE ----------------------------------#
    while not retornar.empty():
        regla , id = retornar.get()                       # Retorna el objeto individuo y el id del individuo
        individuos[id-1] = regla                          # Guarda las configuraciones de cada individuo 
    return individuos                                     # Retorna una lista de objetos
####################################### ( C O R R I D A S ) ##################################################
def resultados_corridas(configuracion, corridas, n_generaciones,n_individuos,longitud,degradacion, F, CR, resultados):
    individuo_optimo, mejor_por_generaciones = evolucion_diferencial(configuracion, corridas, n_generaciones,n_individuos,longitud,degradacion, F, CR)
    eje_x = [j for j in range(n_generaciones + 1)]
    eje_y = [k[3] for k in mejor_por_generaciones]
    resultados.put([corridas, eje_x, eje_y, individuo_optimo[3]])

############################################################################################################
# E V O L U C I Ó N    D I F E R E N C I A L   P A R A   V A R I A B L E S   R E A L E S  Y  B I N A R I A #
############################################################################################################

def parametros_regla4(n_individuos, longitud):
    x = [[]]*(n_individuos)                                    # Representación del individuo
    for i in range(n_individuos):                              # Iteramos sobre cada individuo
        x[i] = np.random.uniform(1, 0, 1 + 2*longitud).tolist()# Números aleatorios entre 0 y 1
    return x

def binarizacion(x, n_individuos, longitud):
    ALPHA = [0]*n_individuos
    VECTOR_POPULARIDAD = [[0]*longitud for k in range(n_individuos)]
    VECTOR_DISTANCIA = [[0]*longitud for k in range(n_individuos)]
    tam = 1 + 2*longitud
    poblacion = [[0]*tam for i in range(n_individuos)]         # Lista para guardar los individuos en binario
    for i in range(n_individuos):                        
        for j in range(2*longitud + 1):                        # Itera sobre las entradas de x
                if j==0:
                    x[i][0] = round(x[i][0], 3)                # Redondear la primera entrada a 3
                    poblacion[i][0] = x[i][0]
                else:
                    if x[i][j] > 0.5:                          # Umbral binario
                        poblacion[i][j] = 1
                    else:
                        poblacion[i][j] = 0
    for i in range(n_individuos):
        ALPHA[i] = poblacion[i][0]                             # Guarda la primera entrada de cada entrada de la lista
        VECTOR_POPULARIDAD[i] = poblacion[i][1 : longitud + 1] # Guarda las entradas correspondientes al primer vector
        VECTOR_DISTANCIA[i] = poblacion[i][longitud + 1 : 1 + (2*longitud)]

    return ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA , poblacion

def generacion_hijos(x, n_hijos, F, CR):
    d = len(x[0]) - 1                                          # Dimension total del individuo sin la aptitud
    u = [[0]*d for i in range(n_hijos)]                        # Lista para guardar a los hijos mutados
    for j in range(n_hijos):
        entradas = [p for p in range(n_hijos) if p!=j]         # Lista de las posiciones de los individuos en x excepto el individuo j
        r = np.random.choice(entradas, size = 3,replace=False) # Elegir aletoriamente 3 individuos distintos
        x1 = np.array(x[r[0]])
        x2 = np.array(x[r[1]])
        x3 = np.array(x[r[2]])
        v = x1 +(F*(x2-x3))                                    # Vector mutante real
        #------------ C R U C E   B I N O M I A L -------------#
        k_rand = np.random.randint(d-1)                        # Elegir aleatoriamente la entrada del 
        for k in range(d):                                     # Iteración sobre cada entrada del individuo
            if (np.random.uniform(0,1) <= CR) or k == k_rand:  # Creación del individuo hijo
                u[j][k] = v[k]                                 
            else:
                u[j][k] = x[j][k]
        #------------------- C A M P L E O --------------------#
        for k in range(d):                                     # Recorremos nuevamente el las entredas del hijo mutado 
            u[j][k] = min(1, max(0, u[j][k]))                  # Mantiene los valores dentro del intervalo [0,1]
    return u                                                   # Retorna los hijos con entradas reales y sin redondear

##################################################
#   F U N C I O N   D E L   A L G O R I T M O    #
##################################################
def evolucion_diferencial(configuracion, corrida, n_generaciones, n_individuos, longitud, degradacion, F, CR):
    #-------- << E T A P A  1 >> : G E N E R A C I Ó N   D E   L A   P O B L A C I Ó N   I N I C I A L --------------------------------------#
    experimento = 0                                            # Carpeta de la población inicial <Experimento0>
    x = parametros_regla4(n_individuos, longitud)              # Generar los parametros de la regla 4
    ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, poblacion = binarizacion(x, n_individuos, longitud)
    print(f'x: {x}')
    print(f'poblacion :{poblacion}')
    poblacion_inicial = generacion_individuos(configuracion, corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA) 
    # --------------------- Eliminar la carpeta experimento: ------------------------------------#
    # ----------------------La info se encuentra en la lista de objetos poblacion_inicial--------#
    ruta_actual = os.getcwd()
    ruta_experimento = os.path.abspath((os.path.join(ruta_actual,'..','..',f'Configuracion_{configuracion}',f'Corrida{corrida}',f'Experimento{experimento}')))
    shutil.rmtree(ruta_experimento)
    for i in range(n_individuos):
        x[i].append(poblacion_inicial[i].R_COMUNICACION)        # Agregar aptitud a cada individuo
        poblacion[i].append(poblacion_inicial[i].R_COMUNICACION)
        poblacion[i].append(poblacion_inicial[i].PUNTO_CRITICO)
        poblacion[i].append(poblacion_inicial[i].R_CONECTIVIDAD)                                 
        poblacion[i].append(poblacion_inicial[i].PROMEDIO)                                  

    # ---------------------- Almacenar al mejor en la población inicial -------------------------#
    tam = 1 + (2*longitud)                                         # Tamaño total del individuo con su aptitud
    mejores = [[0,[],[],0,0,0,0] for i in range(1+n_generaciones)] # Lista que guardara a los mejores por generación
    for i in range(n_individuos):                                  # Encuentra el mejor de la población inicial
        if poblacion[i][tam]> mejores[0][3]:
            #mejores[0] = x[i]
            mejores[0][0] = poblacion[i][0]
            mejores[0][1] = poblacion[i][1:1+longitud]
            mejores[0][2] = poblacion[i][1+longitud:tam]
            mejores[0][3] = poblacion[i][tam]
            mejores[0][4] = poblacion[i][tam + 1]
            mejores[0][5] = poblacion[i][tam + 2]
            mejores[0][6] = poblacion[i][tam + 3]
    # ------------------- Creación del archivo csv y registro de la poblacion inicial y el mejor ----------#
    ruta_actual = os.getcwd()                                                    # Obtenemos la ruta actual
    ruta_archivo_csv = os.path.abspath(os.path.join(ruta_actual,'..','..'))      # Ruta del archivo csv
    ruta_archivo_csv = os.path.abspath(os.path.join(ruta_archivo_csv, f'ArchivosConfiguracion_{configuracion}',f'Corrida{corrida}'))
    with open(ruta_archivo_csv+'_resultados.csv','w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['No.Generacion','Hijos','Poblacion','Mejor_alpha','Mejor_vector_pop','Mejor_vector_dist','Mejor_aptitud'])
        writer.writerow([
            0,
            str([]),
            str(poblacion),
            f'{mejores[0][0]}',
            ','.join(f'{a}' for a in mejores[0][1]),
            ','.join(f'{a}' for a in mejores[0][2]),
            f'{mejores[0][3]}',
            f'{mejores[0][4]}',
            f'{mejores[0][5]}',
            f'{mejores[0][6]}'])
        
    # ---------------------- I t e r a c i ó n   p a r a   l a s   s i g u i e n t e s   g e n e r a c i o n e s -------------------------#
    for k in range(1, n_generaciones + 1):
        #-------- << E T A P A  2 >> : C R E A C I Ó N   D E   L O S   H I J O S - ----------------------------------------------------------#
        u = generacion_hijos(x, n_individuos, F = F, CR = CR)             # hijos como listas reales
        n_hijos = len(u)
        ALPHA_HIJO,VECTOR_POPULARIDAD_HIJO,VECTOR_DISTANCIA_HIJO, generacion=binarizacion(u,n_hijos,longitud)# Binarización de los hijos
        hijos = generacion_individuos(configuracion, corrida, k, n_individuos, degradacion, ALPHA_HIJO, VECTOR_POPULARIDAD_HIJO, VECTOR_DISTANCIA_HIJO)
        # --------------------- Eliminar la carpeta experimento: ------------------------------------#
        # ----------------------La info se encuentra en la lista de objetos (hijos) -----------------#
        ruta_actual = os.getcwd()
        ruta_experimento = os.path.abspath((os.path.join(ruta_actual,'..','..',f'Configuracion_{configuracion}',f'Corrida{corrida}',f'Experimento{k}')))
        shutil.rmtree(ruta_experimento)
        #-------- << E T A P A  3 >> : S E L E C C I Ó N   D E   L O S   I N D I V I D U O S   M Á S   A P T O S   P O R   G E N E R A C I Ó N
        for i in range(n_individuos):                                     # Comparamos aptitud de hijos y padres
            u[i].append(hijos[i].R_COMUNICACION)                          # La aptitud de los hijos en la lista de objetos
            generacion[i].append(hijos[i].R_COMUNICACION)
            generacion[i].append(hijos[i].PUNTO_CRITICO)
            generacion[i].append(hijos[i].R_CONECTIVIDAD)
            generacion[i].append(hijos[i].PROMEDIO)
            if hijos[i].R_COMUNICACION >= x[i][tam]:                                                   
                x[i] = u[i]                                               # Reemplazar el padre por el hijo
                poblacion[i] = generacion[i]
                print(f'u_{i}: {u[i]}')
            else:
                print(f'x_{i}: {x[i]}')
        print(f'u: {u}')
        print(f'generacion: {generacion}')
        # ( A Q U I   Y A   S E   A C T U A L I Z Ó   X   Q U E   C O N T I E N E   L O S   I N D I V I D U O S   M Á S   A P T O S ) ----#
        for i in range(n_individuos):
            if poblacion[i][tam] > mejores[k][3]:                          # Encuentra el máximo por generación
                #mejores[k][0] = x[i][0]
                mejores[k][0] = poblacion[i][0]
                mejores[k][1] = poblacion[i][1:1+longitud]
                mejores[k][2] = poblacion[i][1+longitud:tam]
                mejores[k][3] = poblacion[i][tam]
                mejores[k][4] = poblacion[i][tam + 1]
                mejores[k][5] = poblacion[i][tam + 2]
                mejores[k][6] = poblacion[i][tam + 3]
            #mejores[k].append(x[i])
        # ------------------ Registramos la siguiente generación y el mejor ----------------------#
        with open(ruta_archivo_csv+'_resultados.csv','a',newline='') as f: # Abrir en modo append
            writer = csv.writer(f)
            writer.writerow([
                k,
                str(generacion),
                str(poblacion),
                f'{mejores[k][0]}',
                ','.join(f'{a}' for a in mejores[k][1]),
                ','.join(f'{b}' for b in mejores[k][2]),
                f'{mejores[k][3]}',
                f'{mejores[k][4]}',
                f'{mejores[k][5]}',
                f'{mejores[k][6]}'])                                                                  
        print(f'Nueva generacion: {x}')
    #------------- I N D I V I D U O   O P T I M O   P O R   C O R R I D A--------------#
    return mejores[n_generaciones], mejores
#########################################################################################################
# F U N C I O N   Q U E   C O N F I G U R A   C A D A   P R U E B A   P A R A   L A S   C O R R I D A S #
#########################################################################################################
def pruebas(configuracion, n_corridas, n_generaciones, n_individuos, degradacion, longitud, F, CR):
    ruta_actual = os.getcwd()                                           # Obtenemos la ruta actual
    ruta_grafica = os.path.abspath(os.path.join(ruta_actual,'..','..',f'ArchivosConfiguracion_{configuracion}'))
    os.makedirs(ruta_grafica, exist_ok=True)                            # Crear carpeta ArchivosConfiguracion_i
    #------- E J E C U T A R   V A R I A S   C O R R I D A S   D E L   A L G O R I T M O -----#
    aptitudes = []
    plt.figure()
    for j in range(n_corridas):
        individuo_optimo, mejor_por_generaciones = evolucion_diferencial(configuracion, j+1, n_generaciones,n_individuos,longitud,degradacion, F, CR)
        aptitudes.append(individuo_optimo[3])
        eje_x = [j for j in range(n_generaciones + 1)]
        eje_y = [k[3] for k in mejor_por_generaciones]
        plt.plot(eje_x, eje_y, label = f'corrida{j+1}')                    # Graficar el mejor en cada generacion de la corrida
    plt.title('Evolución de la aptitud en múltiples corridas')
    plt.xlabel('Generación')
    plt.ylabel('Aptitud')
    plt.legend()   
    plt.savefig(ruta_grafica+'/grafica_aptitud.png', dpi = 200)
    #------------------------------- E S T A D I S T I C A S ------------------------------------#
    df_aptitudes = pd.DataFrame(aptitudes)
    estadisticas = df_aptitudes.describe()
    with open(ruta_grafica+'/estadisticas.csv','w',newline='') as f:            # Guardar en cvs
        estadisticas.to_csv(f, index=True)
    #-------------------------- D I A G R A M A   D E   C A J A S -------------------------------#
    plt.figure(figsize=(10,6))
    plt.boxplot(aptitudes)
    plt.title('Diagrama de cajas')
    plt.ylabel('Aptitudes')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig(ruta_grafica+'/diag_cajas.png', dpi=200)
###################################################################################################
#                           P R U E B A S   D E L   A L G O R I T M O                             #
###################################################################################################
#--------(1) P R U E B A S   P A R A   L O S   5   P A R A M E T R O S   D I S T I N T O S -------#
F = [0.2, 0.4]              #[f1, f2]
CR = [0.5,0.7]              #[cr1, cr2]
n_corridas = [5]            #[cor1, cor2]
n_individuos = [5]          #[ind1, ind2]
n_generaciones = [3]        #[gen1, gen2]
longitud = 14
degradacion = 'Ataques'
configuracion = len(F)*len(CR)*len(n_corridas)*len(n_individuos)*len(n_generaciones) 
#--------- Iniciar con el numero de la primer configuracion en caso de que se detenga ------------#
tiempos = []
k = 1
for f in F:
    for cr in CR:
        for cor in n_corridas:
            for ind in n_individuos:
                for gen in n_generaciones:
                    inicio = time.perf_counter()
                    pruebas(configuracion=k, n_corridas=cor, n_generaciones=gen, n_individuos=ind, degradacion=degradacion, longitud=longitud, F=f, CR=cr)
                    fin = time.perf_counter()
                    duracion = fin - inicio
                    minutos = duracion / 60
                    tiempos.append({'Configuracion':k,'Corrida':cor, 'Generaciones':gen, 'Individuos':ind, 'F':f, 'CR':cr, 'Tiempo_Segundos':duracion, 'Tiempo_minutos':minutos})
                    #--------------------- Borrar carpetas de las corridas------------------------#
                    ruta_actual = os.getcwd()
                    ruta_configuracion = os.path.abspath((os.path.join(ruta_actual,'..','..',f'Configuracion_{k}')))
                    shutil.rmtree(ruta_configuracion)
                    k += 1
#------------------------ Aqui terminan de ejecutarse las configuraciones ------------------------#
df_tiempos = pd.DataFrame(tiempos)                     # Preparar para guarda en una archivo csv
ruta_actual = os.getcwd()
ruta_archivo = os.path.abspath(os.path.join(ruta_actual, '..', '..'))
ruta_tiempos = os.path.join(ruta_archivo,'tiempos.csv')
with open(ruta_tiempos,'w',newline='') as f:           # Guardar en cvs
    df_tiempos.to_csv(f, index=False)
datos = [[] for entrada in range(configuracion)]       # Extraer informacion de cada carpeta de configuracion
print(datos)
#-----------------(2) Obtención de la mejor aptitud de cada corrida ------------------------------#
for a in range(1, configuracion + 1):
    for b in n_corridas:                               # Obtener las corridas que correponden a cada configuracion
        for c in range(1 , b + 1):
            ruta_archivo_corrida = os.path.join(ruta_archivo, f'ArchivosConfiguracion_{a}', f'Corrida{c}_resultados.csv')
            with open(ruta_archivo_corrida, newline="", encoding="utf-8") as f:
                reader = list(csv.reader(f))
                ultima_fila = reader[-1]
                valor = float(ultima_fila[-4])
                datos[a-1].append(valor)
print(f'dato: {datos}')
#------------------(3) Diagrama de cajas ---------------------------------------------------------#
ruta_cajas = os.path.join(ruta_archivo, 'cajas.png')
print(f'ruta_cajas: {ruta_cajas}')
df_configuraciones = pd.DataFrame()     # Crear un DataFrame mejor aptitud de cada corrida
c = 0                                   # Posicion de la lista corresponendiente a la configuracion
for f in F:
    for cr in CR:
        for cor in n_corridas:
                for ind in n_individuos:
                    for gen in n_generaciones:
                        df_configuraciones[f'F={f}\nCR={cr}\nCorridas={cor}\nIndividuos={ind}\nGeneraciones={gen}'] = datos[c]
                        c +=1
plt.figure(figsize=(30,8))
df_config = df_configuraciones.melt(var_name='Configuracion', value_name='Aptitud')
ax =sns.boxplot(x='Configuracion', y='Aptitud', hue='Configuracion',data=df_config, palette='Set2')
plt.savefig(ruta_cajas, dpi=300, bbox_inches='tight')
