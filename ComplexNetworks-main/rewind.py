import os
import subprocess
from individuo import Individuo, IndividuoAlgoritmo
import shutil

############## F U N C I O N   Q U E   E J E C U T A   C A D A   E X P E R I M E N T O  #################
#  S E   P A R A L E L I Z A    C O N   H I L O S   L A   E J E C U C I O N   D E L   S I M U L A D O R #
def ejecutar_experimento(i, ruta_experimento, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA):        
    ruta_individuo = os.path.join(ruta_experimento,f'Individuo{i}')       # Ruta completa de cada carpeta
    os.makedirs(ruta_individuo, exist_ok=True)                            # Creación de carpeta Individuo

    #-------(4) CREAR UN OBJETO DE INDIVIDUO PARA CADA RED ---------------------------------------------#
    regla = Individuo(ruta_individuo,                         
                    ALPHA = ALPHA[i-1],
                    VECTOR_POPULARIDAD = VECTOR_POPULARIDAD[i-1],
                    VECTOR_DISTANCIA = VECTOR_DISTANCIA[i-1],
                    DEGRADACION = degradacion)  
    
    #-------(5) COPIAR SIMULADOR PARA EL INDIVIDUO -----------------------------------------------------#
    subprocess.run(['python', os.path.join(ruta_actual,'0creaCopiaSimulador.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])

    #-------(6) AGREGAR PARAMETROS EN ARCHIVO DE CONFIGURACION -----------------------------------------#
    ruta_configFormacion = os.path.join(regla.INDIVIDUO_DIR,'configFormacion.py')
    with open(ruta_configFormacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nALPHA = {regla.ALPHA}')
        f.write(f'\nVECTOR_POPULARIDAD = {regla.VECTOR_POPULARIDAD}')
        f.write(f'\nVECTOR_DISTANCIA = {regla.VECTOR_DISTANCIA}')

    #-------(7) AGREGAR TIPO DE DEGRADACION EN ARCHIVO DE CONFIGURACION --------------------------------#
    ruta_configDegradacion = os.path.join(regla.INDIVIDUO_DIR,'configDegradacion.py')
    with open(ruta_configDegradacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nTIPO_DEGRADACION=["{degradacion}"]')

    #-------(8) EXPERIMENTOS DE FORMACION DE REDES -----------------------------------------------------#
    ruta_formacion = os.path.join(regla.INDIVIDUO_DIR,'formacion.py')
    subprocess.run(['python',ruta_formacion,
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)],
                    cwd = regla.FORMACION_DIR)
    
    subprocess.run(['python', os.path.join(ruta_actual,'1creaPromediosFormacion.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    #-------(9) EXPERIMENTOS DE DEGRADACION DE REDES ---------------------------------------------------#
    ruta_degradacion = os.path.join(regla.INDIVIDUO_DIR,'degradacion.py')
    subprocess.run(['python', ruta_degradacion,
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    
    subprocess.run(['python', os.path.join(ruta_actual,'6creaPromediosDegradacion.py'),
                    str(regla.INDIVIDUO_DIR),str(regla.FORMACION_DIR), str(regla.DEGRADACION_DIR)])
    #--------------------( A Q U I   T E R M I N A   E L   E X P E R I M E N T O )----------------------#

    #--------(10) APTITUD DEL INDIVIDUO ----------------------------------------------------------------#
    regla.robustez()                                                   # Calcula la resistencia de la red
    return regla , i                                                   # Objeto y el id del individuo
