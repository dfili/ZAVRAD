FROM node:16.10-alpine

WORKDIR /client

COPY package.json ./

RUN corepack enable
RUN yarn init -2
RUN yarn install
RUN yarn global add serve

COPY ./public ./public
COPY ./src ./src

EXPOSE 5000

CMD yarn build && serve -s build