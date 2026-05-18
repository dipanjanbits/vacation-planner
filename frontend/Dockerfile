FROM node:18-alpine as build

WORKDIR /app
COPY package.json ./
RUN npm install
COPY public/ public/
COPY src/ src/

# API calls will be proxied through nginx to /api/
ENV REACT_APP_API_URL=/api

RUN npm run build

# Production - serve with nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
