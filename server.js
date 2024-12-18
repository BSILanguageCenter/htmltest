const express = require('express');
const path = require('path');

const app = express();
const port = 3000;

// Настроим Express для обслуживания статических файлов из папки public
app.use(express.static(path.join(__dirname, 'public')));

// Запустим сервер
app.listen(port, () => {
    console.log(`Сервер работает на http://localhost:${port}`);
});
