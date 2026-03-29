import subprocess
import os
import sys
import re

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr.strip()}"

def find_odoo_bin():
    possible_paths = [
        "/opt/odoo/odoo-server/odoo-bin",
        "/usr/bin/odoo",
        "/usr/local/bin/odoo-bin"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # Try finding it
    res = run_cmd("find / -type f -name odoo-bin 2>/dev/null | head -n 1")
    return res if res and "ERROR" not in res else None

def get_odoo_config():
    # Detect from systemd
    res = run_cmd("systemctl cat odoo 2>/dev/null | grep -oP 'ExecStart=.*(?:-c|--config)\\s+\\K[^\\s]+' | tr -d '\"'")
    if res and "ERROR" not in res:
        return res
    # Fallback paths
    fallback = ["/etc/odoo/odoo.conf", "/etc/odoo.conf"]
    for f in fallback:
        if os.path.exists(f):
            return f
    return None

def get_databases():
    res = run_cmd("sudo -u postgres psql -t -c \"SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres';\"")
    if "ERROR" in res:
        return []
    return [d.strip() for d in res.split("\n") if d.strip()]

def check_logic():
    print("--- [Odoo Health Check & Logic Repair] ---")
    
    # 1. Path Detection
    bin_path = find_odoo_bin()
    conf_path = get_odoo_config()
    print(f"[*] Odoo Binary: {bin_path or 'NOT FOUND'}")
    print(f"[*] Odoo Config: {conf_path or 'NOT FOUND'}")
    
    if not bin_path or not conf_path:
        print("[!] CRITICAL: Could not detect Odoo paths. Run as root.")
        return

    # 2. Git Check
    if os.path.exists(".git"):
        print("[*] Git Repository detected. Pulling changes...")
        print(run_cmd("git pull origin master"))
    
    # 3. Database Integrity (Logic Fixes)
    dbs = get_databases()
    print(f"[*] Found Databases: {', '.join(dbs)}")
    
    for db in dbs:
        print(f"\n[+] Processing Database: {db}")
        # Logic Fix 1: Orphaned Teacher IDs
        print(f"    - Fixing orphaned teacher_id logic...")
        sql = "UPDATE rehab_class SET teacher_id = NULL WHERE teacher_id IS NOT NULL AND teacher_id NOT IN (SELECT id FROM rehab_staff);"
        run_cmd(f"sudo -u postgres psql -d {db} -c \"{sql}\"")
        
        # Logic Fix 2: Force Module Registry Update
        print(f"    - Upgrading rehab_management registry...")
        upgrade_cmd = f"sudo su - odoo -s /bin/bash -c \"{bin_path} -c {conf_path} -d {db} -u rehab_management --stop-after-init\""
        res = run_cmd(upgrade_cmd)
        if "ERROR" in res:
            print(f"    [!] Upgrade Failed: {res}")
        else:
            print(f"    [OK] Module logic synchronized.")

    # 4. Final Restart
    print("\n[*] Restarting Odoo Service...")
    run_cmd("sudo systemctl restart odoo")
    print("\n--- ALL TASKS COMPLETE. SYSTEM IS ONLINE ---")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script as root (sudo).")
        sys.exit(1)
    check_logic()
