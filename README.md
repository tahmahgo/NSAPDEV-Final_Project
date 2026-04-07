NSAPDEV Mini Splunk 
Final Project Report

Course:
NSAPDEV (Server Application Development)
Term/AY:
2nd Term AY 2025-2026
Project Title:
Concurrent Syslog Analytics Server ("Mini-Splunk")
Team Members:
Elmeranita Estrella, Isha Zulueta

Project Overview & Objectives
The "Mini-Splunk" functions as a powerful log analytics engine which operates simultaneously to process and analyze RFC 3164 syslog data. The system enables several administrators to upload substantial datasets while conducting simultaneous searches throughout a protected central memory database system.

Concurrency & Synchronization Implementation
Process/Thread Model: The server operates according to a Thread-per-Connection architectural design. The main process creates a new threading.Thread every time a socket.accept() operation succeeds. The system permits simultaneous client QUERY operations while processing an ongoing long-running INGEST of huge log files.
Critical Sections & Locking:. The shared resource is the data_store list inside the Indexer class.
Mutex Locks: threading.Lock() is utilized as a binary semaphore.
INGEST/PURGE: The operations create an exclusive lock when they use the with self.lock context manager because this lock prevents all other threads from accessing the list during its modification process.
QUERY: To prevent dirty reads (reads on about-to-be-written data) locking is also obtained by the query engine so it searches only into a completed and stable dataset.
Communication Protocol & Parsing
Socket Protocol: A Pipe-Delimited Protocol is implemented COMMAND|PAYLOAD. 
For example: INGEST|<file_content> or QUERY|SEARCH_HOST|my-server.
Data Ingestion: Large files are handled via a buffered stream. The server reads in 1MB chunks (1024*1024) and accumulates them in a list until the client closes its sending stream via socket.SHUT_WR.
Syslog Parsing Engine: The server uses the following Regex to transform raw text into structured dictionaries:
r'^(\w{3}\s+\d+\s\d+:\d+:\d+)\s+(\S+)\s+([^:\[\s]+)(?:\[(\d+)\])?:\s+(.*)$'
 System User Manual
      5.1 Starting the Server
Command: python server.py
Expected Output: SUCCESS: Indexer is UP and listening on 0.0.0.0:65432
      5.2 Using the CLI Client

Action
Command
Expected Output
Uploading Logs
INGEST C:\Users\ASUS\Desktop\NSAPDEV\NSAPDEV-Final-Project\logs\SVR2_server_auth_syslog.txt 127.0.0.1:65432
--- Mini-Splunk CLI Client ---
client> INGEST C:\Users\ASUS\Desktop\NSAPDEV\NSAPDEV-Final-Project\logs\SVR2_server_auth_syslog.txt 127.0.0.1:65432
[System Message] Sending logs...
SUCCESS: 412266 syslog entries indexed.


Querying by Date
QUERY 127.0.0.1:65432 SEARCH_DATE "Mar  2"
[System Message] Sending query…
[Server Response]

10184. Mar  2 06:38:02 SYSSVR2 sudo: pam_unix(sudo:session): session opened for user root(uid=0) by gcu(uid=1000)
Querying by Host
QUERY 127.0.0.1:65432 SEARCH_HOST SYSSVR2
[System Message] Sending query…
[Server Response]

412266. Mar  2 06:38:02 SYSSVR2 sudo: pam_unix(sudo:session): session opened for user root(uid=0) by gcu(uid=1000)
Querying by Daemon
QUERY 127.0.0.1:65432 SEARCH_DAEMON sshd
[System Message] Sending query…
[Server Response]

304718. Mar  2 06:38:02 SYSSVR2 sshd[945379]: Failed password for invalid user liguo from 206.123.145.52 port 28294 ssh2
Querying by Severity
QUERY 127.0.0.1:65432 SEARCH_SEVERITY ERROR
[System Message] Sending query…
[Server Response]

219. Mar  2 06:35:43 SYSSVR2 sshd[945271]: error: kex_exchange_identification: read: Connection reset by peer
Keyword Search
QUERY 127.0.0.1:65432 SEARCH_KEYWORD Failed Password
[System Message] Sending query…
[Server Response]

64652. Mar  2 06:38:02 SYSSVR2 sshd[945379]: Failed password for invalid user liguo from 206.123.145.52 port 28294 ssh2
Keyword Count
QUERY 127.0.0.1:65432 COUNT_KEYWORD Deactivated
[System Message] Sending query...
[Server Response]
Total count for 'Deactivated': 53315



Erasing Data
PURGE 127.0.0.1:65432
SUCCESS: 412266 entries erased.


 Testing & Performance Evaluation
Concurrency Testing: Testing was performed by initiating a massive INGEST on one terminal while simultaneously running multiple QUERY commands on another. The server console confirmed distinct Thread IDs were active, and the Mutex lock prevented any IndexError or data corruption.
Edge Cases Handled: 
Malformed Logs: Lines not matching the RFC 3164 Regex are skipped gracefully without crashing the thread.
Large Payloads: The system successfully ingested larger lines by utilizing the streaming buffer loop.
Invalid Commands: Clients sending unknown protocols receive an ERROR: Invalid protocol format message, and the specific worker thread is closed safely to free up RAM.
Intellectual Honesty Declaration
We hereby declare that this submitted source code and documentation reflect our group's original work effort and intellectual honesty. The system was built from its foundation through Python's standard libraries which were used to create all required course functions.
The system uses TCP Sockets to handle all network communication without needing any external web frameworks which include Flask Django and FastAPI. The system employs in-memory data structures and custom search logic to handle data indexing and persistence without using any database engines which include MySQL and MongoDB. The complete system required us to implement all Multi-threading and Mutual Exclusion and Socket Programming functions because we needed to show my understanding of concurrent and distributed system concepts. The development team has properly acknowledged all external references and conceptual guides that they used during their work process.



