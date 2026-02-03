# CONFIGURACIÓN DE UNA SERIE DE EXPERIMENTOS DE FORMACIÓN DE REDES
#---------------------(A N I L L O )---------------------
NODOS_ANILLO=50                                          # Número de nodos del anillo. Colocar 0 si no se usa anillo
#--------------------( M A L L A )-----------------------
ROWS=8                                                   # Filas de la malla. Colocar 0 si no se usa malla
COLUMNS=8                                                # Columnas de la malla
#----------------( F O R M A C I O N )-------------------
# Estos parámetros se deben definir como lista aunque contengan un solo valor
RED=["malla"]                                            # Tipo de red: "malla", "anillo"
ROUTING=["COMPASS-ROUTING"]                              # Algoritmo de encaminamiento: "COMPASS-ROUTING", "RANDOM-WALK", "SHORTEST-PATH"
REGLAS=[4]                                               # 1,2,3
LONG_ENLACES=[1]                                         # Divisor de la longitud de enlace dinámico: 1, 2, 4, 8, 16, 32
#----------------( E J E C U C I O N )--------------------
CICLOS = 15                                               # Número de ciclos de recableo
EJECUCIONES = 10                                          # Número de ejecuciones por experimento   
#-------------------( E X T R A S )-----------------------
ENLACES_DINAMICOS=2                                      # Número de enlaces dinámicos por nodo
EXPLORADORES=10                                          # Número de paquetes exploradores por ciclo
# Divisor del máximo número de conexiones permitidas (máximo numero de conexiones permitidas=num_nodos/DIV_CONEXIONES)
DIV_CONEXIONES=1
#------------------( R E G L A   4 )---------------------
