# How to run a helix cluster at home with basic instrumentation
This is an example of using docker-compose to run a cluster of nodes on a host machine.

**Necessary prerequisites:**
* Python 3
* docker-compose
* helix-1.0 jar

## QUICKSTART
1. **Build the dev-instrumentation branch of the dnck fork of helix-1.0.**
2. **Put the jar into the helix-1.0/target directory in this repo**
3. ```python configure-many.py -num_nodes 5 -spam_interval 1000 && docker-compose up --build -d```

**Optional prerequisites:**
* If you want the cluster to be available to the public, you might need to set up port forwarding on your router for the nginx server.
