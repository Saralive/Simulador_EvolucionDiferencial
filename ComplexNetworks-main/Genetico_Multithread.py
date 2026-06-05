import os
import csv
import numpy as np
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from individuo import Individuo, IndividuoAlgoritmo
import threading
import queue
import time
import shutil
import random
import copy
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

    #-------(7) AGREGAR TIPO DE DEGRADACION EN ARCHIVO DE CONFIGURACION --------------------------------#
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
    retornar.put([regla, i])                                           # Objeto y el id del individuo
#############################################################################################################
#--------------------------- G E N E R A C I Ó N   D E   I N D I V I D U O S -------------------------------#
#---------------------------(  P A R A L E L I Z A D A   C O N   H I L O S  )-------------------------------#
def generacion_individuos(configuracion,corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, pool_hilos):
    configuracion = str(configuracion)
    corrida = str(corrida)
    experimento = str(experimento)
    #-----------(1) RUTAS ----------------------------------------------------------------------------------#
    ruta_actual = os.getcwd()                                                 # Obtener la ruta actual
    ruta_configuracion = os.path.abspath(os.path.join(ruta_actual,'..','..'))
    ruta_configuracion = os.path.join(ruta_configuracion, f'Configuracion_{configuracion}') # Ruta de la configuracion
    ruta_corrida = os.path.join(ruta_configuracion,f'Corrida{corrida}')      # Ruta de la carpeta Corrida
    os.makedirs(ruta_corrida, exist_ok=True)
    #-----------(2) CREAR LA CARPETA EXPERIMENTO -----------------------------------------------------------#
    ruta_experimento = os.path.join(ruta_corrida,f'Experimento{experimento}')
    os.makedirs(ruta_experimento, exist_ok=True)
    #-----------(3) CREAR UNA CARPETA POR INDIVIDUO DEL EXPERIMENTO ----------------------------------------#
    individuos = [0]*n_individuos                             # Lista de individuos
    #-----------( P O O L S   D E   H I L O S )-------------------------------------------------------------#
    #(pool_hilos) como parametro de entrada de esta funcion   # Numero de hilos que soporta la maquina (15)
    total_pools =int(n_individuos/pool_hilos)                 # Dividir entre el numero de hilos de la maquina
    for h in range(total_pools):                              # Numero de equipos de hilos a lanzar
        hilos = []                                            # Llevar un conteo del equipo de los hilos
        retornar = queue.Queue()                              # Obtener lo que retorna la funcion
        #-----------(4) CREAR UN HILO POR CADA INDIVIDUO ---------------------------------------------------#
        for i in range(1 + h*pool_hilos, 1 + (h+1)*pool_hilos):
            #print(f'i: {i}')
            t = threading.Thread(target=ejecutar_experimento, args=(i, ruta_experimento, retornar, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA ))
            hilos.append(t)
        #-----------(5) INICIAR TODOS LOS HILOS ------------------------------------------------------------#
        for t in hilos:
            t.start()                                         # Ejecución del hilo
        #-----------(6) ESPERAR QUE TERMINEN TODOS LOS HILOS -----------------------------------------------#
        for t in hilos:
            t.join()                                          # Esperar que terminen cada hilo
        #-----------(7) GUARDAR LOS RESULTADOS DE CADA HILO DONDE CORRESPONDE ------------------------------#
        while not retornar.empty():
            regla , id = retornar.get()                       # Retorna el objeto individuo y el id del individuo
            individuos[id-1] = regla                          # Guarda las configuraciones de cada individuo 
    return individuos                                         # Retorna una lista de objetos
#############################################################################################################
#      F U N C I O N E S   P A R A   C O N S T R U I R   E L   A L G O R I T M O   G E N E R T I C O        #
#############################################################################################################
#---- G E N E R A C I O N   A L E A T O R I A   D E   L O S   P A R A M E T R O S   D E   L A   R E G L A   4
def generacion_poblacion_inicial(n_individuos, longitud):
    x = []                      # X se convertira en una lista de objetos de individuos del algoritmo
    for i in range(n_individuos):
        real = round(np.random.uniform(0,1),3)
        binarios1 = np.random.randint(2, size=longitud).tolist()
        binarios2  = np.random.randint(2, size=longitud).tolist()
        #---------CREACION DE UNA INSTANCIA DE LA CLASE (IndividuoAlgoritmo)-------------------------#
        individuo = IndividuoAlgoritmo(i+1, real, binarios1, binarios2)
        x.append(individuo)
    return x                                                    # Retorna una lista de objetos
