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
import time
import shutil
import random
import copy
from concurrent.futures import ThreadPoolExecutor
import generar_redes
import configGenetico
#############################################################################################################
#      F U N C I O N E S   P A R A   C O N S T R U I R   E L   A L G O R I T M O   G E N E R T I C O        #
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
    individuos = [None]*n_individuos                          # Lista de individuos
    #-----------(4) CREAR UN POOL DE HILOS -----------------------------------------------------------------#
    with ThreadPoolExecutor(max_workers=pool_hilos) as executor:
        equipos = []
        for i in range(1, n_individuos + 1):
            #---(5) MAPEO DE LAS TAREAS DE FORMA DINAMICA ---------------------------------------#
            f = executor.submit(
                generar_redes.ejecutar_experimento, 
                i, ruta_experimento, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA)
            equipos.append(f)
        #-------(6) LANZAR LOS EQUIPOS DE HILOS -------------------------------------------------#
        for f in equipos:
            regla, id_individuo = f.result()
            if regla is None:                                               # Si el hilo falló (retornó None)
                print(f"Alerta: Guardando 'None' en el índice {id_individuo-1} debido al fallo anterior.")
            individuos[id_individuo - 1] = regla                          
            
    return individuos
#---------------------------------------------#
configuracion=1
corrida=1
experimento=0
n_individuos=1
degradacion='Ataques'
ALPHA=[0.5]
VECTOR_POPULARIDAD=[[0,1,0,1,0,1,0,1,0,1]]
VECTOR_DISTANCIA=[[0,1,0,1,0,1,0,1,0,1]]
pool_hilos=2
#---------------------------------------------#
ruta_actual = os.getcwd()                                 # Obtenemos la ruta actual
ruta_grafica = os.path.abspath(os.path.join(ruta_actual,'..','..',f'ArchivoConfiguracion_{configuracion}'))
os.makedirs(ruta_grafica, exist_ok=True)                  # Crear carpeta de resultados
lista = generacion_individuos(configuracion,corrida, experimento, n_individuos, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA, pool_hilos)
print(f'individuos:{lista}')