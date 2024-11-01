# Industries Summarizer

## Обзор

Industries Summarizer - комплексный инструмент, предназначенный для агрегации, суммирования и генерации отчетов по отраслевой информации из различных онлайн-источников при помощи llama3:instruct.

## Содержание

1. [Особенности](#особенности)
2. [Структура проекта](#структура-проекта)
3. [Установка](#установка)
4. [Использование](#использование)
5. [Поисковые запросы](#поисковые-запросы)
6. [Логирование](#логирование)

## Особенности

- **Агрегация результатов поиска**: Получение результатов поиска из Google на основе предопределенных запросов.
- **Суммирование**: Суммирование содержимого полученных URL-адресов с использованием языковой модели.
- **Генерация отчетов**: Создание подробных отчетов на основе саммари.
- **Парсинг отчетов**: Обработка и форматирование отчетов для удобного чтения.

## Структура проекта

```plaintext
industries_summarizer/
├── .gitignore
├── run.py
├── scripts/
│   ├── __init__.py
│   ├── get_root_project_dir.py
│   ├── report_generator.py
│   ├── report_parser.py
│   ├── search_results_aggregator.py
│   └── summarizer.py
├── search_quaries/
│   └── smart_manufacturing.json
└── README.md
```

### Основные файлы и директории

- **run.py**: Основной скрипт для запуска всего процесса.
- **scripts/**: Содержит все основные скрипты для агрегации, суммирования, генерации отчетов и парсинга.
- **search_quaries/**: Содержит JSON-файлы с поисковыми запросами для различных отраслей.

## Установка

### Предварительные требования

- Python 3.8 или выше
- [Ollama](https://ollama.com/download)

### Шаги

1. **Клонируйте репозиторий**:
    ```sh
    git clone https://github.com/ddreamboy/industries_summarizer.git
    cd industries_summarizer
    ```
2. **Установите Ollama** из [официального источника](https://ollama.com/download).
Запустите Ollama и выполните команду для установки модели:
    ```sh
    ollama run llama3:instruct
    ```
3. **Создайте и активируйте виртуальную среду**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # В Windows используйте `venv\Scripts\activate`
    ```

4. **Установите необходимые пакеты**:
    ```sh
    pip install -r requirements.txt
    ```

## Использование

### Запуск основного скрипта

Для запуска основного скрипта выполните следующую команду:

```sh
python run.py
```

Это запустит процесс агрегации результатов поиска, суммирования содержимого и генерации отчетов по отрасли, указанной в переменной `industry = 'smart_manufacturing'` в функции `main()` в `run.py`

> На данный момент по неисследованным причинам при непрерывной работе пайплайна, от поиска ссылок на источники до генерации отчетов, модель начинает выдавать нерелевантные отчеты, поэтому код с 40 по 43 строки и на 55 строке в `run.py` закомментирован.
> В связи с этим после завершения работы скрипта `run.py` необходимо выаолнить команду

```sh
python scripts/report_generator.py
```
>Если вы изменяли отрасль в функции `main()` в `run.py`, это также следует сделать в функции `main()` в `scripts/report_generator.py`

### Описание скриптов

- **run.py**: Организует весь процесс, вызывая функции из других скриптов.
- **scripts/search_results_aggregator.py**: Получает результаты поиска на основе предопределенных запросов.
- **scripts/summarizer.py**: Суммирует содержимое полученных URL-адресов.
- **scripts/report_generator.py**: Создает отчеты по каждому саммари, определяя значимость источника.
- **scripts/report_parser.py**: Обрабатывает и форматирует отчеты в markdown формате.

### Поисковые запросы

Поисковые запросы определены в JSON-файлах, расположенных в директории `search_quaries`. Например, `smart_manufacturing.json` содержит запросы, связанные с умным производством.

### Логирование

Логирование настроено на сохранение логов в директории `logs`. Каждый скрипт имеет свой собственный файл логов:

- **main.log**: Логи из основного скрипта.
- **search_result_aggregator.log**: Логи из агрегатора результатов поиска.
- **summarizer.log**: Логи из сумматора.
