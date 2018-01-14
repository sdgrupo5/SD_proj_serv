# -*- coding: utf-8 -*-
import time 
import sys
sys.path.insert(0, '/etc/sd_proj_ip/')
from sd_ip import *
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host=SD_HOST_IP))
channel = connection.channel()
channel.queue_declare(queue='sd_pedidos')
def callback(ch, method, properties, body):
   file = open("/etc/sd_proj_ip/sd_pedidos.txt","a")
   file.write(time.strftime('%Y-%m-%d %H:%M:%S') + ": " + body + "\n") 
   file.close() 

channel.basic_consume(callback,
                      queue='sd_pedidos',
                      no_ack=True)  
channel.start_consuming()

