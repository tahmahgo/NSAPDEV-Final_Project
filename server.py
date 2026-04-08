import socket
import threading
import re
import time

class Indexer:
    def __init__(self):
        self.data_store = []
        self.lock = threading.Lock() 
        # Updated Regex to better capture the message body for severity filtering
        self.syslog_re = re.compile(r'^(\w{3}\s+\d+\s\d+:\d+:\d+)\s+(\S+)\s+([^:\[\s]+)(?:\[(\d+)\])?:\s+(.*)$')

    def parse_and_index(self, raw_content):
        entries = []
        lines = raw_content.strip().splitlines()
        for line in lines:
            match = self.syslog_re.match(line)
            if match:
                msg_content = match.group(5)
                # Determine severity by looking for keywords in the message
                severity = "INFO" # Default
                if "ERROR" in msg_content.upper() or "CRITICAL" in msg_content.upper():
                    severity = "ERROR"
                elif "WARN" in msg_content.upper():
                    severity = "WARN"
                
                entries.append({
                    "raw": line,
                    "date": match.group(1),
                    "host": match.group(2),
                    "daemon": match.group(3),
                    "severity": severity,
                    "msg": msg_content
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
                # NEW: Severity Filtering
                elif q_type == "SEARCH_SEVERITY" and q_val.upper() == e['severity']: results.append(e['raw'])

            if not results:
                return "No matches found."
            
            header = f"Found {len(results)} matching entries for '{q_val}':\n"
            return header + "\n".join([f"{i+1}. {line}" for i, line in enumerate(results)])

    def purge(self):
        with self.lock:
            count = len(self.data_store)
            self.data_store.clear()
            return f"SUCCESS: {count} entries erased."

idx = Indexer()

def handle_client(conn, addr):
    thread_id = threading.get_ident()
    try:
        print(f"\n[NEW CONNECTION] Thread {thread_id} for {addr}")
        
        received_chunks = []
        while True:
            chunk = conn.recv(1024*1024)
            if not chunk: break
            received_chunks.append(chunk.decode('utf-8'))
        
        full_data = "".join(received_chunks)
        if not full_data: return

        parts = full_data.split("|", 1)
        cmd = parts[0]

        if cmd == "INGEST" and len(parts) >= 2:
            count = idx.parse_and_index(parts[1])
            conn.send(f"SUCCESS: {count} syslog entries indexed.".encode())
        elif cmd == "QUERY":
            query_parts = parts[1].split("|")
            if len(query_parts) >= 2:
                response = idx.query(query_parts[0], query_parts[1])
                conn.send(response.encode())
        elif cmd == "PURGE":
            conn.send(idx.purge().encode())
            
    except Exception as e:
        print(f"[ERROR] Thread {thread_id}: {e}")
    finally:
        conn.close()

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 65432))
    s.listen(10)
    print("SUCCESS: Indexer is UP and listening on 0.0.0.0:8080")
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()

if __name__ == "__main__":
    run_server()
