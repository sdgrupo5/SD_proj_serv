from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import requests
from functools import wraps
import sys
sys.path.insert(0, '/etc/sd_proj_ip/')
from sd_ip import *
import pika


app = Flask(__name__)

#Home
@app.route('/')
def index():
   return render_template('home.html')

#About
@app.route('/about')
def about():
   return render_template('about.html')

#Services
@app.route('/services')
def services():
   return render_template('services.html')

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      usernamein = request.form["username"]
      passwordin = request.form["password"]
      #lidar com erro http e if service down
      try:
         #Obter lista de users
         m_api=requests.get('http://' + SD_HOST_IP + ':8020/sdusers', auth=('admin', 'SuperSecretPwd'))
         m_api.raise_for_status()
         msg_api=m_api.json()
      except requests.exceptions.RequestException as err:
         msg_api={}
         flash('Service Unavailable, tente mais tarde', 'danger')
      #Procurar user e obter pass
      password=""
      for attr in msg_api:
         if attr["username"] == usernamein:
            password = attr["password"]
            break
      #Se user exist, verificar pass valida
      if password:
         if sha256_crypt.verify(passwordin, password):
            flash('Login efetuado', 'success')
            session["logged_in"] = True
            session["username"] = usernamein
            return redirect(url_for('index'))
         else:
            flash('Password Incorrecto', 'warning')
      else:
         flash('Username Incorrecto', 'warning')

   return render_template('login.html')

#Form para pagina de registo
class RegisterForm(Form):
   nomein = StringField("Nome:", [validators.Length(min=1, max=50)])
   emailin = StringField("Email:", [validators.Length(min=5, max=50)])
   usernamein = StringField("Username:", [validators.Length(min=4, max=50)])
   passwordin = PasswordField("Password:",[
      validators.DataRequired(),
      validators.EqualTo("confirmin", message="Password do not match")
   ])
   confirmin = PasswordField("Confirm Password:")

#Lidar com o registo
@app.route('/registo', methods=['GET', 'POST'])
def registo():
   form = RegisterForm(request.form)
   if request.method == 'POST' and form.validate():
      nomepost = form.nomein.data
      emailpost = form.emailin.data
      usernamepost = form.usernamein.data
      passwordpost = form.passwordin.data
      #lidar com erro http, if service down
      try:
         #Enviar para db
         r = requests.post('http://' + SD_HOST_IP + ':8020/sdusers',
            auth=('admin', 'SuperSecretPwd'),
            data = {
               'nome' : nomepost,
               'email' : emailpost,
               'username' : usernamepost,
               'password' : sha256_crypt.encrypt(str(passwordpost))
            })
      except requests.exceptions.RequestException as err:
         r="erro"
      #lidar com a resposta do envio
      if r == "erro":
         flash('Service Unavailable, tente mais tarde', 'danger')
      else:
         if r.text.strip('\n') == "\"success\"":
            flash('Registo efetuado', 'success')
         elif r.text.strip('\n') == "\"exist\"":
            flash('Falhou, escolha outro nome', 'warning')
         else:
            flash('Falhou, tente mais tarde', 'danger')
      return redirect(url_for('login'))

   return render_template('registo.html',form=form)


#Verificar se user logged in, ver paginas apenas autorizadas
def is_logged_in(f):
   @wraps(f)
   def wrap(*args, **kwargs):
      if 'logged_in' in session:
         return f(*args, **kwargs)
      else:
         flash('Nop, sem acesso. Fazer login.', 'danger')
         return redirect(url_for('login'))
   return wrap



