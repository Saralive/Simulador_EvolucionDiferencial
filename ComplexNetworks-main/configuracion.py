#------------- CONFIGURACIÓN DE UNA SERIE DE EXPERIMENTOS DE FORMACIÓN DE REDES -----------------------------------#
#-------------------( A N I L L O )----------------------
NODOS_ANILLO=50                                          # Número de nodos del anillo. Colocar 0 si no se usa anillo
#--------------------( M A L L A )-----------------------
ROWS=8                                                   # Filas de la malla. Colocar 0 si no se usa malla
COLUMNS=8                                                # Columnas de la malla
#----------------( F O R M A C I O N )-------------------
# Estos parámetros se deben definir como lista aunque contengan un solo valor
RED=["malla"]                                            # Tipo de red: "malla", "anillo"
ROUTING=["COMPASS-ROUTING"]                              # Algoritmo de encaminamiento: "COMPASS-ROUTING", "RANDOM-WALK", "SHORTEST-PATH"
REGLAS=[4]                                               # 1,2,3,4
LONG_ENLACES=[1]                                         # Divisor de la longitud de enlace dinámico: 1, 2, 4, 8, 16, 32
#--------------( Parámetros para Node2Vec )--------------
PQ_NODE2VEC = [
    (0.25,0.25), (0.25,0.5), (0.25,1), (0.25,2),
    (0.5,0.25), (0.5,0.5), (0.5,1), (0.5,2),
    (1,0.25), (1,0.5), (1,1), (1,2),
    (2,0.25), (2,0.5), (2,1), (2,2)
    ]
#----------------( E J E C U C I O N )-------------------
CICLOS=5                                                 # Número de ciclos de recableo
EJECUCIONES=2                                            # Número de ejecuciones por experimento   
#-------------------( E X T R A S )----------------------
ENLACES_DINAMICOS=2                                      # Número de enlaces dinámicos por nodo
EXPLORADORES=6                                           # Número de paquetes exploradores por ciclo
# Divisor del máximo número de conexiones permitidas (máximo numero de conexiones permitidas=num_nodos/DIV_CONEXIONES)
DIV_CONEXIONES=1
#-------------- CONFIGURACIÓN DE UNA SERIE DE EXPERIMENTOS DE DEGRADACIÓN DE REDES ----------------------------------#
#--------------( D E G R A D A C I O N )-----------------
SAVE_STEP=4                                              # Cada cuántos ataques registra medidas
#--------------( P A R A L E L I S M O )-----------------# Ajustar según el número de cores de la CPU                                                     
NUM_WORKERS=4                                            # Número de procesos paralelos para ejecutar simulaciones
#-------------- SE AGREGARÁ LA CONFIGURACIÓN DE CADA RED EN EL MÉTODO DE OPTIMIZACIÓN -------------------------------#