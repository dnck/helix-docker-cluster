# -*- coding: utf-8 *-*

import shutil
import os
from subprocess import call
import argparse
import networkx as nx

api_host = "172.20.0."

DOCKERFILE = """
FROM ubuntu:16.04 as builder

FROM openjdk:jre-slim

RUN apt-get update && apt-get install -y --no-install-recommends socat && rm -rf /var/lib/apt/lists/*

EXPOSE {}:{}
EXPOSE {}:{}
EXPOSE {}:{}

COPY ./src ./src

ENV JAVA_OPTIONS="-XX:+UnlockExperimentalVMOptions -XX:+DisableAttachMechanism -XX:InitiatingHeapOccupancyPercent=60 -XX:G1MaxNewSizePercent=75 -XX:MaxGCPauseMillis=10000 -XX:+UseG1GC" JAVA_MIN_MEMORY=2G JAVA_MAX_MEMORY=4G

CMD java -jar ./target/*.jar --config ./configs/config{}.ini
"""

CONFIG =  """#NODE {} CONFIG
API_HOST = {}
PORT = {}
UDP_RECEIVER_PORT = {}
TCP_RECEIVER_PORT = {}
NEIGHBORS
ZMQ_THREADS = 1
ZMQ_ENABLED = false
ZMQ_ENABLE_IPC = false
ZMQ_ENABLE_TCP = false
ZMQ_PORT = {}
ZMQ_IPC = ipc://sbx/feeds/{}
GRAPH_ENABLED = false
HXI_DIR =  hxi
HEADLESS = true
DB_PATH = db
LOCAL_SNAPSHOTS_DEPTH = 2
#NOMINEE =
#NOMINEE_KEYFILE =
SPAM_DELAY = 0
# important that you use the dnck fork instrumentation branch for this to make
# sense:
LOCAL_SNAPSHOTS_ENABLED = true
LOCAL_SNAPSHOTS_BASE_PATH = snapshots
SAVELOG_XML_FILE = /logback-save.xml
"""

BASE_COMPOSE = """version: "3"
networks:
  helix_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24

services:
"""

API_COMPOSE = """
  node_{}:
    build:
      context: ./helix-1.0
      dockerfile: Dockerfile{}
    hostname: node_{}
    restart: unless-stopped
    volumes:
      - ./helix-1.0/target:/target
      - ./helix-1.0/configs:/configs
      - ./logs:/logs
      - ./dbs/node_{}_db:/db
      - ./dbs/node_{}_log:/mainnet.log
      - ./spent_addresses/node_{}_db:/spent-addresses-db
      - ./spent_addresses/node_{}_log:/spent-addresses-log
      - ./snapshots/node_{}_snapshots:/snapshots
    environment:
      - JAVA_MAX_MEMORY=4096m
      - JAVA_MIN_MEMORY=256m
    ports:
      - "{}:{}"
      - "{}:{}/udp"
    networks:
      helix_network:
        ipv4_address: {}
"""

NGINX_COMPOSE = """
  nginx:
    restart: unless-stopped
    build: ./nginx/
    ports:
      - "80:80"
      - "81:81"
    networks:
      helix_network:
        ipv4_address: 172.20.0.{}
"""

NGINX_CONFIG = """
upstream helix_cluster {

"""

PROMETHUES_CONFIG = """
  prometheus:
    restart: unless-stopped
    build: ./prometheus/
    ports:
      - "9090:9090"
    networks:
      helix_network:
        ipv4_address: {}{}
"""

GRAFANA_CONFIG = """
  grafana:
    restart: unless-stopped
    build: ./grafana/
    ports:
      - "3000:3000"
    networks:
      helix_network:
        ipv4_address: {}{}
"""

PROM_YML = """
global:
  scrape_interval: 5s
  evaluation_interval: 10s

scrape_configs:
  - job_name: 'helix_logs'
    scrape_interval: 5s
    static_configs:
      - targets: ['{}{}:3903']
        labels:
          group: 'logs'
"""

MTAIL_YML = """
  mtail:
    build:
      context: ./mtail
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "3903:3903"
    volumes:
      - ./logs:/logs
    networks:
      helix_network:
        ipv4_address: {}{}
    command: ["-progs", "./helix_log_analysis.mtail", "-logs", "/logs/*.log"]
"""

