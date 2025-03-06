import database as db

class Pacchetto:
    def __init__(self, nome, descrizione, prezzo, numero_lezioni, durata_giorni):
        self.nome = nome
        self.descrizione = descrizione
        self.prezzo = prezzo
        self.numero_lezioni = numero_lezioni
        self.durata_giorni = durata_giorni

    def salva(self):
        return db.add_pacchetto(self.nome, self.descrizione, self.prezzo, self.numero_lezioni, self.durata_giorni)

    @staticmethod
    def get_pacchetto(pacchetto_id):
        return db.get_pacchetto(pacchetto_id)

    @staticmethod
    def get_all_pacchetti():
        return db.get_all_pacchetti()

# ... altre funzioni relative ai pacchetti se necessario ...
