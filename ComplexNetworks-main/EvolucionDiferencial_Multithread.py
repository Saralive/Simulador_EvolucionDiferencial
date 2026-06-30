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
import rewind
from concurrent.futures import ThreadPoolExecutor
import configEvolucionDiferencial
#############################################################################################################
#      F U N C I O N E S   P A R A   C O N S T R U I R   E L   A L G O R I T M O   G E N E R T I C O        #
#############################################################################################################
###########################  G E N E R A C I Ó N   D E   I N D I V I D U O S  ################################
#---------------------------(  P A R A L E L I Z A D A   C O N   H I L O S  )-------------------------------#
def generacion_individuos(configuracion,corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA,pool_hilos):
    configuracion = str(configuracion)
    corrida = str(corrida)
    experimento = str(experimento)
    #-----------(1) RUTAS ---------------------------------------------------------------------------------------------#
    ruta_actual = os.getcwd()                                                               # Obtener la ruta actual
    ruta_configuracion = os.path.abspath(os.path.join(ruta_actual,'..','..'))
    ruta_configuracion = os.path.join(ruta_configuracion, f'Configuracion_{configuracion}') # Ruta de la configuracion
    ruta_corrida = os.path.join(ruta_configuracion,f'Corrida{corrida}')                     # Ruta de la carpeta Corrida
    os.makedirs(ruta_corrida, exist_ok=True)

    #-----------(2) CREAR LA CARPETA EXPERIMENTO ----------------------------------------------------------------------#
    ruta_experimento = os.path.join(ruta_corrida,f'Experimento{experimento}')
    os.makedirs(ruta_experimento, exist_ok=True)

    #-----------(3) CREAR UNA CARPETA POR INDIVIDUO DEL EXPERIMENTO ---------------------------------------------------#
    individuos = [None]*n_individuos                                                           # Lista de individuos
    #-----------(4) CREAR UN POOL DE HILOS -----------------------------------------------------------------#
    with ThreadPoolExecutor(max_workers=pool_hilos) as executor:
        equipos = []
        for i in range(1, n_individuos + 1):
            #---(5) MAPEO DE LAS TAREAS DE FORMA DINAMICA ---------------------------------------#
            f = executor.submit(
                rewind.ejecutar_experimento, 
                i, ruta_experimento, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA)
            equipos.append(f)
        #-------(6) LANZAR LOS EQUIPOS DE HILOS -------------------------------------------------#
        for f in equipos:
            regla, id_individuo = f.result()
            if regla is None:                                               # Si el hilo falló (retornó None)
                print(f"Alerta: Guardando 'None' en el índice {id_individuo-1} debido al fallo anterior.")
            individuos[id_individuo - 1] = regla                          
            
    return individuos      
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

