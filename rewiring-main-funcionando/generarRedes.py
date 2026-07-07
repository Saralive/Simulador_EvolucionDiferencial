import os
import subprocess
from individuo import Individuo, IndividuoAlgoritmo
import shutil
############## F U N C I O N   Q U E   E J E C U T A   C A D A   E X P E R I M E N T O  #################
#  S E   P A R A L E L I Z A    C O N   H I L O S   L A   E J E C U C I O N   D E L   S I M U L A D O R #
def ejecutar_experimento(n_individuos, ruta_experimento, ruta_actual, degradacion, ALPHA, VECTOR_POPULARIDAD, VECTOR_DISTANCIA):
    individuos = [None]*n_individuos                                   # Lista que almacenará los individuos
    #-------(1) CREAR UN OBJETO DE INDIVIDUO PARA CADA RED -------------------------------------------------#
    for i in range(1, n_individuos + 1):
        regla = Individuo(i, ruta_experimento,                         
                        ALPHA = ALPHA[i-1],
                        VECTOR_POPULARIDAD = VECTOR_POPULARIDAD[i-1],
                        VECTOR_DISTANCIA = VECTOR_DISTANCIA[i-1],
                        DEGRADACION = degradacion)  
        print(f'Individuo_dir : {regla.INDIVIDUO_DIR}')
        print(f'Formacion_dir : {regla.FORMACION_DIR}')
        print(f'Degradacion_dir : {regla.DEGRADACION_DIR}')
        individuos[i-1]=regla

    #-------(2) COPIAR SIMULADOR PARA EL EXPERIMENTO -----------------------------------------------------#
    ruta_Formacion = os.path.join(ruta_experimento,'Formacion')
    ruta_Degradacion =os.path.join(ruta_experimento,'Degradacion')
    subprocess.run(['python', os.path.join(ruta_actual,'0creaCopiaSimulador.py'),
                    str(ruta_experimento),str(ruta_Formacion), str(ruta_Degradacion)])

    #-------(3) AGREGAR PARAMETROS PARA TODOS LOS INDIVIDUOS EN EL ARCHIVO DE CONFIGURACION-------------#
    j = 1
    ruta_configFormacion = os.path.join(ruta_experimento,'configuracion.py')
    with open(ruta_configFormacion, 'a', encoding = 'utf-8') as f:
        f.write(f'\nTIPO_DEGRADACION=["{degradacion}"]')
        for regla in individuos:
            f.write(f'\nALPHA_{j} = {regla.ALPHA}')
            f.write(f'\nVECTOR_POPULARIDAD_{j} = {regla.VECTOR_POPULARIDAD}')
            f.write(f'\nVECTOR_DISTANCIA_{j} = {regla.VECTOR_DISTANCIA}')
            j += 1

    #-------(8) EXPERIMENTOS DE FORMACION DE REDES -----------------------------------------------------#
    ruta_formacion_py= os.path.join(ruta_experimento,'formacion.py')
    subprocess.run(['python',ruta_formacion_py,
                    str(ruta_experimento),str(ruta_Formacion), str(ruta_Degradacion)],
                    cwd = ruta_Formacion)
    
    subprocess.run(['python', os.path.join(ruta_actual,'1creaPromediosFormacion.py'),
                    str(ruta_experimento),str(ruta_Formacion), str(ruta_Degradacion)])
    
    #-------(9) EXPERIMENTOS DE DEGRADACION DE REDES ---------------------------------------------------#
    ruta_degradacion_py = os.path.join(ruta_experimento,'degradacion.py')
    subprocess.run(['python', ruta_degradacion_py,
                    str(ruta_experimento),str(ruta_Formacion), str(ruta_Degradacion)])
    
    subprocess.run(['python', os.path.join(ruta_actual,'6creaPromediosDegradacion.py'),
                    str(ruta_experimento),str(ruta_Formacion), str(ruta_Degradacion)])
    #--------------------( A Q U I   T E R M I N A   E L   E X P E R I M E N T O )----------------------#

    #--------(10) APTITUD DEL INDIVIDUO ----------------------------------------------------------------#
    for i in range(n_individuos):
        individuos[i].robustez()                                       # Calcula la resistencia de la red
    return individuos                                                  # Objeto y el id del individuo