#Booking, Reserva de salas
@app.route('/booking', methods=['GET', 'POST'])
@is_logged_in
def booking():
   #Obter a sala a reservar
   if request.method == 'POST':
      salain = request.form["reserva"]
      #Update a reserva
      try:
         r = requests.put('http://' + SD_HOST_IP + ':8021/sdsalas',
            auth=('admin', 'SuperSecretPwd'),
            data= {'sala' : salain})
      except requests.exceptions.RequestException as err:
            r="erro"
      #lidar com a resposta do envio
      if r == "erro":
         flash('Service Unavailable, tente mais tarde', 'danger')
      else:
         if r.text.strip('\n') == "\"success_reserva\"":
            flash('Reserva efetuada', 'success')
         elif r.text.strip('\n') == "\"success_desocupa\"":
            #desocupar o horario
            m_api=requests.delete('http://' + SD_HOST_IP + ':8022/sdhorario/' + salain, auth=('admin', 'SuperSecretPwd'))
            flash('Reserva libertada', 'success')
         elif r.text.strip('\n') == "\"exist\"":
            flash('Falhou, escolha outra sala', 'warning')
         else:
            flash('Falhou, tente mais tarde', 'danger')
      return redirect(url_for('booking'))
   #lidar com erro http, if service down
   try:
      #mostrar lista com as salas
      m_api=requests.get('http://' + SD_HOST_IP + ':8021/sdsalas', auth=('admin', 'SuperSecretPwd'))
      m_api.raise_for_status()
      msg_api=m_api.json()
   except requests.exceptions.RequestException as err:
      msg_api={}
      flash('Service Unavailable, tente mais tarde', 'danger')
   return render_template('booking.html', msg_api=msg_api)


#Aoresentar salas com horario
@app.route('/horariomain')
@is_logged_in
def horariomain():
   try:
      #mostrar lista com as salas
      m_api=requests.get('http://' + SD_HOST_IP + ':8021/sdsalas', auth=('admin', 'SuperSecretPwd'))
      m_api.raise_for_status()
      msg_api=m_api.json()
   except requests.exceptions.RequestException as err:
      msg_api={}
      flash('Service Unavailable, tente mais tarde', 'danger')
   return render_template('horariomain.html', msg_api=msg_api)


#Form reservar horario
class HorarioForm(Form):
   reservadiain = StringField("Data:", [validators.Length(min=10, max=10)])
   horainiin = StringField("Hora Inicio:", [validators.Length(min=5, max=5)])
   horaendin = StringField("Hora Fim:", [validators.Length(min=5, max=5)])

#Horario das salas
@app.route('/horario/<string:nome>/', methods=['GET', 'POST'])
@is_logged_in
def horario(nome):
    form = HorarioForm(request.form)
    if request.method == 'POST' and form.validate():
       reservadia = form.reservadiain.data
       horaini = form.horainiin.data
       horaend = form.horaendin.data
       #lidar com erro http, if service down
       try:
          #Enviar para db
          r = requests.post('http://' + SD_HOST_IP + ':8022/sdhorario/' + nome,
             auth=('admin', 'SuperSecretPwd'),
             data = {
                'nome' : nome,
                'reservadia' : reservadia,
                'horaini' : horaini,
                'horaend' : horaend
             })
       except requests.exceptions.RequestException as err:
          r="erro"
       #lidar com a resposta do envio
       if r == "erro":
          flash('Service Unavailable, tente mais tarde', 'danger')
       else:
          if r.text.strip('\n') == "\"success\"":
             flash('Registo efetuado', 'success')
          else:
             flash('Falhou, tente mais tarde', 'danger')
       return redirect(url_for('booking'))

    #lidar com erro http, if service down
    try:
       m_api=requests.get('http://' + SD_HOST_IP + ':8022/sdhorario/' + nome, auth=('admin', 'SuperSecretPwd'))
       m_api.raise_for_status()
       msg_api=m_api.json()
    except requests.exceptions.RequestException as err:
       msg_api={}
       flash('Service Unavailable, tente mais tarde', 'danger')
    return render_template('horario.html', msg_api=msg_api, nome=nome, form=form)

#Pedidos
@app.route('/pedidos', methods=['GET', 'POST'])
@is_logged_in
def pedidos():
   if request.method == 'POST':
      userpedido = request.form["userpedido"]
      try:
         connection = pika.BlockingConnection(pika.ConnectionParameters(host=SD_HOST_IP))
         channel = connection.channel()
         channel.queue_declare(queue='sd_pedidos')
         channel.basic_publish(exchange='',
                            routing_key='sd_pedidos',
                            body=session["username"] + ':' + userpedido)
         connection.close()
         flash('O seu pedido foi enviado', 'success')
         return redirect(url_for('index'))
      except pika.exceptions.ConnectionClosed as err:
         flash('Service Unavailable, tente mais tarde', 'danger')

   return render_template('pedidos.html')



@app.route('/logout')
def logout():
   session.clear()
   flash('Logout efetuado', 'success')
   return redirect(url_for('login'))

if __name__ == '__main__':
   app.secret_key='chave_secret123'
   app.run(host= '0.0.0.0', debug=True)
