import os
import csv
import numpy as np
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
from pathlib import Path
from individuo import Individuo

###########################  G E N E R A C I Ó N   D E   I N D I V I D U O S  ################################
def generacion_individuos(corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA):
    corrida =str(corrida)
    experimento = str(experimento)
    #-----------(1) RUTAS ----------------------------------------------------------------------------------#
    ruta_actual = os.getcwd()                                                 # Obtener la ruta actual
    ruta_corrida = os.path.abspath(os.path.join(ruta_actual,'..','..'))
    ruta_corrida = os.path.join(ruta_corrida,f'Corrida{corrida}')             # Ruta de la carpeta Corrida
    os.makedirs(ruta_corrida, exist_ok=True)

    #-----------(2) CREAR LA CARPETA EXPERIMENTO -----------------------------------------------------------#
    ruta_experimento = os.path.join(ruta_corrida,f'Experimento{experimento}')
    os.makedirs(ruta_experimento, exist_ok=True)

    #-----------(3) CREAR UNA CARPETA POR INDIVIDUO DEL EXPERIMENTO-----------------------------------------#
    individuos = []                                                           # Lista los objetos individuo
    for i in range(1, n_individuos + 1):
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
        ruta_configFormacion_opt = os.path.join(regla.INDIVIDUO_DIR,'configFormacion_opt.py')
        with open(ruta_configFormacion_opt, 'a', encoding = 'utf-8') as f:
            f.write(f'\nALPHA = {regla.ALPHA}')
            f.write(f'\nVECTOR_POPULARIDAD = {regla.VECTOR_POPULARIDAD}')
            f.write(f'\nVECTOR_DISTANCIA = {regla.VECTOR_DISTANCIA}')

        #-------(7) AGREGAR TIPO DE DEGRADACION EN ARCHIVO DE CONFIGURACION --------------------------------#
        ruta_configDegradacion_opt = os.path.join(regla.INDIVIDUO_DIR,'configDegradacion_opt.py')
        with open(ruta_configDegradacion_opt, 'a', encoding = 'utf-8') as f:
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
        regla.robustez()
        #--------(11) GUARDAR CONFIGURACIONES DE CADA INDIVIDUO --------------------------------------------# 
        individuos.append(regla)
    return individuos                                          # Retorna un lista de objetos

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

def generacion_hijos(x, n_hijos,F=0.4, CR =0.5):
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

