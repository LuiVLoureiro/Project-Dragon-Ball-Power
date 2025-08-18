# db.py
from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Optional

import logging
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, ForeignKey,
    UniqueConstraint, Index, event
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.associationproxy import association_proxy

# -----------------------------------------------------------------------------
# Logging – mostra exatamente o que está acontecendo no terminal
# -----------------------------------------------------------------------------
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, stream=sys.stdout)
logger = logging.getLogger(__name__)

Base = declarative_base()

# ----------------------------------------------------------
# PRAGMA para garantir FKs no SQLite
# ----------------------------------------------------------
@event.listens_for(Engine, "connect")
def _enable_foreign_keys(dbapi_con, con_record):
    try:
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        logger.debug("PRAGMA foreign_keys=ON habilitado com sucesso.")
    except Exception as exc:
        # Não interrompe a execução, mas registra o problema
        logger.exception("Falha ao habilitar PRAGMA foreign_keys=ON: %s", exc)


# ===========================
# Dimensões
# ===========================
class Raca(Base):
    __tablename__ = "racas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)

    personagens = relationship("Personagem", back_populates="raca")

    def __repr__(self) -> str:
        return f"<Raca id={self.id} nome={self.nome!r}>"


class Tecnica(Base):
    __tablename__ = "tecnicas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)

    personagem_links = relationship("PersonagemTecnica", back_populates="tecnica",
                                    cascade="all, delete-orphan")

    # atalho de leitura (viewonly) para acessar personagens direto
    personagens = relationship(
        "Personagem",
        secondary="personagem_tecnicas",
        viewonly=True,
        back_populates="tecnicas",
    )

    def __repr__(self) -> str:
        return f"<Tecnica id={self.id} nome={self.nome!r}>"


