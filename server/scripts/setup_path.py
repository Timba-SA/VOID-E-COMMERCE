"""
Helper para agregar el directorio server al sys.path.
Importar este módulo al inicio de cada script en scripts/.
"""
import sys
from pathlib import Path

# Agregar el directorio server al path
server_dir = Path(__file__).parent.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))
