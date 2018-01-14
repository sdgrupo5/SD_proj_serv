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
app.config['MYSQL_DB'] = 'sd_horario' 
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

def buscalista(nome):
   # Create cursor connection to mysql
   cur = mysql.connection.cursor()
   # Get table
   result = cur.execute("SELECT * FROM sd_horario_table WHERE nome = %s", {nome})
   if result > 0:
      sd_horario_table = []
      for row in cur:
         sd_horario_table.append(row)
      return sd_horario_table
   else:
      msg = 'Nop, not fount'
      return msg
   # Close connection
   cur.close()

#Parser Request para post
parser = reqparse.RequestParser()
parser.add_argument('nome')
parser.add_argument('reservadia')
parser.add_argument('horaini')
parser.add_argument('horaend')

class ListaHorario(Resource):
   @auth.login_required
   def get(self, nome_id):
      return buscalista(nome_id)

   def post(self, nome_id):
      args = parser.parse_args()
      #Verificar se vazio
      if args.nome and args.reservadia and args.horaini and args.horaend and args.nome == nome_id:
         #Lidar se nao ligar db
         try:
            #Criar connect
            cur = mysql.connection.cursor() 
            #Execute the query
            cur.execute("INSERT INTO sd_horario_table(nome, reservadia, horaini, horaend) VALUES(%s, %s, %s, %s)", (args.nome, args.reservadia, args.horaini, args.horaend))
            #Comit changes to DB
            mysql.connection.commit()
         except Error as error:
            return "fail"
         finally:
            #Close connection
            cur.close()
            return "success"
      else:
         return "fail"

   def delete(self, nome_id):
     try:
        #Criar connect
        cur = mysql.connection.cursor()
        #Execute the query
        cur.execute("DELETE FROM sd_horario_table WHERE nome = %s", {nome_id})
        #Comit changes to DB
        mysql.connection.commit()
     except Error as error:
        return "fail"
     finally:
        #Close connection
        cur.close()
        return "success" 

## Add api resource routing
api.add_resource(ListaHorario, '/sdhorario/<nome_id>')

if __name__ == '__main__':
   app.run(host= '0.0.0.0', debug=True, port=8022)


