FROM node:16.8-alpine

WORKDIR /client

ENV PATH /app/node_modules/.bin:$PATH

COPY package.json ./
COPY package-lock.json ./
RUN npm install

COPY ./public ./public
COPY ./src ./src

EXPOSE 3000

CMD npm start
