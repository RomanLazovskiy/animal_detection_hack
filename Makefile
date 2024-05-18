APP_NAME_ASCII = ClassificationApp  # ASCII-friendly name for internal use
VENV_DIR = .venv
SPEC_FILE = app.spec
MAIN_FILE = gui/app.py

.DEFAULT_GOAL := help

# Detect the OS
ifeq ($(OS),Windows_NT)
    ACTIVATE_CMD = .\\$(VENV_DIR)\\Scripts\\activate
    PYTHON = python
    RM_DIR = rmdir /S /Q
    RM_FILE = del /Q
    TOUCH = $(PYTHON) -c "from pathlib import Path; Path('.venv/Scripts/activate').touch()"
else
    ACTIVATE_CMD = . $(VENV_DIR)/bin/activate
    PYTHON = python3
    RM_DIR = rm -rf
    RM_FILE = rm -f
    TOUCH = touch $(VENV_DIR)/bin/activate
endif

# Установка виртуального окружения и зависимостей
venv: $(VENV_DIR)/Scripts/activate
$(VENV_DIR)/Scripts/activate: pyproject.toml
	if [ ! -d "$(VENV_DIR)" ]; then \
	    $(PYTHON) -m venv $(VENV_DIR); \
	    $(ACTIVATE_CMD) && poetry install --no-root; \
	    $(TOUCH); \
	fi

# Сборка приложения в исполняемый exe файл
build: venv $(SPEC_FILE)
	$(ACTIVATE_CMD) && pyinstaller --clean --noconfirm $(SPEC_FILE)

# Удаление сборки и временных файлов
clean:
	$(RM_DIR) build dist __pycache__ $(VENV_DIR)
	$(RM_FILE) $(SPEC_FILE)

# Запуск приложения
run: venv
	$(ACTIVATE_CMD) && python $(MAIN_FILE)

# Обновление зависимостей через poetry
update-deps: venv
	$(ACTIVATE_CMD) && poetry update

# Помощь
help:
	@echo "Используйте make <опция> для выполнения одного из следующих действий:"
	@echo "  venv            Создание виртуального окружения и установка зависимостей"
	@echo "  build           Сборка приложения в исполняемый exe файл"
	@echo "  clean           Удаление сборки и временных файлов"
	@echo "  run             Запуск приложения"
	@echo "  update-deps     Обновление зависимостей через poetry"

.PHONY: venv build clean run update-deps help
