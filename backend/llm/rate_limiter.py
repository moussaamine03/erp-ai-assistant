import time
import threading

class RateLimiter:
    """
    Limite le nombre d'appels API par fenêtre de temps.
    Si la limite est atteinte, attend automatiquement.
    """
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls   # ex: 5 appels
        self.period    = period      # ex: 60 secondes
        self.calls     = []
        self.lock      = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            # Garder uniquement les appels dans la fenêtre actuelle
            self.calls = [t for t in self.calls if now - t < self.period]

            if len(self.calls) >= self.max_calls:
                # Calculer le temps d'attente nécessaire
                oldest = self.calls[0]
                wait_time = self.period - (now - oldest) + 0.5
                print(f"⏳ Rate limiter : attente {wait_time:.1f}s...")
                time.sleep(wait_time)
                # Nettoyer après attente
                now = time.time()
                self.calls = [t for t in self.calls if now - t < self.period]

            self.calls.append(time.time())


# Instance globale partagée — ajuste selon ton plan Mistral
# Plan gratuit ≈ 1 req/sec → on prend 1 appel toutes les 3s pour être safe
mistral_limiter = RateLimiter(max_calls=1, period=3.0)