FROM nginx:alpine

# Copy static files
COPY ../*.html /usr/share/nginx/html/
COPY ../*.css /usr/share/nginx/html/
COPY ../*.js /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]