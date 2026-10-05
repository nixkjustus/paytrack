import json, sqlite3, secrets, hashlib, os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from http.cookies import SimpleCookie
from datetime import datetime, timezone

ROOT=os.path.dirname(__file__); DB=os.path.join(ROOT,'paytrack.db')
con=sqlite3.connect(DB); con.executescript('''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT,rate REAL DEFAULT 20,tax REAL DEFAULT 17.3,overtime REAL DEFAULT 1.5);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER);
CREATE TABLE IF NOT EXISTS shifts(id INTEGER PRIMARY KEY,user_id INTEGER,date TEXT,start TEXT,end TEXT,break_mins INTEGER DEFAULT 0,note TEXT DEFAULT '');
'''); con.close()
def db(): return sqlite3.connect(DB)
def hashpw(p): return hashlib.sha256(('paytrack-v1:'+p).encode()).hexdigest()
class H(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  p=urlparse(path).path
  if p=='/': p='/index.html'
  return os.path.join(ROOT,p.lstrip('/'))
 def sendj(self,x,status=200,cookie=None):
  b=json.dumps(x).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',len(b));
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers(); self.wfile.write(b)
 def body(self):
  try:return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
  except:return {}
 def user(self):
  c=SimpleCookie(self.headers.get('Cookie')); t=c.get('session')
  if not t:return None
  con=db(); r=con.execute('select users.id,email,rate,tax,overtime from sessions join users on users.id=sessions.user_id where token=?',(t.value,)).fetchone(); con.close(); return r
 def do_POST(self):
  p=urlparse(self.path).path; x=self.body()
  if p in ['/api/signup','/api/login']:
   email=x.get('email','').strip().lower(); pw=x.get('password','')
   if not email or len(pw)<6:return self.sendj({'error':'Enter a valid email and a password of 6+ characters.'},400)
   con=db()
   try:
    if p.endswith('signup'):
     cur=con.execute('insert into users(email,password) values(?,?)',(email,hashpw(pw))); uid=cur.lastrowid
    else:
     r=con.execute('select id from users where email=? and password=?',(email,hashpw(pw))).fetchone()
     if not r:return self.sendj({'error':'Email or password is incorrect.'},401)
     uid=r[0]
    token=secrets.token_urlsafe(32); con.execute('insert into sessions values(?,?)',(token,uid)); con.commit(); con.close(); return self.sendj({'ok':1},cookie=f'session={token}; Path=/; HttpOnly; SameSite=Lax')
   except sqlite3.IntegrityError: con.close(); return self.sendj({'error':'An account with that email already exists.'},409)
  u=self.user()
  if not u:return self.sendj({'error':'Unauthorized'},401)
  con=db()
  if p=='/api/shifts':
   con.execute('insert into shifts(user_id,date,start,end,break_mins,note) values(?,?,?,?,?,?)',(u[0],x['date'],x['start'],x['end'],int(x.get('break_mins',0)),x.get('note',''))); con.commit(); con.close(); return self.sendj({'ok':1})
  if p=='/api/settings':
   con.execute('update users set rate=?,tax=?,overtime=? where id=?',(float(x['rate']),float(x['tax']),float(x['overtime']),u[0])); con.commit(); con.close(); return self.sendj({'ok':1})
  if p=='/api/logout':
   c=SimpleCookie(self.headers.get('Cookie')); con.execute('delete from sessions where token=?',(c['session'].value,)); con.commit(); con.close(); return self.sendj({'ok':1},cookie='session=; Max-Age=0; Path=/')
  con.close(); self.sendj({'error':'Not found'},404)
 def do_DELETE(self):
  u=self.user()
  if not u:return self.sendj({'error':'Unauthorized'},401)
  try:i=int(urlparse(self.path).path.split('/')[-1])
  except:return self.sendj({'error':'Bad id'},400)
  con=db(); con.execute('delete from shifts where id=? and user_id=?',(i,u[0])); con.commit(); con.close(); self.sendj({'ok':1})
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/api/data':
   u=self.user()
   if not u:return self.sendj({'authenticated':False})
   con=db(); rows=con.execute('select id,date,start,end,break_mins,note from shifts where user_id=? order by date desc,start desc',(u[0],)).fetchall(); con.close()
   return self.sendj({'authenticated':True,'user':{'email':u[1],'rate':u[2],'tax':u[3],'overtime':u[4]},'shifts':[dict(zip(['id','date','start','end','break_mins','note'],r)) for r in rows]})
  return super().do_GET()
if __name__=='__main__': ThreadingHTTPServer(('0.0.0.0',8000),H).serve_forever()
