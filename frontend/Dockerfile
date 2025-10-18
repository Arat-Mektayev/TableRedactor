FROM node:20-alpine
WORKDIR /app

# Установка serve для раздачи статики
RUN npm install -g serve

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем все зависимости, включая devDependencies
RUN npm install --legacy-peer-deps

# Копируем исходный код
COPY . .

# Сборка проекта
RUN npm run build

EXPOSE 3000

# Запуск сервера для раздачи статики
CMD ["serve", "-s", "build", "-l", "3000"]