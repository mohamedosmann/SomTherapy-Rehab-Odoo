import psycopg2
import traceback

try:
    conn = psycopg2.connect(dbname='rehab_db', user='openpg', password='openpgpwd', host='localhost', port=5432)
    cur = conn.cursor()
    cur.execute('UPDATE rehab_class SET teacher_id=NULL;')
    conn.commit()
    print('Fix applied successfully: cleared teacher_id.')
except Exception as e:
    print(f'Error occurred: {e}')
    traceback.print_exc()
finally:
    if 'cur' in locals(): cur.close()
    if 'conn' in locals(): conn.close()
