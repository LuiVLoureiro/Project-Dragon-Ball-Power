from __future__ import annotations

import string
from urllib.parse import urljoin
from typing import Optional, List, Iterable

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# >>> importe tudo do SEU db.py (não recrie Base/engine aqui)
from dragonball.db import (
    get_session, safe_commit,
    Raca, Tecnica, Personagem, PersonagemTecnica,
)

BASE = "https://dragonball.fandom.com/"

# ---------------------------
# Helpers DB (upsert)
# ---------------------------
def upsert_raca(session, nome: Optional[str]) -> Optional[Raca]:
    if not nome:
        return None
    nome = nome.strip()
    r = session.query(Raca).filter(Raca.nome == nome).one_or_none()
    if r: 
        return r
    session.add(Raca(nome=nome))
    try:
        safe_commit(session)
    except Exception:
        # pode ser corrida por UNIQUE; tenta recuperar
        return session.query(Raca).filter(Raca.nome == nome).one()
    return session.query(Raca).filter(Raca.nome == nome).one()

def upsert_tecnica(session, nome: str) -> Tecnica:
    nome = nome.strip()
    t = session.query(Tecnica).filter(Tecnica.nome == nome).one_or_none()
    if t:
        return t
    session.add(Tecnica(nome=nome))
    try:
        safe_commit(session)
    except Exception:
        return session.query(Tecnica).filter(Tecnica.nome == nome).one()
    return session.query(Tecnica).filter(Tecnica.nome == nome).one()

def upsert_personagem(session, nome: str, raca: Optional[Raca], link: Optional[str]) -> Personagem:
    q = session.query(Personagem)
    p = None
    if link:
        p = q.filter(Personagem.link == link).one_or_none()
    if not p:
        p = q.filter(Personagem.nome == nome, Personagem.raca_id == (raca.id if raca else None)).one_or_none()

    if p:
        changed = False
        if raca and p.raca_id != raca.id:
            p.raca_id = raca.id; changed = True
        if link and not p.link:
            p.link = link; changed = True
        if changed:
            safe_commit(session)
        return p

    p = Personagem(nome=nome, raca_id=(raca.id if raca else None), link=link)
    session.add(p)
    safe_commit(session)
    return p

def link_tecnicas(session, personagem: Personagem, nomes: Iterable[str]) -> None:
    for nm in nomes:
        if not nm: 
            continue
        tec = upsert_tecnica(session, nm)
        exists = (
            session.query(PersonagemTecnica)
            .filter(PersonagemTecnica.personagem_id == personagem.id,
                    PersonagemTecnica.tecnica_id == tec.id)
            .one_or_none()
        )
        if not exists:
            session.add(PersonagemTecnica(personagem_id=personagem.id, tecnica_id=tec.id))
    safe_commit(session)

# ---------------------------
# Bot de scraping
# ---------------------------
class Bot():
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.session = get_session()  # <- usa data/dragonball.db do db.py

    # =========== EXTRAÇÃO ===========
    def extrair_personagens(self):
        characters_url = "wiki/Category:Characters?from="

        with sync_playwright() as p:
            nav = p.chromium.launch(headless=self.headless)
            page = nav.new_page()

            for letra in string.ascii_uppercase:
                page.goto(self.url(characters_url, letra))
                self._espera(page)
                soup = BeautifulSoup(page.content(), "html.parser")

                nomes = soup.find_all("a", class_="category-page__member-link")
                for a in nomes:
                    nome = (a.text or "").strip()
                    # ignora subcategorias
                    if not nome or nome.startswith("Category:"):
                        continue

                    # link absoluto da página do personagem
                    link_character = self.url(a.get("href") or "", "")

                    # visita a página do personagem
                    page.goto(link_character)
                    self._espera(page)
                    psoup = BeautifulSoup(page.content(), "html.parser")

                    # --- Raça
                    raca_nome = self._extrair_raca(psoup)

                    # --- Técnicas (heurística simples)
                    tecnicas = self._extrair_tecnicas_da_pagina(psoup)

                    # --- Persistência no SQLite
                    raca = upsert_raca(self.session, raca_nome)
                    personagem = upsert_personagem(self.session, nome, raca, link_character)
                    link_tecnicas(self.session, personagem, tecnicas)

                    print(f"[OK] {nome} | raça={raca_nome} | técnicas={len(tecnicas)} | {link_character}")

            nav.close()

    # =========== UTIL ===========
    def url(self, context, letter):
        # aceita caminho relativo, absoluto, e sufixo de letra
        if context.startswith(("http://", "https://")):
            return context
        return urljoin(BASE, f"{context}{letter}")

    def _espera(self, page):
        try:
            page.wait_for_load_state("networkidle", timeout=45000)
        except PWTimeout:
            pass  # segue mesmo assim; às vezes a página não estaciona

    # ======== parsers de página ========
    def _extrair_raca(self, soup: BeautifulSoup) -> Optional[str]:
        # 1) infobox com data-source="Race"
        for div in soup.find_all("div", {"data-source": "Race"}):
            val = div.find("div", class_="pi-data-value")
            if val:
                return val.get_text(" ", strip=True)
        # 2) fallback: rótulo "Race"
        for lab in soup.select(".pi-data .pi-data-label"):
            if "Race" in lab.get_text(strip=True):
                val = lab.find_next("div", class_="pi-data-value")
                if val:
                    return val.get_text(" ", strip=True)
        return None

    def _extrair_tecnicas_da_pagina(self, soup: BeautifulSoup) -> List[str]:
        """
        Procura seção 'Techniques/Abilities/Attacks' e coleta itens de listas/tabelas.
        (heurística suficiente p/ MVP)
        """
        import re
        def clean(x: str) -> str:
            x = re.sub(r"\(.*?\)", "", x)  # remove parênteses
            x = re.sub(r"\s+", " ", x)
            return x.strip()

        nomes: set[str] = set()
        heads = [h for h in soup.find_all(["h2", "h3", "h4"])
                 if any(k in h.get_text(" ", strip=True).lower() for k in ("technique", "abilities", "attacks"))]
        if not heads:
            return []

        head = heads[0]
        for sib in head.next_siblings:
            nm = getattr(sib, "name", None)
            if nm in ("h2", "h3", "h4"):  # próxima seção -> para
                break
            # listas
            for li in getattr(sib, "find_all", lambda *_: [])("li"):
                txt = (li.get_text(" ", strip=True) or "")
                if txt and len(txt) < 120:
                    nomes.add(clean(txt))
            # tabelas
            for tr in getattr(sib, "find_all", lambda *_: [])("tr"):
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if cells:
                    cand = cells[0]
                    if cand and len(cand) < 120:
                        nomes.add(clean(cand))

        return sorted(nomes)


# =========== Execução ===========
if __name__ == "__main__":
    bot = Bot(headless=True)
    bot.extrair_personagens()
