"""
Libero - Chat e Histórico
Armazena conversas entre idoso, Libero e cuidador.
"""

import os
import json
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX development platforms
    fcntl = None

DATA_DIR = Path.home() / "libero" / "data" / "chat"
DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(DATA_DIR, 0o700)

_lock = Lock()


class ChatStore:
    """Armazena conversas em memória + arquivo JSON."""
    
    def __init__(self):
        self.conversas = {}  # idoso_id -> {conversas: [...], mensagens: [...]}
        self._carregar()
    
    def _carregar(self):
        """Carrega conversas salvas em disco."""
        for arquivo in DATA_DIR.glob("*.json"):
            try:
                with open(arquivo, "r") as f:
                    dados = json.load(f)
                    idoso_id = dados.get("idoso_id")
                    if idoso_id:
                        self.conversas[idoso_id] = dados
            except Exception as e:
                print(f"[Libero Chat] Erro ao carregar {arquivo}: {e}")

    @contextmanager
    def _lock_arquivo(self):
        """Serialize edge and API processes writing the same local chat JSON."""
        if fcntl is None:
            yield
            return
        lock_path = DATA_DIR / ".chatstore.lock"
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _recarregar_idoso(self, idoso_id):
        """Refresh one resident from disk so long-running processes see each other."""
        self._validar_idoso(idoso_id)
        arquivo = DATA_DIR / f"{idoso_id}.json"
        try:
            with arquivo.open("r", encoding="utf-8") as handle:
                dados = json.load(handle)
            if dados.get("idoso_id") == idoso_id:
                self.conversas[idoso_id] = dados
        except FileNotFoundError:
            self.conversas.pop(idoso_id, None)
        except Exception as e:
            print(f"[Libero Chat] Erro ao atualizar {arquivo}: {e}")
    
    def _salvar(self, idoso_id):
        """Salva conversas em disco."""
        self._validar_idoso(idoso_id)
        if idoso_id not in self.conversas:
            return
        arquivo = DATA_DIR / f"{idoso_id}.json"
        fd, temporario = tempfile.mkstemp(dir=DATA_DIR, prefix=".chat-", suffix=".tmp")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.conversas[idoso_id], f, ensure_ascii=False, indent=2)
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
        if idoso_id not in self.conversas:
            self.conversas[idoso_id] = {
                "idoso_id": idoso_id,
                "conversas": [],  # lista de conversas (sessões)
                "mensagens": [],   # todas as mensagens
                "criado_em": datetime.now(timezone.utc).isoformat()
            }
    
    def adicionar_mensagem(self, idoso_id, autor, texto, tipo="normal", metadata=None):
        """
        Adiciona uma mensagem.
        
        Args:
            idoso_id: ID do idoso
            autor: "idoso", "libero" ou "cuidador"
            texto: conteúdo da mensagem
            tipo: "normal", "memoria", "emergencia"
            metadata: dict com dados extras
        """
        with _lock, self._lock_arquivo():
            self._recarregar_idoso(idoso_id)
            self._init_idoso(idoso_id)

            msg = {
                "id": str(uuid.uuid4())[:8],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "autor": autor,
                "texto": texto,
                "tipo": tipo,
                "metadata": metadata or {}
            }

            self.conversas[idoso_id]["mensagens"].append(msg)

            # Limitar a 1000 mensagens por idoso
            if len(self.conversas[idoso_id]["mensagens"]) > 1000:
                self.conversas[idoso_id]["mensagens"] = \
                    self.conversas[idoso_id]["mensagens"][-1000:]

            self._salvar(idoso_id)
            return msg
    
    def listar_mensagens(self, idoso_id, limite=50, offset=0):
        """Lista mensagens com paginação."""
        with _lock, self._lock_arquivo():
            self._recarregar_idoso(idoso_id)
            self._init_idoso(idoso_id)
            mensagens = list(self.conversas[idoso_id]["mensagens"])

        # Ordenar por timestamp (mais recente primeiro)
        mensagens_ordenadas = sorted(
            mensagens,
            key=lambda m: m["timestamp"],
            reverse=True
        )
        
        return mensagens_ordenadas[offset:offset + limite]
    
    def listar_memorias(self, idoso_id):
        """Lista apenas mensagens do tipo memória."""
        with _lock, self._lock_arquivo():
            self._recarregar_idoso(idoso_id)
            self._init_idoso(idoso_id)
            mensagens = list(self.conversas[idoso_id]["mensagens"])
        return [m for m in mensagens if m.get("tipo") == "memoria"]
    
    def listar_emergencias(self, idoso_id):
        """Lista apenas emergências."""
        with _lock, self._lock_arquivo():
            self._recarregar_idoso(idoso_id)
            self._init_idoso(idoso_id)
            mensagens = list(self.conversas[idoso_id]["mensagens"])
        return [m for m in mensagens if m.get("tipo") == "emergencia"]
    
    def estatisticas(self, idoso_id):
        """Estatísticas do chat."""
        with _lock, self._lock_arquivo():
            self._recarregar_idoso(idoso_id)
            self._init_idoso(idoso_id)
            mensagens = list(self.conversas[idoso_id]["mensagens"])
        
        return {
            "total_mensagens": len(mensagens),
            "total_memorias": len([m for m in mensagens if m["tipo"] == "memoria"]),
            "total_emergencias": len([m for m in mensagens if m["tipo"] == "emergencia"]),
            "ultima_mensagem": mensagens[-1] if mensagens else None
        }


# Instância global
_store = ChatStore()


def get_store():
    return _store
