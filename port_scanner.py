#!/bin/python3

import sys
import socket
from datetime import datetime


if len(sys.argv) == 2:
    target = socket.gethostbyname(sys.argv[1]) 
else:
    print("Cantidad de argumentos invalida")
    print("Ejemplo: python3 port_scanner.py")


print("")
print(chr(27)+"[1;33m"+"Buscando puertos en: "+target)
print("")

try:
    for port in range(1,65535):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(1)
        result = s.connect_ex((target,port)) 
        if result == 0:
            print("El puerto {} está abierto".format(port))
        s.close()

except KeyboardInterrupt:
    print("\nSaliendo.")
    sys.exit()
    
except socket.gaierror:
    print("No se puede resolver el hostname")
    sys.exit()

except socket.error:
    print("No se puede conectar con el servidor")
    sys.exit()
