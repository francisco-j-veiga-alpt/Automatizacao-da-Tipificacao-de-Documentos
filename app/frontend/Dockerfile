FROM node:18-alpine
WORKDIR /app/frontend
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]

#RUN npm run build
# FROM nginx:alpine
# COPY --from=0 /app/build /usr/share/nginx/html
# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]