#################################################################################################
#  F U N C I O N   D E L   A L G O R I T M O   D E   E V O L U C I O N   D I F E R E N C I A L  #
#################################################################################################
def evolucion_diferencial(configuracion, corrida, n_generaciones, n_individuos, longitud, degradacion, F, CR, pool_hilos):
    #-------- << E T A P A  1 >> : G E N E R A C I Ó N   D E   L A   P O B L A C I Ó N   I N I C I A L --------------------------------------#
    experimento = 0                                            # Carpeta de la población inicial <Experimento0>
    x = parametros_regla4(n_individuos, longitud)              # Generar los parametros de la regla 4
    ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, poblacion = binarizacion(x, n_individuos, longitud)
    print(f'x: {x}')
    print(f'poblacion :{poblacion}')
    poblacion_inicial = generacion_individuos(configuracion, corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, pool_hilos) 
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
    ruta_archivo_csv = os.path.abspath(os.path.join(ruta_archivo_csv, f'ArchivoConfiguracion_{configuracion}',f'Corrida{corrida}'))
    with open(ruta_archivo_csv+'_resultados.csv','w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['No.Generacion','Hijos','Poblacion','Mejor_alpha','Mejor_vector_pop','Mejor_vector_dist','Mejor_aptitud', 'Punto_critico', 'R_conectividad', 'Promedio'])
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
        hijos = generacion_individuos(configuracion, corrida, k, n_individuos, degradacion, ALPHA_HIJO, VECTOR_POPULARIDAD_HIJO, VECTOR_DISTANCIA_HIJO,pool_hilos)
        # --------------------- Eliminar la carpeta experimento: ------------------------------------#
        # ----------------------La info se encuentra en la lista de objetos poblacion_inicial--------#
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
def pruebas(configuracion, n_corridas, n_generaciones, n_individuos, degradacion, longitud, F, CR, pool_hilos):
    ruta_actual = os.getcwd()                                           # Obtenemos la ruta actual
    ruta_grafica = os.path.abspath(os.path.join(ruta_actual,'..','..',f'ArchivoConfiguracion_{configuracion}'))
    os.makedirs(ruta_grafica, exist_ok=True)                             # Crear carpeta de resultados
    #------- E J E C U T A R   V A R I A S   C O R R I D A S   D E L   A L G O R I T M O -----#
    aptitudes = []
    plt.figure()
    for j in range(n_corridas):
        individuo_optimo, mejor_por_generaciones = evolucion_diferencial(configuracion, j+1, n_generaciones,n_individuos,longitud,degradacion, F, CR, pool_hilos)
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
F = configEvolucionDiferencial.F
CR = configEvolucionDiferencial.CR
n_corridas = configEvolucionDiferencial.N_CORRIDAS
n_individuos = configEvolucionDiferencial.N_INDIVIDUOS
n_generaciones = configEvolucionDiferencial.N_GENERACIONES
longitud = configEvolucionDiferencial.LONGITUD
degradacion = configEvolucionDiferencial.DEGRADACION
pool_hilos = configEvolucionDiferencial.POOL_HILOS
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
                    pruebas(configuracion=k, n_corridas=cor, n_generaciones=gen, n_individuos=ind, degradacion=degradacion, longitud=longitud, F=f, CR=cr, pool_hilos=pool_hilos)
                    fin = time.perf_counter()
                    duracion = fin - inicio
                    minutos = duracion / 60
                    tiempos.append({'Configuracion':k,'Corrida':cor, 'Generaciones':gen, 'Individuos':ind, 'F':f, 'CR':cr, 'Tiempo_Segundos':duracion, 'Tiempo_minutos':minutos})
                    # ---------- Eliminar capetas de las corridas de cada configuracion ----------#
                    ruta_actual = os.getcwd()
                    ruta_configuracion = os.path.abspath((os.path.join(ruta_actual,'..','..',f'Configuracion_{k}')))
                    shutil.rmtree(ruta_configuracion)
                    k += 1
#------------------------ Aqui terminan de ejecutarse las configuraciones ------------------------#
df_tiempos = pd.DataFrame(tiempos)                     # Preparar para guarda en una archivo csv
print(df_tiempos)
ruta_actual = os.getcwd()
ruta_archivo = os.path.abspath(os.path.join(ruta_actual, '..', '..'))
df_tiempos.to_csv(ruta_archivo+'tiempos.csv', index=False)
datos = [[] for entrda in range(configuracion)]        # Extraer informacion de cada carpeta de configuracion
#-----------------(2) Obtención de la mejor aptitud de cada corrida ------------------------------#
for a in range(1, configuracion + 1):
    for b in n_corridas:                               # Obtener las corridas que correponden a cada configuracion
        for c in range(1 , b + 1):
            ruta_archivo_corrida = os.path.join(ruta_archivo, f'ArchivoConfiguracion_{a}', f'Corrida{c}_resultados.csv')
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
df_config = df_configuraciones.melt(var_name='Configuracion', value_name='Aptitud')
ax =sns.boxplot(x='Configuracion', y='Aptitud', data=df_config,hue='Configuracion', palette="Set2")
plt.savefig(ruta_cajas, dpi=300, bbox_inches='tight')
