import subprocess
import os

key_path = r'C:\Users\yuusuf\.ssh\id_rsa'
if not os.path.exists(key_path):
    proc = subprocess.Popen(['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', key_path, '-N', ''], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    print(out.decode())
    print(err.decode())
else:
    print('Key already exists.')
