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
        # Create socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set options to help with firewall/redirection issues
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            s.settimeout(15.0) 
            s.connect((ip, int(port)))
            
            # Send the entire payload
            s.sendall(payload.encode('utf-8'))
            
            # Signal to the server we are done sending data
            s.shutdown(socket.SHUT_WR)
            
            # Read the response in chunks
            response = ""
            while True:
                chunk = s.recv(4096).decode('utf-8')
                if not chunk:
                    break
                response += chunk
            return response
            
    except ConnectionResetError:
        return "Network Error: [WinError 10054] Connection Reset. This usually means the Proxmox Host rejected the data packet or the Redirection rule is misconfigured."
    except Exception as e:
        return f"Network Error: {e}"

def main():
    print("--- Mini-Splunk CLI Client ---")
    print("Type HELP for command list.")
    
    while True:
        try:
            user_input = input("client> ").strip()
            if not user_input:
                continue
            if user_input.upper() == "EXIT":
                break
            if user_input.upper() == "HELP":
                print_usage()
                continue
            
            # Split into parts to identify the command
            parts = user_input.split()
            cmd = parts[0].upper()

            if cmd == "INGEST":
                # Usage: INGEST <file_path> <IP:Port>
                if len(parts) < 3:
                    print_usage("INGEST")
                    continue
                
                # Handling file paths that might contain spaces
                target = parts[-1]
                file_path = " ".join(parts[1:-1])
                
                if not is_valid_address(target):
                    print(f"Error: '{target}' is not a valid IP:Port format.")
                    continue
                if not os.path.exists(file_path):
                    print(f"Error: File '{file_path}' not found.")
                    continue
                
                with open(file_path, 'r') as f:
                    print(f"[System Message] Sending logs to {target}...")
                    content = f.read()
                    print(send_payload(target, f"INGEST|{content}"))

            elif cmd == "QUERY":
                # Usage: QUERY <IP:Port> <TYPE> <VALUE>
                if len(parts) < 4:
                    print_usage("QUERY")
                    continue
                
                target = parts[1]
                search_type = parts[2].upper()
                # Join the rest in case the search value has spaces
                val = " ".join(parts[3:]).strip('"')
                
                if not is_valid_address(target):
                    print(f"Error: '{target}' is not a valid IP:Port format.")
                    continue
                
                print(f"[System Message] Querying {target}...")
                response = send_payload(target, f"QUERY|{search_type}|{val}")
                print(f"\n[Server Response]\n{response}")

            elif cmd == "PURGE":
                # Usage: PURGE <IP:Port>
                if len(parts) != 2 or not is_valid_address(parts[1]):
                    print_usage("PURGE")
                    continue
                
                target = parts[1]
                print(f"[System Message] Purging {target}...")
                print(send_payload(target, "PURGE"))
            
            else:
                print("Unknown command.")
                print_usage()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Client Error: {e}")

if __name__ == "__main__":
    main()