FROM nginx

ADD nginx_default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80