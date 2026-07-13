#----------CONFIGURACIÓN DE LOS PARÁMETROS DEL ALGORITMO GENÉTICO-----------#
#---------------------( G E N É T I C O )-----------------------------------#
N_CORRIDAS=5          # Número de veces que se ejecuta el genético
N_GENERACIONES=20
N_INDIVIDUOS=24       # El número de individuos debe ser par
N_TORNEO=3            # Número de individuos seleccionados a torneo
N_PADRES=2            # Número de padres 
N_CRUZA=2             # Número de puntos de cruza
PROB_CRUZA=[0.4] # Probabilidad de cruza binomial: valor entre 0 y 1
PROB_MUT=[0.03]       # Probabilidad de mutación binaria : valor entre 0 y 1
#---------------------( R E G L A   4 )-------------------------------------#
LONGITUD=50                           # Longitud de los vectores de selección
#-----------------( D E G R A D A C I Ó N )---------------------------------#
DEGRADACION='Ataques'              # Tipo de degradación 'Ataques' o 'Fallas'
