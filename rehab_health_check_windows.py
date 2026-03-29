import subprocess
import os
import sys
import glob

def run_cmd(cmd):
    try:
        # Use shell=True for Windows and handle encoding
        result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def find_local_odoo():
    # Common Windows Odoo paths
    paths = [
        r"C:\Program Files\Odoo 19.0.20260309\server\odoo-bin.exe",
        r"C:\Program Files\Odoo 19.0\server\odoo-bin.exe"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def find_local_conf():
    paths = [
        r"C:\Program Files\Odoo 19.0.20260309\server\odoo.conf",
        r"C:\Program Files\Odoo 19.0\server\odoo.conf"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def validate_files():
    print("\n--- [Phase 1: Local File Validation] ---")
    errors = []
    
    python_exe = r"C:\Program Files\Odoo 19.0.20260309\python\python.exe"
    
    # Check XML
    print("[*] Checking XML files for syntax errors...")
    for xml_file in glob.glob("**/*.xml", recursive=True):
        # Using a simple python script to parse
        out, err, code = run_cmd(f'"{python_exe}" -c "import lxml.etree; lxml.etree.parse(r\"{xml_file}\")"')
        if code != 0:
            print(f"    [!] XML Syntax Error in {xml_file}")
            errors.append(xml_file)
            
    # Check Python
    print("[*] Checking Python files for syntax errors...")
    for py_file in glob.glob("**/*.py", recursive=True):
        if "rehab_health_check" in py_file: continue
        out, err, code = run_cmd(f'"{python_exe}" -m py_compile "{py_file}"')
        if code != 0:
            print(f"    [!] Python Syntax Error in {py_file}")
            errors.append(py_file)
            
    if not errors:
        print("[OK] All code files passed local syntax validation.")
    return errors

def check_logic():
    print("====================================================")
    print("      REHAB ODOO LOCAL WINDOWS HEALTH CHECK         ")
    print("====================================================")
    
    bin_path = find_local_odoo()
    conf_path = find_local_conf()
    print(f"[*] Odoo Binary: {bin_path or 'NOT DETECTED'}")
    print(f"[*] Odoo Config: {conf_path or 'NOT DETECTED'}")
    
    validate_files()
    
    print("\n--- [Phase 3: Local Database Repair] ---")
    # On Windows, psql might not be in path or might need PGUSER
    sql = "UPDATE rehab_class SET teacher_id = NULL WHERE teacher_id IS NOT NULL AND teacher_id NOT IN (SELECT id FROM rehab_staff);"
    db = "rehab_db"
    print(f"[*] Attempting data repair on {db}...")
    run_cmd(f'psql -d {db} -U openpg -c "{sql}"')
    
    if bin_path and conf_path:
        print(f"[*] Attempting module upgrade on {db}...")
        # Note: On Windows we usually run odoo-bin directly
        upgrade_cmd = f'"{bin_path}" -c "{conf_path}" -d {db} -u rehab_management --stop-after-init'
        print(f"    Executing: {upgrade_cmd}")
        _, err, code = run_cmd(upgrade_cmd)
        if code != 0:
             print(f"    [!] Upgrade error: {err[:200]}")
        else:
             print(f"    [OK] Local registry updated.")

    print("\n--- [Final Verification] ---")
    print("[*] Local health check finished. Please restart your Odoo service manually if needed.")

if __name__ == "__main__":
    check_logic()