class Transformacao(Base):
    __tablename__ = "transformacoes"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    nivel = Column(Integer)

    __table_args__ = (
        UniqueConstraint("nome", "nivel", name="uq_transformacoes_nome_nivel"),
    )

    personagem_links = relationship("PersonagemTransformacao", back_populates="transformacao",
                                    cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Transformacao id={self.id} nome={self.nome!r} nivel={self.nivel}>"


class Saga(Base):
    __tablename__ = "sagas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)

    personagem_sagas = relationship("PersonagemSaga", back_populates="saga",
                                    cascade="all, delete-orphan")
    transformacao_links = relationship("PersonagemTransformacao", back_populates="saga")

    def __repr__(self) -> str:
        return f"<Saga id={self.id} nome={self.nome!r}>"


# ===========================
# Entidade central
# ===========================
class Personagem(Base):
    __tablename__ = "personagem"
    id = Column(Integer, primary_key=True)
    nome = Column(Text, nullable=False)
    raca_id = Column(Integer, ForeignKey("racas.id"), nullable=False)
    poder_geral = Column(Float)  # opcional
    link = Column(Text, unique=True)  # URL do scraping

    raca = relationship("Raca", back_populates="personagens")

    # --- N:N com Técnicas
    tecnica_links = relationship(
        "PersonagemTecnica",
        back_populates="personagem",
        cascade="all, delete-orphan",
    )
    tecnicas = relationship(
        "Tecnica",
        secondary="personagem_tecnicas",
        viewonly=True,
        back_populates="personagens",
    )

    # --- N:N com Transformações (com saga)
    transformacao_links = relationship(
        "PersonagemTransformacao",
        back_populates="personagem",
        cascade="all, delete-orphan",
    )
    # atalho somente-leitura para acessar transformações diretamente
    transformacoes = association_proxy("transformacao_links", "transformacao")

    # --- N:N com Sagas (com atributo poder)
    saga_links = relationship(
        "PersonagemSaga",
        back_populates="personagem",
        cascade="all, delete-orphan",
    )
    sagas = association_proxy("saga_links", "saga")

    def __repr__(self) -> str:
        return f"<Personagem id={self.id} nome={self.nome!r} raca_id={self.raca_id}>"


# ===========================
# Junções N:N
# ===========================
class PersonagemTecnica(Base):
    __tablename__ = "personagem_tecnicas"
    personagem_id = Column(Integer, ForeignKey("personagem.id", ondelete="CASCADE"),
                           primary_key=True, nullable=False)
    tecnica_id = Column(Integer, ForeignKey("tecnicas.id", ondelete="CASCADE"),
                        primary_key=True, nullable=False)

    personagem = relationship("Personagem", back_populates="tecnica_links")
    tecnica = relationship("Tecnica", back_populates="personagem_links")

    def __repr__(self) -> str:
        return f"<PersonagemTecnica personagem_id={self.personagem_id} tecnica_id={self.tecnica_id}>"


class PersonagemTransformacao(Base):
    __tablename__ = "personagem_transformacoes"
    personagem_id = Column(Integer, ForeignKey("personagem.id", ondelete="CASCADE"),
                           primary_key=True, nullable=False)
    transformacao_id = Column(Integer, ForeignKey("transformacoes.id", ondelete="CASCADE"),
                              primary_key=True, nullable=False)
    saga_id = Column(Integer, ForeignKey("sagas.id", ondelete="CASCADE"),
                     primary_key=True, nullable=False)

    personagem = relationship("Personagem", back_populates="transformacao_links")
    transformacao = relationship("Transformacao", back_populates="personagem_links")
    saga = relationship("Saga", back_populates="transformacao_links")

    def __repr__(self) -> str:
        return (f"<PersonagemTransformacao personagem_id={self.personagem_id} "
                f"transformacao_id={self.transformacao_id} saga_id={self.saga_id}>")


class PersonagemSaga(Base):
    __tablename__ = "personagem_sagas"
    personagem_id = Column(Integer, ForeignKey("personagem.id", ondelete="CASCADE"),
                           primary_key=True, nullable=False)
    saga_id = Column(Integer, ForeignKey("sagas.id", ondelete="CASCADE"),
                     primary_key=True, nullable=False)
    poder = Column(Float)  # poder por saga
    power_unit = Column(Text)  # opcional

    personagem = relationship("Personagem", back_populates="saga_links")
    saga = relationship("Saga", back_populates="personagem_sagas")

    def __repr__(self) -> str:
        return f"<PersonagemSaga personagem_id={self.personagem_id} saga_id={self.saga_id} poder={self.poder}>"


# ===========================
# Índices (iguais aos do DDL)
# ===========================
Index("idx_personagem_raca", Personagem.raca_id)
Index("idx_pt_char", PersonagemTecnica.personagem_id)
Index("idx_pt_tech", PersonagemTecnica.tecnica_id)
Index("idx_ptr_char", PersonagemTransformacao.personagem_id)
Index("idx_ptr_transf", PersonagemTransformacao.transformacao_id)
Index("idx_ptr_saga", PersonagemTransformacao.saga_id)
Index("idx_ps_char", PersonagemSaga.personagem_id)
Index("idx_ps_saga", PersonagemSaga.saga_id)


# ===========================
# Helpers de engine/sessão com tratamento de erros
# ===========================
def _ensure_parent_dir(db_path: str) -> None:
    try:
        parent = Path(db_path).parent
        parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Diretório de dados garantido: %s", parent.resolve())
    except Exception as exc:
        logger.exception("Falha ao criar diretório de dados para %s: %s", db_path, exc)
        raise


def get_engine(db_path: str = "data/dragonball.db", echo: bool = False):
    """
    Cria o engine SQLite (com future=True) e garante a pasta do DB.
    """
    try:
        _ensure_parent_dir(db_path)
        url = f"sqlite:///{db_path}"
        logger.info("Criando engine para %s (echo=%s)...", url, echo)
        engine = create_engine(url, future=True, echo=echo)
        logger.debug("Engine criado com sucesso.")
        return engine
    except SQLAlchemyError as exc:
        logger.exception("Erro do SQLAlchemy ao criar engine: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Erro inesperado ao criar engine: %s", exc)
        raise


def create_schema(db_path: str = "data/dragonball.db", echo: bool = False):
    """
    Cria todas as tabelas conforme os modelos acima.
    """
    try:
        engine = get_engine(db_path, echo=echo)
        logger.info("Criando schema no banco %s ...", db_path)
        Base.metadata.create_all(engine)
        logger.info("Schema criado/atualizado com sucesso.")
        return engine
    except SQLAlchemyError as exc:
        logger.exception("Erro do SQLAlchemy ao criar schema: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Erro inesperado ao criar schema: %s", exc)
        raise


def get_session(db_path: str = "data/dragonball.db", echo: bool = False):
    """
    Retorna uma sessão já com o schema criado (se necessário).
    """
    try:
        engine = create_schema(db_path, echo=echo)
        logger.info("Abrindo sessão no banco: %s", db_path)
        SessionLocal = sessionmaker(bind=engine, autoflush=False)
        session = SessionLocal()
        logger.debug("Sessão aberta com sucesso.")
        return session
    except SQLAlchemyError as exc:
        logger.exception("Erro do SQLAlchemy ao abrir sessão: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Erro inesperado ao abrir sessão: %s", exc)
        raise


def safe_commit(session) -> None:
    """
    Faz commit com tratamento de erros e rollback automático.
    """
    try:
        logger.debug("Tentando commit...")
        session.commit()
        logger.info("Commit realizado com sucesso.")
    except IntegrityError as exc:
        logger.error("Violação de integridade (UNIQUE/FK/PK): %s", exc)
        logger.debug("Detalhes:\n%s", traceback.format_exc())
        session.rollback()
        logger.info("Rollback efetuado após erro de integridade.")
        raise
    except OperationalError as exc:
        logger.error("Erro operacional do banco (arquivo bloqueado/corrompido?): %s", exc)
        logger.debug("Detalhes:\n%s", traceback.format_exc())
        session.rollback()
        logger.info("Rollback efetuado após erro operacional.")
        raise
    except SQLAlchemyError as exc:
        logger.error("Erro SQLAlchemy no commit: %s", exc)
        logger.debug("Detalhes:\n%s", traceback.format_exc())
        session.rollback()
        logger.info("Rollback efetuado após erro SQLAlchemy.")
        raise
    except Exception as exc:
        logger.error("Erro inesperado no commit: %s", exc)
        logger.debug("Detalhes:\n%s", traceback.format_exc())
        session.rollback()
        logger.info("Rollback efetuado após erro inesperado.")
        raise


# -----------------------------------------------------------------------------
# Smoke test quando executado diretamente: cria schema e insere uma raça
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("== Iniciando smoke test do db.py ==")
        sess = get_session(echo=False)  # defina echo=True para ver SQL bruto
        # Inserção simples (idempotente): cria 'Saiyan' se não existir
        exists = sess.query(Raca).filter(Raca.nome == "Saiyan").first()
        if not exists:
            logger.info("Inserindo raça 'Saiyan'...")
            sess.add(Raca(nome="Saiyan"))
            safe_commit(sess)
        else:
            logger.info("Raça 'Saiyan' já existe (id=%s).", exists.id)

        logger.info("Listando raças no banco:")
        for r in sess.query(Raca).order_by(Raca.nome.asc()).all():
            logger.info(" - %s", r)

        sess.close()
        logger.info("== Smoke test finalizado com sucesso ==")
    except Exception as e:
        logger.exception("Falha no smoke test: %s", e)
        sys.exit(1)
