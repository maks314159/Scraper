#!/bin/bash

# Создайте виртуальное окружение (если оно еще не создано)
python3 -m venv myenv

# Активируйте виртуальное окружение
source myenv/bin/activate

# Устанавливаем библиотеки
pip install pyTelegramBotAPI
pip install beautifulsoup4
pip install requests