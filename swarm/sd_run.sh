#!/bin/bash

docker stack deploy -c docker-compose_sd_layout.yml serv_layout
sleep 1s
docker stack deploy -c docker-compose_sd_user_registo.yml serv_user_registo
sleep 1s
docker stack deploy -c docker-compose_sd_salas.yml serv_salas
sleep 1s
docker stack deploy -c docker-compose_sd_horario.yml serv_horario
sleep 1s
docker stack deploy -c docker-compose_sd_pedidos.yml serv_pedidos
