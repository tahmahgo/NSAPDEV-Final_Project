import random
import datetime

def generate_test_logs(filename, num_entries=1000):
    hosts = ["SYSSVR1", "DB-HOST-01", "WEB_PROD_A", "GATEWAY-NYC"]
    daemons = ["sshd", "systemd", "kernel", "cron", "apache2"]
    severities = ["INFO", "WARN", "ERROR", "CRITICAL"]
    messages = [
        "User login successful",
        "Failed password for invalid user admin",
        "Disk quota exceeded",
        "Connection reset by peer",
        "Task completed in 45ms",
        "Unexpected packet received"
    ]

    with open(filename, "w") as f:
        for i in range(num_entries):
            # Generate Syslog components
            now = datetime.datetime.now() - datetime.timedelta(seconds=random.randint(0, 86400))
            timestamp = now.strftime("%b %d %H:%M:%S")
            host = random.choice(hosts)
            daemon = random.choice(daemons)
            pid = f"[{random.randint(1, 99999)}]" if random.random() > 0.2 else "" # 20% have no PID
            sev = random.choice(severities)
            msg = random.choice(messages)

            # Format: Feb 22 00:05:38 HOST DAEMON[PID]: SEVERITY: MESSAGE
            line = f"{timestamp} {host} {daemon}{pid}: {sev}: {msg}\n"
            f.write(line)
    
    print(f"Generated {num_entries} log entries in {filename}")

if __name__ == "__main__":
    generate_test_logs("stress_test.log", 5000)