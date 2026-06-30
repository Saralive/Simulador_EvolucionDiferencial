# CONFIGURACIÓN DE LOS PARÁMETROS DEL ALGORITMO GENÉTICO
#--------------( E V O L U C I Ó N   D I F E R E N C I A L )----------------#
N_CORRIDAS=1          # Número de veces que se ejecuta el genético
N_GENERACIONES=0
N_INDIVIDUOS=6        # El número de individuos debe ser par
F = [0.2, 0.4]        # valor entre 0 y 1
CR = [0.5]            # Probabilidad de cruza binomial: valor entre 0 y 1 
#---------------------( R E G L A   4 )-------------------------------------#
LONGITUD=10                           # Longitud de los vectores de selección
#-----------------( D E G R A D A C I Ó N )---------------------------------#
DEGRADACION='Ataques'                  # Tipo de degradación 'Ataques' o 'Fallas'
#---------------------------------------------------------------------------#
POOL_HILOS=1
