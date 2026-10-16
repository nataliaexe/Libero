"""Libero - Tarefas e Remédios; armazena tarefas em arquivos JSON."""

import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DATA_DIR = Path.home() / "libero" / "data" / "tasks"
DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(DATA_DIR, 0o700)

_lock = Lock()


class TaskStore:
    def __init__(self):
        self.tasks = {}
        self._carregar()

    def _carregar(self):
        for arquivo in DATA_DIR.glob("*.json"):
            try:
                with open(arquivo, encoding="utf-8") as f:
                    dados = json.load(f)
                idoso_id = dados.get("idoso_id")
                if idoso_id:
                    self.tasks[idoso_id] = dados
            except (OSError, json.JSONDecodeError) as e:
                print(f"[Libero Tasks] Erro: {e}")

    def _salvar(self, idoso_id):
        self._validar_idoso(idoso_id)
        if idoso_id not in self.tasks:
            return
        arquivo = DATA_DIR / f"{idoso_id}.json"
        fd, temporario = tempfile.mkstemp(dir=DATA_DIR, prefix=".task-", suffix=".tmp")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.tasks[idoso_id], f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporario, arquivo)
        except Exception:
            try:
                os.unlink(temporario)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _validar_idoso(idoso_id):
        if not isinstance(idoso_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", idoso_id):
            raise ValueError("idoso_id inválido")

    def _init_idoso(self, idoso_id):
        self._validar_idoso(idoso_id)
        if idoso_id not in self.tasks:
            self.tasks[idoso_id] = {
                "idoso_id": idoso_id,
                "tasks": [],
                "criado_em": datetime.now(timezone.utc).isoformat(),
            }

    def listar(self, idoso_id):
        with _lock:
            self._init_idoso(idoso_id)
            return self.tasks[idoso_id]["tasks"]

    def criar(self, idoso_id, titulo, hora, tipo="remedio"):
        with _lock:
            self._init_idoso(idoso_id)
            task = {
                "id": str(uuid.uuid4())[:8],
                "titulo": titulo,
                "hora": hora,
                "tipo": tipo,
                "status": "pendente",
                "criado_em": datetime.now(timezone.utc).isoformat(),
            }
            self.tasks[idoso_id]["tasks"].append(task)
            self._salvar(idoso_id)
            return task

    def atualizar(self, idoso_id, task_id, status):
        with _lock:
            self._init_idoso(idoso_id)
            for task in self.tasks[idoso_id]["tasks"]:
                if task["id"] == task_id:
                    task["status"] = status
                    task["atualizado_em"] = datetime.now(timezone.utc).isoformat()
                    self._salvar(idoso_id)
                    return task
            return None

    def remover(self, idoso_id, task_id):
        with _lock:
            self._init_idoso(idoso_id)
            tarefas = self.tasks[idoso_id]["tasks"]
            self.tasks[idoso_id]["tasks"] = [t for t in tarefas if t["id"] != task_id]
            self._salvar(idoso_id)
            return True


_store = TaskStore()


def get_store():
    return _store