class SmallWorldTopology():
    def __init__(
        self,
        num_nodes,
        average_in_degree,
        probability_addition_innode
    ):
        self.average_in_degree = average_in_degree
        self.p_new_edge = probability_addition_innode
        self.overlay = nx.watts_strogatz_graph(
            n=num_nodes, k=self.average_in_degree, p=self.p_new_edge,
            seed=69
        )

    def get_neighbor(self, node_id):
        if list(self.overlay.neighbors(node_id)):
            return list(self.overlay.neighbors(node_id))

    def get_matrix(self):
        self.overlay_matrix = nx.to_numpy_matrix(self.overlay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-docker_inet_start',
        metavar='Last digit for docker inet to start iterating at',
        type=int, default=2, help=''
        )
    parser.add_argument('-api_port_start',
        metavar='Port to start iterating at',
        type=int, default=8085, help=''
        )
    parser.add_argument('-udp_port_start',
        metavar='UDP Receiver port to start iterating at',
        type=int, default=4100, help=''
        )
    parser.add_argument('-tcp_port_start',
        metavar='TCP Receiver port to start iterating at',
        type=int, default=5100, help=''
        )
    parser.add_argument('-zmq_ipc_start',
        metavar='ZMQ ipc port to start iterating at',
        type=int, default=1, help=''
        )
    parser.add_argument('-zmq_port_start',
        metavar='ZMQ port to start iterating at',
        type=int, default=6550, help=''
        )
    parser.add_argument('-num_nodes',
        metavar='Number of nodes.',
        type=int, default=5, help=''
        )
    parser.add_argument('-spam_interval',
        metavar='Interval between spam messages in miliseconds.',
        type=int, default=40, help=''
        )

    args = parser.parse_args()

    docker_inet_start = args.docker_inet_start
    api_port_start = args.api_port_start
    udp_port_start = args.udp_port_start
    tcp_port_start = args.tcp_port_start
    zmq_ipc_start = args.zmq_ipc_start
    zmq_port_start = args.zmq_port_start
    num_nodes = args.num_nodes
    spam_interval = args.spam_interval

    udp_port = 4100

    topology = SmallWorldTopology(
        num_nodes,
        average_in_degree=3,
        probability_addition_innode=0.1
        )

    if os.path.isdir("./helix-1.0/configs"):
        shutil.rmtree(os.path.normpath("./helix-1.0/configs"))
    os.mkdir(os.path.normpath("./helix-1.0/configs"))

    if not os.path.isdir("./snapshots"):
        os.mkdir(os.path.normpath("./snapshots"))
    if not os.path.isdir("./dbs"):
        os.mkdir(os.path.normpath("./dbs"))
    if not os.path.isdir("./spent_addresses"):
        os.mkdir(os.path.normpath("./spent_addresses"))

    old_docker_files = [
        os.path.join("./helix-1.0", i)
            for i in os.listdir("./helix-1.0") if i.startswith("Dockerfile")
    ]
    [os.remove(i) for i in old_docker_files]
    for node_id in range(num_nodes):

        node_docker_file = DOCKERFILE.format(
            api_port_start, api_port_start,
            udp_port_start, udp_port_start,
            tcp_port_start, tcp_port_start,
            node_id)

        host = api_host + str(docker_inet_start)

        config_file = CONFIG.format(
            node_id,
            host,
            api_port_start,
            udp_port_start,
            tcp_port_start,
            zmq_port_start,
            zmq_ipc_start
            )

        node_neighbors = ""
        for n in topology.get_neighbor(node_id):
            node_neighbors = \
                node_neighbors + "udp://{}:{}, ".format(
                    api_host + str(2 + n), udp_port + n
                    )

        node_neighbors = node_neighbors[:-2]

        config_file = config_file.replace(
            "NEIGHBORS", "NEIGHBORS = {}".format(node_neighbors)
            )

        if node_id in [0, 1, 2, 3, 4]:
            config_file = \
                config_file.replace('#NOMINEE =', 'NOMINEE = {}'.format(
                'src/main/resources/nominees/nominee{}/nominee_seed_{}.txt'.format(
                    node_id+1, node_id+1
                    )
                )
            )
            config_file = \
                config_file.replace(
                    '#NOMINEE_KEYFILE =', 'NOMINEE_KEYFILE = {}'.format(
                        '/nominees/nominee{}/Nominee_{}.key'.format(
                            node_id+1, node_id+1
                        )
                    )
                )
        #else:
        NGINX_CONFIG += \
            '      server {} weight=1;\n'.format(host+':'+str(api_port_start))
        config_file = \
            config_file.replace('SPAM_DELAY = 0', 'SPAM_DELAY = {}'.format(
                spam_interval
                )
            )
        BASE_COMPOSE = BASE_COMPOSE + API_COMPOSE.format(
            node_id, node_id, node_id, node_id, node_id, node_id, node_id,
            node_id, api_port_start, api_port_start, udp_port_start,
            udp_port_start, host
        )
        #prometheus_pushers.append(host+":2019")
        docker_inet_start += 1
        api_port_start += 1
        udp_port_start += 1
        tcp_port_start += 1
        zmq_ipc_start += 1
        zmq_port_start += 1

        with open(
            os.path.normpath(
                "./helix-1.0/configs/config{}.ini".format(node_id)), "w"
            ) as f:
            f.write(config_file)

        with open(os.path.normpath(
            "./helix-1.0/Dockerfile{}".format(node_id)), "w"
            ) as f:
            f.write(node_docker_file)

    BASE_COMPOSE = BASE_COMPOSE + NGINX_COMPOSE.format(docker_inet_start)
    docker_inet_start += 1
    BASE_COMPOSE = BASE_COMPOSE + PROMETHUES_CONFIG.format(api_host, docker_inet_start)
    docker_inet_start += 1
    BASE_COMPOSE = BASE_COMPOSE + GRAFANA_CONFIG.format(api_host, docker_inet_start)
    grafana_host = "{}{}:3000".format(api_host, docker_inet_start)
    NGINX_CONFIG += """
      }
upstream helix_grafana {
      server """+grafana_host+";"+"""
      }"""
    docker_inet_start += 1
    BASE_COMPOSE = BASE_COMPOSE + MTAIL_YML.format(api_host, docker_inet_start)

    PROM_YML = PROM_YML.format(api_host, docker_inet_start)
    with open(
        os.path.normpath("./prometheus/prometheus.yml"), "w") as f:
        f.write(PROM_YML)
    with open(
        os.path.normpath("./docker-compose.yml"), "w") as f:
        f.write(BASE_COMPOSE)
    NGINX_CONFIG += """
    server {
        listen 80;
        server_name helix_cluster;
        location / {
            proxy_pass http://helix_cluster;
        }
    }
    server {
        listen 81;
        server_name helix_grafana;
        location / {
            proxy_pass http://helix_grafana;
        }
    }
    """
    with open(
        os.path.normpath("./nginx/helixnet.conf"), "w") as f:
        f.write(NGINX_CONFIG)