##########################################################################################################################################
#############################    A L G O R I T M O   E V O L U C I O N   D I F E R E N C I A L #################################
##########################################################################################################################################
def evolucion_diferencial(corrida, n_generaciones, n_individuos, longitud, degradacion):
    #-------- << E T A P A  1 >> : G E N E R A C I Ó N   D E   L A   P O B L A C I Ó N   I N I C I A L --------------------------------------#
    experimento = 0                                                                              # Carpeta de la población inicial <Experimento0>
    x = parametros_regla4(n_individuos, longitud)                                                # Generar los parametros de la regla 4
    ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, poblacion = binarizacion(x, n_individuos, longitud)
    print(f'x: {x}')
    print(f'poblacion :{poblacion}')
    poblacion_inicial = generacion_individuos(corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA) 
    for i in range(n_individuos):
        x[i].append(poblacion_inicial[i].R_COMUNICACION)         # FUNCIÓN APTITUD                                             # Agregar aptitud a cada individuo
        poblacion[i].append(poblacion_inicial[i].R_COMUNICACION) # FUNCIÓN APTITUD
        poblacion[i].append(poblacion_inicial[i].PUNTO_CRITICO)
        poblacion[i].append(poblacion_inicial[i].R_CONECTIVIDAD)                                 
        poblacion[i].append(poblacion_inicial[i].PROMEDIO)                                  

    # ---------------------- Almacenar al mejor en la población inicial -------------------------#
    tam = 1 + (2*longitud)                                                                       # Tamaño total del individuo con su aptitud
    mejores = [[0,[],[],0,0,0,0] for i in range(1+n_generaciones)]                               # Lista que guardara a los mejores por generación
    for i in range(n_individuos):                                                                # Encuentra el mejor de la población inicial
        if poblacion[i][tam]> mejores[0][3]:
            mejores[0][0] = poblacion[i][0]
            mejores[0][1] = poblacion[i][1:1+longitud]
            mejores[0][2] = poblacion[i][1+longitud:tam]
            mejores[0][3] = poblacion[i][tam]
            mejores[0][4] = poblacion[i][tam + 1]
            mejores[0][5] = poblacion[i][tam + 2]
            mejores[0][6] = poblacion[i][tam + 3]
    # ------------------- Creación del archivo csv y registro de la poblacion inicial y el mejor ----------#
    ruta_actual = os.getcwd()                                                                    # Obtenemos la ruta actual
    ruta_archivo_csv = os.path.abspath(os.path.join(ruta_actual,'..','..',f'Corrida{corrida}'))  # Ruta del archivo csv
    with open(ruta_archivo_csv+'_resultados.csv','w',newline='') as f:
        writer = csv.writer(f) # Mejor_aptitud = r_comunicacion
        writer.writerow(['No.Generacion','Hijos','Poblacion','Mejor_alpha','Mejor_vector_pop','Mejor_vector_dist','Mejor_aptitud','punto_critico','r_conectividad','promedio'])
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
        u = generacion_hijos(x, n_individuos, F=0.4)                                              # hijos como listas reales
        n_hijos = len(u)
        ALPHA_HIJO,VECTOR_POPULARIDAD_HIJO,VECTOR_DISTANCIA_HIJO, generacion=binarizacion(u,n_hijos,longitud)# Binarización de los hijos
        hijos = generacion_individuos(corrida, k, n_individuos, degradacion, ALPHA_HIJO, VECTOR_POPULARIDAD_HIJO, VECTOR_DISTANCIA_HIJO)

        #-------- << E T A P A  3 >> : S E L E C C I Ó N   D E   L O S   I N D I V I D U O S   M Á S   A P T O S   P O R   G E N E R A C I Ó N
        for i in range(n_individuos):                                                            # Comparamos aptitud de hijos y padres
            u[i].append(hijos[i].R_COMUNICACION)           # FUNCIÓN APTITUD                                             # La aptitud de los hijos en la lista de objetos
            generacion[i].append(hijos[i].R_COMUNICACION)  # FUNCIÓN APTITUD
            generacion[i].append(hijos[i].PUNTO_CRITICO)
            generacion[i].append(hijos[i].R_CONECTIVIDAD)
            generacion[i].append(hijos[i].PROMEDIO)
            if hijos[i].R_COMUNICACION >= x[i][tam]:                                                    
                x[i] = u[i]                                                                      # Reemplazar el padre por el hijo
                poblacion[i] = generacion[i]
                print(f'u_{i}: {u[i]}')
            else:
                print(f'x_{i}: {x[i]}')
        print(f'u: {u}')
        print(f'generacion: {generacion}')
        # ( A Q U I   Y A   S E   A C T U A L I Z Ó   X   Q U E   C O N T I E N E   L O S   I N D I V I D U O S   M Á S   A P T O S ) ----#
        for i in range(n_individuos):
            if poblacion[i][tam] > mejores[k][3]:                                               # Encuentra el máximo por generación
                mejores[k][0] = poblacion[i][0]
                mejores[k][1] = poblacion[i][1:1+longitud]
                mejores[k][2] = poblacion[i][1+longitud:tam]
                mejores[k][3] = poblacion[i][tam]
                mejores[k][4] = poblacion[i][tam + 1]
                mejores[k][5] = poblacion[i][tam + 2]
                mejores[k][6] = poblacion[i][tam + 3]
        # ------------------ Registramos la siguiente generación y el mejor ----------------------#
        with open(ruta_archivo_csv+'_resultados.csv','a',newline='') as f:                        # Abrir en modo append
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

###############################################################################################################
################# C O N D I C I O N E S   I N I C I A L E S   D E L   A L G O R I T M O #######################
###############################################################################################################
n_individuos = 5                                               # Cantidad de individuos de la población inicial
degradacion = 'Ataques'                                        # Seleccionar 'Ataques' o 'Fallas'
longitud = 14                                                  # Longitud de los vectores de selección
n_generaciones = 3                                             # Número de generaciones
ruta_actual = os.getcwd()                                      # Obtenemos la ruta actual
ruta_grafica = os.path.abspath(os.path.join(ruta_actual,'..','..'))
n_corridas = 3
#--------------------- C O R R I D A S   D E L   A L G O R I T M O ---------------------#
aptitudes = []                                                 # Guardar las aptitudes por generación y por corrida
plt.figure()
for i in range(n_corridas):
    individuo_optimo, mejor_por_generaciones = evolucion_diferencial(i+1, n_generaciones,n_individuos,longitud,degradacion)
    aptitudes.append(individuo_optimo[3])
    eje_x = [j for j in range(n_generaciones + 1)]
    eje_y = [k[3] for k in mejor_por_generaciones]
    plt.plot(eje_x, eje_y, label = f'corrida{i+1}')

plt.title('Evolución de la aptitud en múltiples corridas')
plt.xlabel('Generación')
plt.ylabel('Aptitud')
plt.legend()   
plt.savefig(ruta_grafica+'/grafica_aptitud.png', dpi = 200)
#------------------------------- E S T A D I S T I C A S ----------------------------------#
df_aptitudes = pd.DataFrame(aptitudes)
estadisticas = df_aptitudes.describe()
with open(ruta_grafica+'/estadisticas.csv','w',newline='') as f:   #Guardar en cvs
    estadisticas.to_csv(f, index=True)
#-------------------------- D I A G R A M A   D E   C A J A S -----------------------------#
plt.figure(figsize=(10,6))
plt.boxplot(aptitudes)
plt.title('Diagrama de cajas')
plt.ylabel('Aptitudes')
plt.grid(True, linestyle='--', alpha=0.5)
plt.savefig(ruta_grafica+'/diag_cajas.png', dpi=200)