def parametros_simulador(x):
    ALPHA =[]
    VECTOR_POPULARIDAD = []
    VECTOR_DISTANCIA = []
    for objeto_individuo in x:
        ALPHA.append(objeto_individuo.ALPHA)
        VECTOR_POPULARIDAD.append(objeto_individuo.POPULARIDAD)
        VECTOR_DISTANCIA.append(objeto_individuo.DISTANCIA)
    return ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA          # Retorna tres listas
def seleccion_torneo1(poblacion, n_individuos, n_padres, n_torneo = 3):
    padres = []
    torneos =[]
    entradas = set(range(n_individuos))                         # Lista de las posiciones de los individuos
    for i in range(n_padres):
        torneo = []
        indices_torneo = random.sample(list(entradas),n_torneo) # Elegir aletoriamente n_torneo individuos distintos
        torneo.extend([poblacion[j] for j in indices_torneo])   # Se toma una muestra de tamaño n_torneo (lista de objetos)
        indice_padre = max(indices_torneo, key=lambda j: poblacion[j].COMUNICACION)
        padre = poblacion[indice_padre]
        entradas.remove(indice_padre)
        padres.append(padre)
        torneos.append(torneo)
    return torneos, padres

def seleccion_torneo(poblacion, n_individuos, n_padres, n_torneo = 3):
    padres = []
    torneos =[]
    entradas = set(range(n_individuos))                         # Lista de las posiciones de los individuos
    for i in range(n_padres):
        torneo = []
        indices_torneo = random.sample(list(entradas),n_torneo) # Elegir aletoriamente n_torneo individuos distintos
        torneo.extend([poblacion[j] for j in indices_torneo])   # Se toma una muestra de tamaño n_torneo (lista de objetos)
        indice_padre = max(indices_torneo, key=lambda j: poblacion[j].COMUNICACION)
        padre = poblacion[indice_padre]
        entradas.remove(indice_padre)
        padres.append(padre)
        torneos.append(torneo)
    return torneos, padres

def Binario_A_Real(cromosoma, longitud, a = 0, b = 1):# Real en el intervalo [a,b]
    n_bits = longitud
    entero = 0                                        # Contador para obtener el entero
    for i in range(n_bits):                           # Recorre los bits del cromosoma
        bit = cromosoma[n_bits - 1 -i]                # Accede al bit desde el final (derecha a izquierda)
        entero += bit * (2**i)                        # Multiplica el bit actual por la potencia de 2
    real = a + entero * (b - a) / (2**n_bits - 1)     # Interpolación lineal (entero a real)
    return round(real, 3)

def Real_A_Binario(real, n_bits, a = 0, b = 1):
    valor_normalizado = (real - a)/ (b - a)
    maximo_valor = 2**n_bits -1
    entero = round(valor_normalizado*maximo_valor)
    entero = max(0, min(entero, maximo_valor))
    binario = []
    for i in range(n_bits -1, -1, -1):
        if entero // (2**i)%2 == 1: # Division entera
            bit = 1
        else:
            bit = 0
        binario.append(bit)
    return binario

