import os
import pandas as pd
from pathlib import Path
import configFormacion_opt
import configDegradacion_opt

######################################################################################################
#        L O S   I N D I V I D U O S   E N   E S T E   E X P E R I M E N T O   S O N   L A S         #
#    R E D E S  G E N E R A D A S   Y   S U   A P T I T U D   E S   S U   R E S I S T E N C I A      #
######################################################################################################

class Individuo:
    def __init__(self,individuo_dir,ALPHA,VECTOR_POPULARIDAD,VECTOR_DISTANCIA,DEGRADACION,
                 R1 = 0, R2 = 0, R3 = 0, R4 = 0): #LISTAS O DICC PARA VARIOS ALG.ENCAMIN/TAM_ENLACES/DEGRACION
        #################################### R U T A S ###############################################
        self.INDIVIDUO_DIR = Path(individuo_dir)
        self.FORMACION_DIR = os.path.join(Path(individuo_dir),'Formacion')
        self.DEGRADACION_DIR = os.path.join(Path(individuo_dir)/'Degradacion')
        ############ P A R A M E T R O S   D E L   A L G O R I T M O   E V O L U T I V O #############
        #------------------------------------ R E G L A  4 ------------------------------------------#
        self.ALPHA = ALPHA                                                   # 0 < = alfa < = 1
        self.VECTOR_POPULARIDAD = VECTOR_POPULARIDAD                         # Ambos vectores deben
        self.VECTOR_DISTANCIA   = VECTOR_DISTANCIA                           # tener la misma longitud
        self.DEGRADACION = DEGRADACION                                       # Tipo de degradacion
        ######################### A P T I T U D   D E L   I N D I V I D U O  #########################
        self.R_CONECTIVIDAD = R1
        self.PUNTO_CRITICO = R2
        self.R_COMUNICACION = R3
        self.PROMEDIO = R4

    ####### < P U N T O   C R Í T I C O  Y  R O B U S T E Z   D E   C O N E C T I V I D A D > ########
    def robustez(self):#(self, DEGRADACION)
        #---------(1) RUTAS DE LAS CARPETAS DE ATAQUES Y FALLAS -------------------------------------#
        if self.DEGRADACION == 'Ataques':
            RUTA_DEGRADACION = os.path.join(self.DEGRADACION_DIR,'Ataques')
        elif self.DEGRADACION == 'Fallas':
            RUTA_DEGRADACION = os.path.join(self.DEGRADACION_DIR,'Fallas')
        #---------(2) ABRE TODOS LOS ARCHIVOS datos-promedio.csv y attr-promedio.csv ----------------#
        for regla in configFormacion_opt.REGLAS:
            for red in configFormacion_opt.RED:
                if red == "anillo":
                    nombre_red = "anillo" + str(configFormacion_opt.NODOS_ANILLO)
                elif red == "malla":
                    nombre_red = f"malla{configFormacion_opt.ROWS}x{configFormacion_opt.COLUMNS}"
                else:
                    print(f" Tipo de red desconocido, saltando: {red}")
                    continue
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
                        # Obtener las rutas de los archivos csv de la carpeta de degradacion
                        RUTA_CSV = os.path.join(RUTA_DEGRADACION,nombre_red,f'R{regla}',routing,f'D{long_enlace}','datos-promedio.csv')
                        RUTA_ATTR_CSV = os.path.join(RUTA_DEGRADACION,nombre_red,f'R{regla}',routing,f'D{long_enlace}','attr-promedio.csv')
                        data = pd.read_csv(RUTA_CSV)                  # Cargar los datos en una tabla de pandas
                        #['avg_clustering','aslp','avg_diameter','rolcc','avg_assot'] # Nombres de las columnas
                        data_NLCC = data['rolcc']
                        tam_grafo = configFormacion_opt.ROWS*configFormacion_opt.COLUMNS
                        SAVE_STEP = configDegradacion_opt.SAVE_STEP
                        #---------------------(3) CALCULO DEL PUNTO CRITICO EN LA FUNCION ------------------------------#
                        valor_critico, indice_critico, fraccion_critica = punto_critico(data_NLCC, SAVE_STEP, tam_grafo)
                        self.PUNTO_CRITICO = fraccion_critica
                        #---------------------(4) CALCULO DE LA ROBUSTEZ DE CONECTIVIDAD--------------------------------#
                        self.R_CONECTIVIDAD = R_conectividad(data_NLCC)
                        #----------------------(5) ATTR YA CALCULADO EN LA SIMULACION ----------------------------------#
                        data_attr = pd.read_csv(RUTA_ATTR_CSV, header = None, index_col = 0)
                        self.R_COMUNICACION = data_attr.loc['AVG_MUA2TR'].values[0]
                        #----------------------(6) PROMEDIO ------------------------------------------------------------#
                        self.PROMEDIO = (self.PUNTO_CRITICO + self.R_CONECTIVIDAD + self.R_COMUNICACION)/3

#-- F U N C I O N E S  -  C Á L C U L O   D E   R O B U S T E Z   D E   L A   R E D--#
def punto_critico(data, SAVE_STEP, tam_grafo):
        porcentaje_registrado = SAVE_STEP/tam_grafo
        for indice, valor in enumerate(data):
            if valor < 0.5:
                valor_critico = valor
                indice_critico = indice
                fraccion_critica = round(porcentaje_registrado*indice_critico,4)
                break
        return valor_critico, indice_critico, fraccion_critica

def R_conectividad(data):
    suma = sum(data)
    divisor = len(data)+1
    return round(suma/divisor,2)