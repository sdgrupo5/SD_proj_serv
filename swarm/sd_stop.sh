#!/bin/bash

docker stack rm serv_layout
sleep 1s
docker stack rm serv_user_registo
sleep 1s
docker stack rm serv_salas
sleep 1s
docker stack rm serv_horario
sleep 1s
docker stack rm serv_pedidos
