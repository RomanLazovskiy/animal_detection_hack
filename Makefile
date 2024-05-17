APP_NAME = Классификация_парнокопытных

VENV_DIR = .venv

SPEC_FILE = app.spec

MAIN_FILE = gui/app.py

.DEFAULT_GOAL := help

# Установка виртуального окружения и зависимостей
venv: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: pyproject.toml
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && poetry install
	touch $(VENV_DIR)/bin/activate

# Сборка приложения в исполняемый файл
build: venv $(SPEC_FILE)
	. $(VENV_DIR)/bin/activate && pyinstaller --clean --noconfirm $(SPEC_FILE)

# Удаление сборки и временных файлов
clean:
	rm -rf build dist $(APP_NAME).spec __pycache__ $(VENV_DIR)

# Запуск приложения
run: venv
	. $(VENV_DIR)/bin/activate && python $(MAIN_FILE)

# Создание спецификации PyInstaller
$(SPEC_FILE): $(MAIN_FILE)
	. $(VENV_DIR)/bin/activate && pyinstaller --name $(APP_NAME) --onefile --windowed $(MAIN_FILE)

# Обновление зависимостей через poetry
update-deps: venv
	. $(VENV_DIR)/bin/activate && poetry update

# Помощь
help:
	@echo "Используйте make <опция> для выполнения одного из следующих действий:"
	@echo "  venv            Создание виртуального окружения и установка зависимостей"
	@echo "  build           Сборка приложения в исполняемый файл"
	@echo "  clean           Удаление сборки и временных файлов"
	@echo "  run             Запуск приложения"
	@echo "  update-deps     Обновление зависимостей через poetry"

.PHONY: venv build clean run update-deps help
