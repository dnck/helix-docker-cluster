# Dockerfile-nginx
FROM nginx:latest

# Nginx will listen on this port
EXPOSE 80
EXPOSE 81

# Remove and replace the default config file
RUN rm /etc/nginx/conf.d/default.conf
COPY helixnet.conf /etc/nginx/conf.d
