"""
MCP Notes Server
----------------
Короткое описание
Этот модуль реализует простой MCP (Model Control Plane) - сервер заметок, который
экспонирует набор инструментов (tools) для создания, поиска, получения и управления
заметками. Каждый метод, помеченный декоратором @mcp.tool, становится доступным как
инструмент (function) для внешних клиентов/моделей через FastMCP.

Ключевые моменты
- Экспортируемые инструменты: add_note, list_notes, list_recent_notes, search_notes,
  delete_note, move_note. Они принимают простые типы и возвращают JSON-совместимые
  структуры (dict/list).
- Хранилище заметок в этой реализации — в памяти (словарь NOTES_BY_ID). Для
  production необходимо заменить на персистентное хранилище (БД, S3, файл и т.д.).
- Конфигурация: HOST и PORT читаются из окружения (NOTES_HOST, NOTES_PORT).
- Запуск: при прямом запуске модуля запускается mcp.run(transport="sse") — пример
  транспортного адаптера (Server-Sent Events). В продакшне рекомендовано запускать
  через процесс-менеджер (systemd/supervisor) или контейнер.

Что добавить для полноценной работы в продакшне
- Персистентность: подключение БД (Postgres/SQLite), миграции, резервное копирование.
- Авторизация/аутентификация: токены/ACL для ограничения доступа к инструментам.
- Логирование/метрики: структурированное логирование, экспорт метрик (Prometheus).
- Безопасность: проверка входных данных, ограничение размеров заметок, rate-limiting.
- Конфигурация деплоя: systemd unit / Dockerfile / Kubernetes manifests.

Примеры использования
- Внутренний вызов (пример): при интеграции с LLM модель может вызвать tool
  "add_note" и получить результат в JSON.
- HTTP/Transport: FastMCP поддерживает несколько транспортов; здесь по умолчанию
  используется SSE при запуске модуля напрямую.

Разработка и тестирование
- Для локальной разработки достаточно активировать виртуальное окружение и установить
  зависимости (`pip install fastmcp` и другие зависимости проекта).
- Рекомендуется добавить unit-тесты для каждой функции-инструмента и интеграционные
  тесты для транспорта.

"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastmcp import FastMCP

NOTES_HOST = os.getenv("NOTES_HOST", "0.0.0.0")
NOTES_PORT = int(os.getenv("NOTES_PORT", "8000"))

mcp = FastMCP("PersonalNotes")

NOTES_BY_ID: dict[int, dict] = {}
NEXT_ID = 1

@mcp.tool(description="Добавить заметку в блокнот")
def add_note(
    title: str,
    body: str,
    notebook: str | None = None,
    created_at: str | None = None,
) -> dict:
    """Создаёт новую заметку и сохраняет её в блокнот.

    Args:
        title: Заголовок заметки. Не может быть пустым.
        body: Текст заметки. Не может быть пустым.
        notebook: Имя блокнота. Если не указано, используется ``"scrapbook"``.
        created_at: Дата создания в формате ISO 8601 (``YYYY-MM-DDTHH:MM:SSZ``).
            Если не указана, используется текущее время UTC.

    Returns:
        Словарь с полями ``id``, ``notebook``, ``created_at``, ``title``, ``body``.

    Raises:
        ValueError: Если ``title`` или ``body`` пусты.
    """
    global NEXT_ID

    title = title.strip()
    body = body.strip()
    notebook = (notebook or "").strip() or "scrapbook"
    created_at = (created_at or "").strip() or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    if not title:
        raise ValueError("заголовок не должен быть пустым")
    if not body:
        raise ValueError("текст заметки не должен быть пустым")

    note = {
        "id": NEXT_ID,
        "notebook": notebook,
        "created_at": created_at,
        "title": title,
        "body": body,
    }
    NOTES_BY_ID[NEXT_ID] = note
    NEXT_ID += 1
    return note


@mcp.tool(description="Список заметок в блокноте или всех блокнотах")
def list_notes(notebook: str | None = None, limit: int = 100) -> dict:
    """Возвращает список заметок, отсортированных по дате (новые первыми).

    Args:
        notebook: Имя блокнота для фильтрации. Если не указано,
            возвращаются заметки из всех блокнотов.
        limit: Максимальное число возвращаемых заметок (по умолчанию 100).

    Returns:
        Словарь с ключами ``notes`` (список заметок) и ``count`` (их количество).

    Raises:
        ValueError: Если ``limit`` не является положительным числом.
    """
    if limit <= 0:
        raise ValueError("лимит должен быть положительным целым числом")

    notebook_filter = (notebook or "").strip()
    notes = list(NOTES_BY_ID.values())
    if notebook_filter:
        notes = [note for note in notes if note["notebook"] == notebook_filter]

    notes.sort(key=lambda n: (n["created_at"], n["id"]), reverse=True)
    notes = notes[:limit]
    return {"notes": notes, "count": len(notes)}


@mcp.tool(description="Получить последние n заметок из всех блокнотов")
def list_recent_notes(n: int = 10) -> dict:
    """Возвращает последние *n* заметок из всех блокнотов.

    Заметки сортируются по дате создания в обратном порядке.

    Args:
        n: Количество заметок для возврата (по умолчанию 10).

    Returns:
        Словарь с ключами ``notes`` (список заметок) и ``count`` (их количество).

    Raises:
        ValueError: Если ``n`` не является положительным числом.
    """
    if n <= 0:
        raise ValueError("n должно быть положительным целым числом")

    notes = list(NOTES_BY_ID.values())
    notes.sort(key=lambda n_: (n_["created_at"], n_["id"]), reverse=True)
    notes = notes[:n]
    return {"notes": notes, "count": len(notes)}


@mcp.tool(description="Поиск заметок по подстроке в заголовке/теле заметки")
def search_notes(query: str, notebook: str | None = None, limit: int = 100) -> dict:
    """Ищет заметки по подстроке в заголовке или теле (регистронезависимо).

    Args:
        query: Строка для поиска. Не может быть пустой.
        notebook: Имя блокнота для фильтрации. Если не указано,
            поиск выполняется по всем блокнотам.
        limit: Максимальное число возвращаемых результатов (по умолчанию 100).

    Returns:
        Словарь с ключами ``notes`` (список найденных заметок) и ``count``.

    Raises:
        ValueError: Если ``query`` пуст или ``limit`` не положителен.
    """
    query = query.strip()
    if not query:
        raise ValueError("запрос не должен быть пустым")
    if limit <= 0:
        raise ValueError("лимит должен быть положительным целым числом")

    query_lower = query.lower()
    notebook_filter = (notebook or "").strip()

    notes = list(NOTES_BY_ID.values())
    if notebook_filter:
        notes = [note for note in notes if note["notebook"] == notebook_filter]

    notes = [
        note
        for note in notes
        if query_lower in note["title"].lower() or query_lower in note["body"].lower()
    ]
    notes.sort(key=lambda n: (n["created_at"], n["id"]), reverse=True)
    notes = notes[:limit]
    return {"notes": notes, "count": len(notes)}


@mcp.tool(description="Удалить заметку по note_id")
def delete_note(note_id: int) -> dict:
    """Удаляет заметку по её идентификатору.

    Если заметка с указанным ``note_id`` не найдена, удаление не происходит,
    но ошибка не выбрасывается — в ответе ``deleted`` будет ``False``.

    Args:
        note_id: Идентификатор заметки для удаления.

    Returns:
        Словарь с ключами ``deleted`` (``True``/``False``) и ``note_id``.

    Raises:
        ValueError: Если ``note_id`` не является положительным числом.
    """
    if note_id <= 0:
        raise ValueError("note_id должен быть положительным целым числом")

    deleted = NOTES_BY_ID.pop(note_id, None) is not None
    return {"deleted": deleted, "note_id": note_id}


@mcp.tool(description="Переместить заметку в другой блокнот")
def move_note(note_id: int, to_notebook: str) -> dict:
    """Перемещает заметку в указанный блокнот.

    Args:
        note_id: Идентификатор заметки.
        to_notebook: Имя целевого блокнота. Не может быть пустым.

    Returns:
        Словарь с обновлёнными данными заметки.

    Raises:
        ValueError: Если ``note_id`` не положителен, ``to_notebook`` пуст
            или заметка с указанным ``note_id`` не найдена.
    """
    if note_id <= 0:
        raise ValueError("note_id должен быть положительным целым числом")

    to_notebook = to_notebook.strip()
    if not to_notebook:
        raise ValueError("to_notebook не должен быть пустым")

    note = NOTES_BY_ID.get(note_id)
    if note is None:
        raise ValueError(f"заметка с id={note_id} не найдена")

    note["notebook"] = to_notebook
    return note

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host=NOTES_HOST,
        port=NOTES_PORT,
    )