"""Accesso a Supabase dall'app: login con email/password e letture con il token dell'utente.

L'app usa SOLO la chiave pubblica (publishable/anon). Cosa può vedere ogni utente
lo decide il database (Row Level Security), non l'app.
"""

from __future__ import annotations

import time

import requests


class ErroreLogin(Exception):
    pass


class SessioneScaduta(Exception):
    pass


class Supa:
    def __init__(self, url: str, chiave_pubblica: str):
        self.url = url.rstrip("/")
        self.chiave = chiave_pubblica

    def _h(self, token: str | None = None) -> dict:
        h = {"apikey": self.chiave, "Content-Type": "application/json"}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    # -------------------------------------------------------------- autenticazione
    def _token(self, grant: str, corpo: dict) -> dict:
        r = requests.post(f"{self.url}/auth/v1/token", params={"grant_type": grant},
                          headers=self._h(), json=corpo, timeout=20)
        if r.status_code in (400, 401):
            raise ErroreLogin("Email o password non corretti")
        r.raise_for_status()
        d = r.json()
        return {"access_token": d["access_token"], "refresh_token": d["refresh_token"],
                "scade": time.time() + int(d.get("expires_in", 3600)) - 60,
                "user_id": d["user"]["id"], "email": d["user"].get("email", "")}

    def login(self, email: str, password: str) -> dict:
        return self._token("password", {"email": email.strip(), "password": password})

    def rinnova(self, sessione: dict) -> dict:
        try:
            return self._token("refresh_token", {"refresh_token": sessione["refresh_token"]})
        except Exception as e:
            raise SessioneScaduta() from e

    def logout(self, sessione: dict) -> None:
        try:
            requests.post(f"{self.url}/auth/v1/logout", headers=self._h(sessione["access_token"]), timeout=10)
        except Exception:
            pass

    # -------------------------------------------------------------- letture
    def leggi(self, token: str, tabella: str, params: dict) -> list[dict]:
        """GET con paginazione (Supabase restituisce al massimo 1000 righe per volta)."""
        righe, offset, passo = [], 0, 1000
        singola = "limit" in params                 # limite esplicito: una sola richiesta
        while True:
            p = dict(params) if singola else {**params, "limit": passo, "offset": offset}
            r = requests.get(f"{self.url}/rest/v1/{tabella}", params=p, headers=self._h(token), timeout=30)
            if r.status_code == 401:
                raise SessioneScaduta()
            r.raise_for_status()
            blocco = r.json()
            righe += blocco
            if singola or len(blocco) < passo:
                return righe
            offset += passo


    # -------------------------------------------------------------- scritture (solo admin, lo impone il database)
    def inserisci(self, token: str, tabella: str, righe: list[dict]) -> None:
        r = requests.post(f"{self.url}/rest/v1/{tabella}",
                          headers={**self._h(token), "Prefer": "resolution=ignore-duplicates,return=minimal"},
                          json=righe, timeout=30)
        if r.status_code == 401:
            raise SessioneScaduta()
        r.raise_for_status()

    def elimina(self, token: str, tabella: str, filtri: dict) -> None:
        r = requests.delete(f"{self.url}/rest/v1/{tabella}", params=filtri,
                            headers={**self._h(token), "Prefer": "return=minimal"}, timeout=30)
        if r.status_code == 401:
            raise SessioneScaduta()
        r.raise_for_status()


def filtro_in(valori: list[str]) -> str:
    """Filtro PostgREST "in" con valori tra virgolette (i nomi contengono spazi)."""
    return "in.(" + ",".join('"' + v.replace('"', '\\"') + '"' for v in valori) + ")"
