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
app.config['MYSQL_DB'] = 'sd_salas' 
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
   result = cur.execute("SELECT * FROM sd_salas_table")
   sd_salas_table = cur.fetchall()
   if result > 0:
      return sd_salas_table
   else:
      msg = 'Nop, not fount'
      return msg
   # Close connection
   cur.close()

#Parser Request
parser = reqparse.RequestParser()
parser.add_argument('sala')

class ListaSalas(Resource):
   @auth.login_required
   def get(self):
      return buscalista()

   def put(self):
      args = parser.parse_args()
      #Verificar se vazio
      if args.sala:
         cur = mysql.connection.cursor()
         #Get sala
         versala=cur.execute("SELECT * FROM sd_salas_table WHERE nome = %s", {args.sala})
         sd_sala = cur.fetchone()
         cur.close()
         #sala existe
         if versala == 1:
            #Lidar se nao ligar db
            try:
               #Criar connect
               cur = mysql.connection.cursor() 
               #Mudar reserva 
               if sd_sala["reserva"] == 0:
                  #Execute the query
                  cur.execute("UPDATE sd_salas_table SET reserva = 1 WHERE nome = %s", {args.sala})
               else:
                  cur.execute("UPDATE sd_salas_table SET reserva = 0 WHERE nome = %s", {args.sala})
               #Comit changes to DB
               mysql.connection.commit()
            except Error as error:
               return "fail"
            finally:
               #Close connection
               cur.close()
               if sd_sala["reserva"] == 0:
                  return "success_reserva"
               else:
                  return "success_desocupa"
         else: 
            return "exist"
      else:
         return "fail"

## Add api resource routing
api.add_resource(ListaSalas, '/sdsalas')

if __name__ == '__main__':
   app.run(host= '0.0.0.0', debug=True, port=8021)


