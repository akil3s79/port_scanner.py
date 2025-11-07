#!/usr/bin/env python3
"""
port_scanner_improved.py
Ejemplo de scanner TCP simple y concurrente con banner grabbing opcional.
Uso: python3 port_scanner_improved.py target --start 1 --end 1024 --timeout 0.8 --workers 200 --banner --output open_ports.txt
"""

import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser(description="Simple TCP port scanner (concurrent).")
    p.add_argument("target", help="Hostname o IP a escanear")
    p.add_argument("--start", type=int, default=1, help="Puerto inicial (default 1)")
    p.add_argument("--end", type=int, default=1024, help="Puerto final inclusive (default 1024)")
    p.add_argument("--timeout", type=float, default=0.8, help="Timeout por intento en segundos (default 0.8)")
    p.add_argument("--workers", type=int, default=200, help="Número máximo de hilos concurrentes (default 200)")
    p.add_argument("--banner", action="store_true", help="Intentar leer banner cuando puerto abierto")
    p.add_argument("--output", help="Fichero para guardar puertos abiertos (append)")
    return p.parse_args()

def scan_port(target_ip, port, timeout, grab_banner=False):
    """Intenta conectar al puerto. Devuelve (port, is_open, banner_or_none, err_or_none)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        res = s.connect_ex((target_ip, port))
        if res == 0:
            banner = None
            if grab_banner:
                try:
                    s.settimeout(0.7)
                    # Intentar recibir algo; puede fracasar si el servicio no envía nada
                    banner = s.recv(1024)
                    if banner:
                        try:
                            banner = banner.decode('utf-8', errors='replace').strip()
                        except Exception:
                            banner = repr(banner)
                except socket.timeout:
                    banner = None
                except Exception:
                    banner = None
            s.close()
            return (port, True, banner, None)
        else:
            s.close()
            return (port, False, None, None)
    except Exception as e:
        try:
            s.close()
        except Exception:
            pass
        return (port, False, None, str(e))

def main():
    args = parse_args()

    try:
        target_ip = socket.gethostbyname(args.target)
    except socket.gaierror:
        print(f"ERROR: No se puede resolver host {args.target}")
        sys.exit(1)

    start_port = max(1, args.start)
    end_port = min(65535, args.end)
    if start_port > end_port:
        print("ERROR: rango de puertos inválido.")
        sys.exit(1)

    ports = range(start_port, end_port + 1)
    open_ports = []

    print("")
    print(f"Buscando puertos en: {args.target} ({target_ip})")
    print(f"Rango: {start_port}-{end_port}  Timeout: {args.timeout}s  Workers: {args.workers}  Banner: {args.banner}")
    print("")

    t0 = datetime.now()
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as exe:
            future_to_port = {exe.submit(scan_port, target_ip, p, args.timeout, args.banner): p for p in ports}
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    p, is_open, banner, err = future.result()
                    if is_open:
                        open_ports.append((p, banner))
                        if banner:
                            print(f"[+] {p} abierto - Banner: {banner}")
                        else:
                            print(f"[+] {p} abierto")
                except KeyboardInterrupt:
                    print("\nInterrumpido por el usuario")
                    exe.shutdown(wait=False)
                    sys.exit(1)
                except Exception as e:
                    # No mostrar un error por cada puerto para no saturar la salida
                    pass
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
        sys.exit(1)

    t1 = datetime.now()
    delta = t1 - t0
    print("")
    print(f"Escaneo completado en {delta}. Puertos abiertos: {len(open_ports)}")
    if args.output and open_ports:
        try:
            with open(args.output, "a") as f:
                for p, banner in open_ports:
                    line = f"{target_ip}:{p}"
                    if banner:
                        line += f" - {banner}"
                    f.write(line + "\n")
            print(f"Guardado en {args.output}")
        except Exception as e:
            print(f"Error al escribir fichero: {e}")

if __name__ == "__main__":
    main()
