#Configuración de una serie de experimentos de formación y degradación
from pathlib import Path

#--------- Directorios para guardar resultados -----------
home_path = Path.home()
BASE_DIR = str(home_path) + "/Documents/POSGRADO/UEAS/TRIM_3/Proyecto/"

RESULTADOS_DIR = BASE_DIR + "Formacion"
DEGRADACION_DIR = BASE_DIR + "Degradacion"