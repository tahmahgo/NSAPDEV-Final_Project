import socket
import os
import re

def print_usage(command_type=None):
    
    if command_type == "INGEST" or not command_type:
        print("  -> INGEST <file_path> <IP:Port>")
    if command_type == "QUERY" or not command_type:
        print("  -> QUERY <IP:Port> <SEARCH_TYPE> \"<value>\"")
        print("     (Types: SEARCH_DATE, SEARCH_HOST, SEARCH_DAEMON, SEARCH_KEYWORD, COUNT_KEYWORD, SEARCH_SEVERITY)")
    if command_type == "PURGE" or not command_type:
        print("  -> PURGE <IP:Port>")
    print("  -> EXIT\n")

def is_valid_address(address):
    return re.match(r'^[a-zA-Z0-9.-]+:\d+$', address) is not None

def send_payload(target, payload):
    try:
        ip, port = target.split(':')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(30.0) 
            s.connect((ip, int(port)))
            s.sendall(payload.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            
            response = ""
            while True:
                chunk = s.recv(4096).decode('utf-8')
                if not chunk: break
                response += chunk
            return response
    except Exception as e:
        return f"Network Error: {e}"

def main():
    print("--- Mini-Splunk CLI Client ---")
    while True:
        try:
            user_input = input("client> ").strip()
            if not user_input: continue
            if user_input.upper() == "EXIT": break
            if user_input.upper() == "HELP":
                print_usage(); continue
            
            parts = user_input.split(maxsplit=3)
            cmd = parts[0].upper()

            if cmd == "INGEST":
                if len(parts) != 3 or not is_valid_address(parts[2]):
                    print_usage("INGEST"); continue
                if not os.path.exists(parts[1]):
                    print(f"Error: File '{parts[1]}' not found."); continue
                with open(parts[1], 'r') as f:
                    print("[System Message] Sending logs...")
                    print(send_payload(parts[2], f"INGEST|{f.read()}"))

            elif cmd == "QUERY":
                if len(parts) < 4 or not is_valid_address(parts[1]):
                    print_usage("QUERY"); continue
                print("[System Message] Sending query...")
                val = parts[3].strip('"') 
                print(f"[Server Response]\n{send_payload(parts[1], f'QUERY|{parts[2].upper()}|{val}')}")

            elif cmd == "PURGE":
                if len(parts) != 2 or not is_valid_address(parts[1]):
                    print_usage("PURGE"); continue
                print(send_payload(parts[1], "PURGE"))
            else:
                print_usage()

        except KeyboardInterrupt: break
        except Exception as e: print(f"Client Error: {e}")

if __name__ == "__main__":
    main()