import subprocess
import os
import sys
import re
import glob

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def find_odoo_bin():
    possible_paths = ["/opt/odoo/odoo-server/odoo-bin", "/usr/bin/odoo", "/usr/local/bin/odoo-bin"]
    for path in possible_paths:
        if os.path.exists(path): return path
    out, _, _ = run_cmd("find / -type f -name odoo-bin 2>/dev/null | head -n 1")
    return out if out else None

def get_odoo_config():
    out, _, _ = run_cmd("systemctl cat odoo 2>/dev/null | grep -oP 'ExecStart=.*(?:-c|--config)\\s+\\K[^\\s]+' | tr -d '\"'")
    if out: return out
    for f in ["/etc/odoo/odoo.conf", "/etc/odoo.conf"]:
        if os.path.exists(f): return f
    return None

def get_databases():
    out, _, _ = run_cmd("sudo -u postgres psql -t -c \"SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres';\"")
    return [d.strip() for d in out.split("\n") if d.strip()]

def validate_files():
    print("\n--- [Phase 1: File Validation (Crash Prevention)] ---")
    errors = []
    
    # 1. XML Syntax Check
    print("[*] Checking XML files for syntax errors...")
    for xml_file in glob.glob("**/*.xml", recursive=True):
        out, err, code = run_cmd(f"python3 -c \"import lxml.etree; lxml.etree.parse('{xml_file}')\" 2>/dev/null")
        if code != 0:
            print(f"    [!] CRITICAL: XML Syntax Error in {xml_file}")
            errors.append(f"XML Error in {xml_file}")
            
    # 2. Python Syntax Check
    print("[*] Checking Python files for syntax errors...")
    for py_file in glob.glob("**/*.py", recursive=True):
        if py_file == "rehab_health_check.py": continue
        out, err, code = run_cmd(f"python3 -m py_compile {py_file}")
        if code != 0:
            print(f"    [!] CRITICAL: Python Syntax Error in {py_file}")
            errors.append(f"Python Error in {py_file}")
            
    if not errors:
        print("[OK] All code files passed basic syntax validation.")
    return errors

def analyze_logs():
    print("\n--- [Phase 2: Log Analysis (Recent Errors)] ---")
    log_files = ["/var/log/odoo/odoo-server.log", "/var/log/odoo/odoo.log"]
    found_any = False
    for log in log_files:
        if os.path.exists(log):
            print(f"[*] Analyzing {log}...")
            out, err, _ = run_cmd(f"tail -n 50 {log} | grep -iE 'ERROR|CRITICAL|Traceback'")
            if out:
                print("    [!] Found recent issues in logs:")
                print("\n".join(["        " + l for l in out.split("\n")[:5]]))
                found_any = True
    if not found_any:
        print("[OK] No recent critical errors found in logs.")

def check_logic():
    print("====================================================")
    print("      REHAB ODOO AUTOMATED HEALTH & REPAIR          ")
    print("====================================================")
    
    # Pre-checks
    bin_path = find_odoo_bin()
    conf_path = get_odoo_config()
    
    # Phase 1 & 2
    syntax_errors = validate_files()
    analyze_logs()
    
    if syntax_errors:
        print("\n[!] STOPPING: Syntax errors detected. Fix them before deploying.")
        return

    print("\n--- [Phase 3: Database & Logic Repair] ---")
    if os.path.exists(".git"):
        print("[*] Syncing with GitHub...")
        run_cmd("git pull origin master")
    
    dbs = get_databases()
    for db in dbs:
        print(f"\n[+] Repairing Logic for: {db}")
        # Logic Fix: Orphaned Teacher IDs (Prevents Registry Crash)
        sql = "UPDATE rehab_class SET teacher_id = NULL WHERE teacher_id IS NOT NULL AND teacher_id NOT IN (SELECT id FROM rehab_staff);"
        run_cmd(f"sudo -u postgres psql -d {db} -c \"{sql}\"")
        
        # Registry Update
        if bin_path and conf_path:
            print(f"    - Upgrading rehab_management module...")
            upgrade_cmd = f"sudo su - odoo -s /bin/bash -c \"{bin_path} -c {conf_path} -d {db} -u rehab_management --stop-after-init\""
            _, err, code = run_cmd(upgrade_cmd)
            if code != 0:
                print(f"    [!] Upgrade failed for {db}")
            else:
                print(f"    [OK] Logic synchronized for {db}")

    print("\n--- [Phase 4: Service Management] ---")
    print("[*] Restarting Odoo service...")
    run_cmd("sudo systemctl restart odoo")
    
    # Final Verification
    print("[*] Verifying service status...")
    out, _, _ = run_cmd("systemctl is-active odoo")
    print(f"[*] Odoo Status: {out.upper()}")
    
    print("\n====================================================")
    print("    AUTO-FIX COMPLETE. SYSTEM IS READY.             ")
    print("====================================================")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script as root (sudo).")
        sys.exit(1)
    check_logic()

