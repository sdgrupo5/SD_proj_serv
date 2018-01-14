from flask import Flask, render_template, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from flask_restful import reqparse, abort, Api, Resource
from flask_httpauth import HTTPBasicAuth
import sys
sys.path.insert(0, '/etc/sd_proj_ip/')
from sd_ip import *

app = Flask(__name__)


# Config MySQL
app.config['MYSQL_HOST'] = SD_HOST_IP
app.config['MYSQL_PORT'] = 6603
app.config['MYSQL_USER'] = 'root' 
app.config['MYSQL_PASSWORD'] = 'mypassword' 
app.config['MYSQL_DB'] = 'sd_users' 
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' 
# init MySQL
mysql = MySQL(app)

#init api
api = Api(app)
#init api private
auth = HTTPBasicAuth()

#Api data access
USER_DATA = {
    "admin": "SuperSecretPwd"
}

#Verificar api access
@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password

def buscalista():
   # Create cursor connection to mysql
   cur = mysql.connection.cursor()
   # Get table
   result = cur.execute("SELECT nome, email, username, password FROM sd_users_table")
   if result > 0:
      sd_users_table = []
      for row in cur:
         sd_users_table.append(row)
      return sd_users_table
   else:
      msg = 'Nop, not fount'
      return msg
   # Close connection
   cur.close()

#Parser Request para post
parser = reqparse.RequestParser()
parser.add_argument('nome')
parser.add_argument('email')
parser.add_argument('username')
parser.add_argument('password')

class ListaNomes(Resource):
   @auth.login_required
   def get(self):
      return buscalista()

   def post(self):
      args = parser.parse_args()
      #Verificar se vazio
      if args.nome and args.email and args.username and args.password:
         cur = mysql.connection.cursor()
         #Verificar se username existe
         veruser=cur.execute("SELECT 1 FROM sd_users_table WHERE username = %s", {args.username})
         cur.close()
         #Se nao existe faz
         if veruser == 0:
            #Lidar se nao ligar db
            try:
               #Criar connect
               cur = mysql.connection.cursor() 
               #Execute the query
               cur.execute("INSERT INTO sd_users_table(nome, email, username, password) VALUES(%s, %s, %s, %s)", (args.nome, args.email, args.username, args.password))
               #Comit changes to DB
               mysql.connection.commit()
            except Error as error:
               return "fail"
            finally:
               #Close connection
               cur.close()
               return "success"
         else: 
            return "exist"
      else:
         return "fail"

## Add api resource routing
api.add_resource(ListaNomes, '/sdusers')

if __name__ == '__main__':
   app.run(host= '0.0.0.0', debug=True, port=8020)


