<img src="https://hlx.ai/images/Helix_Logo-white.svg" alt="helix logo" width="300px"/>

# How to run a helix cluster at home with basic instrumentation
This is an example of using docker-compose to run a cluster of nodes on a host machine.

**Necessary prerequisites:**
* Python 3
* docker-compose
* pendulum jar

## QUICKSTART
1. **Build the dev branch of pendulum.**
https://github.com/HelixNetwork/pendulum/tree/dev
2. **Put the jar into this repo's ./helix-1.0/target directory**
3. On command line, type ```python configure-many.py -num_nodes 8 -spam_interval 0 && docker-compose up --build -d```

The first build might take a while.

**Optional prerequisites:**
* If you want the cluster to be available to the public, you might need to set up port forwarding on your router for the nginx server. You should forward port 80 and port 81. Port 80 goes to the nginx reverse proxy for the api servers, and port 81 goes to the grafana dashboard.
