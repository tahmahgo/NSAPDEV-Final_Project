import socket
import os
import re

def print_usage(command_type=None):
    """
    Prints the correct syntax if the user types a command incorrectly.
    This fulfills the requirement to guide the user on correct usage.
    """
    print("\n[!] INVALID FORMAT. Correct usage:")
    if command_type == "INGEST" or not command_type:
        print("  -> INGEST <file_path> <IP:Port>")
    if command_type == "QUERY" or not command_type:
        print("  -> QUERY <IP:Port> <SEARCH_TYPE> \"<value>\"")
        print("     (Types: SEARCH_DATE, SEARCH_HOST, SEARCH_DAEMON, SEARCH_KEYWORD, COUNT_KEYWORD)")
    if command_type == "PURGE" or not command_type:
        print("  -> PURGE <IP:Port>")
    print("  -> EXIT\n")

def is_valid_address(address):
    """Checks if the address is in the format IP:PORT or Hostname:PORT."""
    return re.match(r'^[a-zA-Z0-9.-]+:\d+$', address) is not None

def send_payload(target, payload):
    """
    Handles the network connection to the server.
    Includes a timeout to prevent the client from hanging if the server is down.
    """
    try:
        ip, port = target.split(':')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10.0) # 10-second timeout for stability
            s.connect((ip, int(port)))
            s.sendall(payload.encode('utf-8'))
            
            # Receive response in chunks to handle large log results
            response = ""
            while True:
                chunk = s.recv(4096).decode('utf-8')
                if not chunk: break
                response += chunk
            return response
    except socket.timeout:
        return "Error: Connection timed out. The server might be busy."
    except ConnectionRefusedError:
        return "Error: Could not connect to server. Is the Indexer running?"
    except Exception as e:
        return f"Network Error: {e}"

def main():
    print("--- Mini-Splunk CLI Client ---")
    print("Type 'HELP' to see commands or 'EXIT' to quit.")
    
    while True:
        try:
            user_input = input("client> ").strip()
            if not user_input: continue
            if user_input.upper() == "EXIT": break
            if user_input.upper() == "HELP":
                print_usage()
                continue
            
            # Split into max 4 parts: CMD, ADDR, TYPE, VALUE
            parts = user_input.split(maxsplit=3)
            cmd = parts[0].upper()

            # --- INGEST COMMAND ---
            if cmd == "INGEST":
                if len(parts) != 3 or not is_valid_address(parts[2]):
                    print_usage("INGEST")
                    continue
                
                file_path = parts[1]
                if not os.path.exists(file_path):
                    print(f"Error: File '{file_path}' not found. Check the directory path.")
                    continue
                
                with open(file_path, 'r') as f:
                    # Packaging data using the pipe '|' delimiter for the server
                    print(send_payload(parts[2], f"INGEST|{f.read()}"))

            # --- QUERY COMMAND ---
            elif cmd == "QUERY":
                if len(parts) < 4 or not is_valid_address(parts[1]):
                    print_usage("QUERY")
                    continue
                
                target = parts[1]
                search_type = parts[2].upper()
                # strip() removes the quotes if the user typed "Feb 23"
                val = parts[3].strip('"') 
                
                print(send_payload(target, f"QUERY|{search_type}|{val}"))

            # --- PURGE COMMAND ---
            elif cmd == "PURGE":
                if len(parts) != 2 or not is_valid_address(parts[1]):
                    print_usage("PURGE")
                    continue
                print(send_payload(parts[1], "PURGE"))

            else:
                print(f"Unknown command: {cmd}")
                print_usage()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Client Error: {e}")

if __name__ == "__main__":
    main()