#############################################################################################################
#                            A L G O R I T M O   G E N E T I C O   H I B R I D O                            #
#############################################################################################################
def genetico(configuracion, corrida, n_generaciones, n_individuos, longitud, degradacion, pool_hilos, n_torneo, n_padres, n_cruza, pc, pm_binaria):
    # ----------<< E T A P A  1 >>: G E N E R A C I O N   D E   L A   P O B L A C I O N   I N I C I A L---------#
    experimento  = 0                                             # Carpeta de la población inicial <Experimento0>
    x = generacion_poblacion_inicial(n_individuos, longitud)
    ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA = parametros_simulador(x)
    print(x)
    poblacion_inicial = generacion_individuos(configuracion, corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, pool_hilos) 
    print(poblacion_inicial)
    # --------------------- Eliminar la carpeta Experimento: ------------------------------------#
    # ----------------------La info se encuentra en la lista de objetos poblacion_inicial y en x-#
    ruta_actual = os.getcwd()
    ruta_experimento = os.path.abspath((os.path.join(ruta_actual,'..','..',f'Configuracion_{configuracion}',f'Corrida{corrida}',f'Experimento{experimento}')))
    shutil.rmtree(ruta_experimento)
    for i in range(n_individuos): # Actualizar los coeficientes que representa la resistencia de la red
        x[i].COMUNICACION = poblacion_inicial[i].R_COMUNICACION
        x[i].PUNTO_CRITICO = poblacion_inicial[i].PUNTO_CRITICO
        x[i].CONECTIVIDAD = poblacion_inicial[i].R_CONECTIVIDAD                                
        x[i].PROMEDIO = poblacion_inicial[i].PROMEDIO  
    for i in range(n_individuos):
        print(x[i].COMUNICACION)
        print(x[i].PUNTO_CRITICO)
        print(x[i].CONECTIVIDAD) 
        print(x[i].PROMEDIO)
    # ---------------------- Almacenar al mejor en la población inicial -------------------------#
    mejores = [[0,[],[],0,0,0,0] for i in range(1+n_generaciones)] # Lista que guardara a los mejores por generación
    for i in range(n_individuos):                                  # Encuentra el mejor de la población inicial
        if x[i].COMUNICACION> mejores[0][3]:
            mejores[0][0] = x[i].ALPHA
            mejores[0][1] = x[i].POPULARIDAD
            mejores[0][2] = x[i].DISTANCIA
            mejores[0][3] = x[i].COMUNICACION
            mejores[0][4] = x[i].PUNTO_CRITICO
            mejores[0][5] = x[i].CONECTIVIDAD
            mejores[0][6] = x[i].PROMEDIO
    # ------------------- Creación del archivo csv y registro de la poblacion inicial y el mejor ----------#
    ruta_actual = os.getcwd()                                                    # Obtenemos la ruta actual
    ruta_archivo_csv = os.path.abspath(os.path.join(ruta_actual,'..','..'))      # Ruta del archivo csv
    ruta_archivo_csv = os.path.abspath(os.path.join(ruta_archivo_csv, f'ArchivoConfiguracion_{configuracion}',f'Corrida{corrida}'))
    with open(ruta_archivo_csv+'_resultados.csv','w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['No.Generacion','Mejor_alpha','Mejor_vector_pop','Mejor_vector_dist','Mejor_aptitud', 'Punto_critico', 'R_conectividad', 'Promedio'])
        writer.writerow([
            0,
            f'{mejores[0][0]}',
            ','.join(f'{a}' for a in mejores[0][1]),
            ','.join(f'{a}' for a in mejores[0][2]),
            f'{mejores[0][3]}',
            f'{mejores[0][4]}',
            f'{mejores[0][5]}',
            f'{mejores[0][6]}'])
    #--------- I t e r a c i ó n   p a r a   l a s   s i g u i e n t e s   g e n e r a c i o n e s -----------#
    for k in range(1, n_generaciones + 1):
        #-------- C R E A C I O N   D E   L A   N U E V A   P O B L A C I O N --------------------------------#
        #-----------------------( Compuesta por padres e hijos )----------------------------------------------#
        #-------- << E T A P A  2 >> : C R E A C I Ó N   D E   L O S   H I J O S -----------------------------#
        poblacion_nueva = []                                                           # Ponerlo como conjunto
        #nueva_generacion = []
        id_hijo = 1
        while len(poblacion_nueva) < n_individuos:
            #-------------------< < SELECCION DE PADRES > >-----------------------------------------------------------#
            #-----( se producen dos hijos con n_padres arbitrarios )
            seleccionados_a_torneo, mejor_padre = seleccion_torneo(x, n_individuos, n_padres, n_torneo)
            #-------------------< < I m p r e s i o n   d e   l o s   r e s u l t a d o s > >-------------------------#
            for padre in seleccionados_a_torneo:
                for j in padre:
                    print(j.COMUNICACION)
            for mejor in mejor_padre:
                print(f'mejor_padre: {mejor.COMUNICACION}')
            #-----( se producen dos hijos con n_padres arbitrarios )
            padre_1 = copy.deepcopy(mejor_padre[0]) # objeto 
            padre_2 = copy.deepcopy(mejor_padre[1]) # objeto
            #-- C O N V E R T I R   D E   R E A L   A   B I N A R I O   E L   A L P H A   D E   C A D A   P A D R E --#
            print(f'padre1_real: {padre_1.ALPHA}, Tipo: {type(padre_1.ALPHA)}')
            print(f'padre2_real: {padre_2.ALPHA}, Tipo: {type(padre_2.ALPHA)}')
            padre_1.ALPHA = Real_A_Binario(padre_1.ALPHA, longitud)
            padre_2.ALPHA = Real_A_Binario(padre_2.ALPHA, longitud)
            print(f'Binario_padre1: {padre_1.ALPHA}')
            print(f'Binario_padre2: {padre_2.ALPHA}')
            #-------- << E T A P A  2 >> : C R E A C I Ó N   D E   L O S   H I J O S ---------------------------------#
            #--------------------< < CRUZA > > -----------------------------------------------------------------------#
            if random.uniform(0,1) < pc:                                                        # Probabalidad de cruza
                #----- -----------------------( C R U Z A   E N   D O S   P U N T O S )-------------------------------#
                numeros = [i for i in range(1, longitud)]
                ca = sorted(random.sample(numeros, n_cruza))                 # Puntos de cruza para el binario de alpha
                cp = sorted(random.sample(numeros, n_cruza))                 # Puntos de cruza del vector popularidad
                cd = sorted(random.sample(numeros, n_cruza))                 # Puntos de cruza del vector distancia
                ca_1 = min(ca)
                ca_2 = max(ca)
                cp_1 = min(cp)
                cp_2 = max(cp)
                cd_1 = min(cd)
                cd_2 = max(cd)
                #----- C R E A C I O N   D E   L O S   O B J E T O S   H I J O S --------------------------------------#
                #------> IndividuosAlgoritmo( ID, ALPHA ,VECTOR_POPULARIDAD , VECTOR_DISTANCIA )
                hijo_1 = IndividuoAlgoritmo(id_hijo,
                                            padre_1.ALPHA[0:ca_1]+padre_2.ALPHA[ca_1:ca_2]+padre_1.ALPHA[ca_2:longitud],
                                            padre_1.POPULARIDAD[0:cp_1]+padre_2.POPULARIDAD[cp_1:cp_2]+padre_1.POPULARIDAD[cp_2:longitud],
                                            padre_1.DISTANCIA[0:cd_1]+padre_2.DISTANCIA[cd_1:cd_2]+padre_1.DISTANCIA[cd_2:longitud]
                                            )
                hijo_2 = IndividuoAlgoritmo(id_hijo + 1,
                                            padre_2.ALPHA[0:ca_1]+padre_1.ALPHA[ca_1:ca_2]+padre_1.ALPHA[ca_2:longitud],
                                            padre_2.POPULARIDAD[0:cp_1]+padre_1.POPULARIDAD[cp_1:cp_2]+padre_2.POPULARIDAD[cp_2:longitud],
                                            padre_2.DISTANCIA[0:cd_1]+padre_1.DISTANCIA[cd_1:cd_2]+padre_2.DISTANCIA[cd_2:longitud]
                                            )
                print(f'padre_1: {padre_1.ALPHA}, {padre_1.POPULARIDAD}, {padre_1.DISTANCIA}')
                print(f'padre_2: {padre_2.ALPHA}, {padre_2.POPULARIDAD}, {padre_2.DISTANCIA}')
                print(f'hijo_1: {hijo_1.ALPHA}, {hijo_1.POPULARIDAD}, {hijo_1.DISTANCIA}')
                print(f'hijo_2: {hijo_2.ALPHA}, {hijo_2.POPULARIDAD}, {hijo_2.DISTANCIA}')
                poblacion_nueva.append(hijo_1)
                poblacion_nueva.append(hijo_2)
            else:
                #-------- L O S   P A D R E S  P A S A N   A   L A   S I G U I E N T E   G E N E R A C I O N----#  
                poblacion_nueva.append(padre_1)
                poblacion_nueva.append(padre_2)
            id_hijo += 2
            print(len(poblacion_nueva))
            #---( S E   C O N S T R U Y O   L A   N U E V A   P O B L A C I O N   C O N   A L P H A   E N   B I N A R I O )---#
        #-------------< <  M U T A C I O N  > >------------------------------------------#
        #----( Alteracion de los bits de la poblacion_nueva con cierta probabilidad )----#
        for hijo in poblacion_nueva:
            #---M U T A C I O N   P A R A   E L   V E C T O R   D E   P O P U L A R I D A D---#
            alpha_binario =[]
            for bit in hijo.ALPHA: 
                if random.uniform(0,1) < pm_binaria:
                    bit = 1 - bit
                    alpha_binario.append(bit)
                else:
                    alpha_binario.append(bit)
            #if len(binario1) == longitud:
            hijo.POPULARIDAD = alpha_binario
            #-----C O N V E R T I R   A L P H A   B I N A R I O   A   R E A L------#
            print(f'parte_real_hijo: {hijo.ALPHA}')
            recuperando_alpha = Binario_A_Real(hijo.ALPHA, longitud)
            hijo.ALPHA = recuperando_alpha
            print(f'Real_recuperado: {recuperando_alpha}')
            binario1 = []
            binario2 = []
            #---M U T A C I O N   P A R A   E L   V E C T O R   D E   P O P U L A R I D A D---#
            for bit in hijo.POPULARIDAD: 
                if random.uniform(0,1) < pm_binaria:
                    bit = 1 - bit
                    binario1.append(bit)
                else:
                    binario1.append(bit)
            hijo.POPULARIDAD = binario1
            #---M U T A C I O N   P A R A   E L   V E C T O R   D E   D I S T A N C I A---#
            for bit in hijo.DISTANCIA: 
                if random.uniform(0,1) < pm_binaria:
                    bit = 1 - bit
                    binario2.append(bit)
                else:
                    binario2.append(bit)
            hijo.DISTANCIA = binario2
            #--( S E   T R A N S F O R M A N   T O D O S   L O S   A L P H A S   D E   B I N A R I O   A   R E A L   E N   L A   P O B L A C I O N   N U E V A )---#
        #--------- CREAR LOS EXPERIMENTOS PARA LOS INVIVIDUOS DE LA NUEVA POBLACION ----------------#
        ALPHA_HIJO, VECTOR_POPULARIDAD_HIJO, VECTOR_DISTANCIA_HIJO = parametros_simulador(poblacion_nueva)
        print(ALPHA_HIJO)
        print(VECTOR_POPULARIDAD_HIJO)
        print(VECTOR_DISTANCIA_HIJO)
        print(poblacion_nueva)
        evaluacion_hijos = generacion_individuos(configuracion, corrida, k, n_individuos, degradacion, ALPHA_HIJO, VECTOR_POPULARIDAD_HIJO, VECTOR_DISTANCIA_HIJO, pool_hilos) 
        print(f'evaluacion_hijos: {evaluacion_hijos}')
        # --------------------- Eliminar la carpeta experimento: ------------------------------------#
        # ----------------------La info se encuentra en la lista de objetos poblacion_inicial--------#
        ruta_actual = os.getcwd()
        ruta_experimento = os.path.abspath((os.path.join(ruta_actual,'..','..',f'Configuracion_{configuracion}',f'Corrida{corrida}',f'Experimento{k}')))
        shutil.rmtree(ruta_experimento)
        #----------- ALMACENAR LAS METRICAS OBTENIDAS CON LOS EXPERIMENTOS EN LA POBLACION NUEVA-----#
        for i in range(n_individuos):                                          
            poblacion_nueva[i].COMUNICACION = evaluacion_hijos[i].R_COMUNICACION
            poblacion_nueva[i].PUNTO_CRITICO = evaluacion_hijos[i].PUNTO_CRITICO
            poblacion_nueva[i].CONECTIVIDAD = evaluacion_hijos[i].R_CONECTIVIDAD
            poblacion_nueva[i].PROMEDIO = evaluacion_hijos[i].PROMEDIO
        #-------- << E T A P A  3 >> : S E L E C C I Ó N     E L I T I S T A  -----------------------#
        poblacion_total = x + poblacion_nueva
        poblacion_total.sort(key=lambda ind: ind.COMUNICACION, reverse=True ) # Ordenarción decreciente
        x = poblacion_total[:n_individuos]
            #----- C O N T I N U A   C O N   L A   S I G U I E N T E   G E N E R A C I O N ----------#
        # ( A Q U I   Y A   S E   A C T U A L I Z Ó   X   Q U E   C O N T I E N E   L O S   I N D I V I D U O S   M Á S   A P T O S ) ----#
        for i in range(n_individuos):
            if  x[i].COMUNICACION > mejores[k][3]:                          # Encuentra el máximo por generación
                mejores[k][0] = x[i].ALPHA
                mejores[k][1] = x[i].POPULARIDAD
                mejores[k][2] = x[i].DISTANCIA
                mejores[k][3] = x[i].COMUNICACION
                mejores[k][4] = x[i].PUNTO_CRITICO
                mejores[k][5] = x[i].CONECTIVIDAD
                mejores[k][6] = x[i].PROMEDIO
            # ------------------ Registramos la siguiente generación y el mejor ----------------------#
        with open(ruta_archivo_csv+'_resultados.csv','a',newline='') as f: # Abrir en modo append
            writer = csv.writer(f)
            writer.writerow([
                k,
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
def pruebas(configuracion, n_corridas, n_generaciones, n_individuos, degradacion, longitud, pool_hilos, n_torneo, n_padres, n_cruza, pc, pm_binaria):
    ruta_actual = os.getcwd()                                 # Obtenemos la ruta actual
    ruta_grafica = os.path.abspath(os.path.join(ruta_actual,'..','..',f'ArchivoConfiguracion_{configuracion}'))
    os.makedirs(ruta_grafica, exist_ok=True)                  # Crear carpeta de resultados
    #------- E J E C U T A R   V A R I A S   C O R R I D A S   D E L   A L G O R I T M O -----#
    aptitudes = []
    plt.figure()
    for j in range(n_corridas):
        individuo_optimo, mejor_por_generaciones = genetico(configuracion, j+1, n_generaciones, n_individuos, longitud, degradacion, pool_hilos, n_torneo, n_padres, n_cruza, pc, pm_binaria)
        aptitudes.append(individuo_optimo[3])
        eje_x = [j for j in range(n_generaciones + 1)]
        eje_y = [k[3] for k in mejor_por_generaciones]
        plt.plot(eje_x, eje_y, label = f'corrida{j+1}')       # Graficar el mejor en cada generacion de la corrida

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
# --------------- < <  P A R A M E T R O S > > ---------------------------------------------------#
n_individuos = 15 #-----------------------> M U L T I P L O   D E L   N U M E R O   D E   H I L O S
pool_hilos = 15   #---------------------------> H I L O S   R E A L E S   D E   L A   M A Q U I N A
longitud = 50
n_corridas = 3
degradacion = 'Ataques'
n_generaciones = 4
n_torneo = 3
n_padres = 2
n_cruza = 2
pc = [0.7]          #----------------------------------> Probablidad de cruza
pm_binaria = [0.4]  #----------------------------------> Probabilidad de mutacion binaria
configuracion = len(pc)*len(pm_binaria)
#--------- Iniciar con el numero de la primer configuracion en caso de que se detenga ------------#
tiempos = []
k = 1 
for p in pc:
        for pb in pm_binaria:
            inicio = time.perf_counter()
            pruebas(k, n_corridas, n_generaciones, n_individuos, degradacion, longitud, pool_hilos, n_torneo, n_padres, n_cruza, pc = p, pm_binaria=pb)
            fin = time.perf_counter()
            duracion = fin - inicio
            minutos = duracion / 60
            tiempos.append({'Configuracion':k,'Corrida':n_corridas, 'Generaciones':n_generaciones, 'Individuos':n_individuos, 'pc':{p},'pm_binario':{pb},'Tiempo_Segundos':duracion, 'Tiempo_minutos':minutos})
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
    for b in [n_corridas]:                             # Obtener las corridas que correponden a cada configuracion
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
for p in pc:
        for pb in pm_binaria:
            df_configuraciones[f'pc={p}\npm_binario={pb}\nCorridas={n_corridas}\nIndividuos={n_individuos}\nGeneraciones={n_generaciones}'] = datos[c]
            c +=1
df_config = df_configuraciones.melt(var_name='Configuracion', value_name='Aptitud')
ax =sns.boxplot(x='Configuracion', y='Aptitud', data=df_config,hue='Configuracion', palette="Set2")
plt.savefig(ruta_cajas, dpi=300, bbox_inches='tight')
