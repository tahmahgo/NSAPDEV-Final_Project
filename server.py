import socket
import threading
import re

class Indexer:
    def __init__(self):
        self.data_store = []
        # Requirement: Mutex lock to prevent data corruption during concurrent access
        self.lock = threading.Lock() 
        # RFC 3164 Syslog Regex (Timestamp, Host, Daemon, PID, Message)
        self.syslog_re = re.compile(r'^(\w{3}\s+\d+\s\d+:\d+:\d+)\s+(\S+)\s+([^:\[\s]+)(?:\[(\d+)\])?:\s+(.*)$')

    def parse_and_index(self, raw_content):
        entries = []
        lines = raw_content.strip().splitlines()
        for line in lines:
            match = self.syslog_re.match(line)
            if match:
                entries.append({
                    "raw": line,
                    "date": match.group(1),
                    "host": match.group(2),
                    "daemon": match.group(3),
                    "msg": match.group(5)
                })
        with self.lock:
            self.data_store.extend(entries)
            return len(entries)

    def query(self, q_type, q_val):
        with self.lock:
            results = []
            if q_type == "COUNT_KEYWORD":
                count = sum(1 for e in self.data_store if q_val.lower() in e['raw'].lower())
                return f"Total count for '{q_val}': {count}"
            
            for e in self.data_store:
                if q_type == "SEARCH_DATE" and e['date'].startswith(q_val): results.append(e['raw'])
                elif q_type == "SEARCH_HOST" and q_val == e['host']: results.append(e['raw'])
                elif q_type == "SEARCH_DAEMON" and q_val == e['daemon']: results.append(e['raw'])
                elif q_type == "SEARCH_KEYWORD" and q_val.lower() in e['raw'].lower(): results.append(e['raw'])

            return "\n".join(results) if results else "No matches found."

    def purge(self):
        with self.lock:
            count = len(self.data_store)
            self.data_store.clear()
            return f"SUCCESS: {count} entries erased."

idx = Indexer()

def handle_client(conn, addr):
    # Get unique ID for this thread to show concurrency in the console
    thread_id = threading.get_ident()
    try:
        print(f"\n[NEW CONNECTION] Thread {thread_id} started for {addr}")
        
        
        data = conn.recv(1024*1024).decode('utf-8')
        if not data: return
        
        # Input Validation: Ensuring the protocol format is respected
        if "|" not in data and data != "PURGE":
            conn.send(b"ERROR: Invalid protocol format.")
            return

        parts = data.split("|")
        cmd = parts[0]

        if cmd == "INGEST" and len(parts) >= 2:
            count = idx.parse_and_index(parts[1])
            conn.send(f"SUCCESS: {count} syslog entries indexed.".encode())
        elif cmd == "QUERY" and len(parts) >= 3:
            response = idx.query(parts[1], parts[2])
            conn.send(response.encode())
        elif cmd == "PURGE":
            conn.send(idx.purge().encode())
            
        print(f"[FINISHED] Thread {thread_id} has completed the request for {addr}.")

    except Exception as e:
        print(f"[ERROR] Thread {thread_id} encountered: {e}")
        conn.send(f"SERVER ERROR: {str(e)}".encode())
    finally:
        conn.close()

def run_server():
    # TCP Socket Setup
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('0.0.0.0', 65432))
        s.listen(10)
        print("SUCCESS: Indexer is UP and listening on 0.0.0.0:65432")
    
        
        while True:
            c, a = s.accept()
            # Requirement: Spawn a NEW thread for every client connection
            client_thread = threading.Thread(target=handle_client, args=(c, a))
            client_thread.daemon = True
            client_thread.start()
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    run_server()