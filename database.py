import sqlite3
import os
from datetime import datetime, timedelta

DATABASE_PATH = "gym_manager.db"

def get_db_connection():
    """Crea una connessione al database"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    """Inizializza il database con le tabelle necessarie"""
    if os.path.exists(DATABASE_PATH):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Creazione tabella clienti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT,
        telefono TEXT,
        data_nascita TEXT,
        indirizzo TEXT,
        citta TEXT,
        cap TEXT,
        note TEXT,
        tipo TEXT NOT NULL,  -- 'lead' o 'effettivo'
        data_registrazione TEXT NOT NULL
    )
    ''')
    
    # Creazione tabella pacchetti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacchetti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descrizione TEXT,
        prezzo REAL NOT NULL,
        numero_lezioni INTEGER NOT NULL,
        durata_giorni INTEGER NOT NULL,
        attivo BOOLEAN NOT NULL DEFAULT 1
    )
    ''')
    
    # Creazione tabella abbonamenti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS abbonamenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        pacchetto_id INTEGER NOT NULL,
        data_inizio DATE NOT NULL,
        data_fine DATE NOT NULL,
        numero_lezioni INTEGER NOT NULL,
        lezioni_utilizzate INTEGER DEFAULT 0,
        prezzo_totale DECIMAL(10,2) NOT NULL,
        numero_rate INTEGER DEFAULT 1,
        FOREIGN KEY (cliente_id) REFERENCES clienti (id),
        FOREIGN KEY (pacchetto_id) REFERENCES pacchetti (id)
    )
    ''')
    
    # Creazione tabella rate
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbonamento_id INTEGER NOT NULL,
        importo DECIMAL(10,2) NOT NULL,
        data_scadenza DATE NOT NULL,
        data_pagamento DATE,
        pagato BOOLEAN DEFAULT 0,
        numero_rata INTEGER NOT NULL,
        FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti (id)
    )
    ''')
    
    # Creazione tabella lezioni
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lezioni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbonamento_id INTEGER NOT NULL,
        data DATE NOT NULL,
        note TEXT,
        registrata_da INTEGER DEFAULT 1,
        FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti (id),
        FOREIGN KEY (registrata_da) REFERENCES utenti (id)
    )
    ''')
    
    # Creazione tabella utenti
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS utenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        ruolo TEXT NOT NULL DEFAULT 'staff',
        attivo BOOLEAN NOT NULL DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Inserimento di dati di esempio per i pacchetti
    cursor.execute('''
    INSERT INTO pacchetti (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo)
    VALUES 
        ('Base', 'Pacchetto base con 10 lezioni', 300.00, 10, 60, 1),
        ('Intermedio', 'Pacchetto intermedio con 20 lezioni', 500.00, 20, 90, 1),
        ('Avanzato', 'Pacchetto avanzato con 30 lezioni', 700.00, 30, 120, 1)
    ''')
    
    # Inserisci un utente admin di default se non esiste
    admin_exists = conn.execute(
        "SELECT 1 FROM utenti WHERE email = 'admin@gym.com'").fetchone()
    if not admin_exists:
        conn.execute('''
        INSERT INTO utenti (nome, cognome, email, password, ruolo)
        VALUES ('Admin', 'System', 'admin@gym.com', 'admin123', 'admin')
        ''')

    conn.commit()
    conn.close()
    
    print("Database inizializzato con successo!")

# Funzioni di utilità per i clienti
def get_all_clienti():
    conn = get_db_connection()
    clienti = conn.execute('SELECT * FROM clienti ORDER BY cognome, nome').fetchall()
    conn.close()
    return clienti

def get_cliente(cliente_id):
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clienti WHERE id = ?', (cliente_id,)).fetchone()
    conn.close()
    return cliente

def get_leads():
    conn = get_db_connection()
    leads = conn.execute("SELECT * FROM clienti WHERE tipo = 'lead' ORDER BY cognome, nome").fetchall()
    conn.close()
    return leads

def get_clienti_effettivi():
    conn = get_db_connection()
    clienti = conn.execute("SELECT * FROM clienti WHERE tipo = 'effettivo' ORDER BY cognome, nome").fetchall()
    conn.close()
    return clienti

def add_cliente(nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_registrazione = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute('''
    INSERT INTO clienti (nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, data_registrazione)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, data_registrazione))
    
    conn.commit()
    cliente_id = cursor.lastrowid
    conn.close()
    return cliente_id

def update_cliente(cliente_id, nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo):
    conn = get_db_connection()
    conn.execute('''
    UPDATE clienti 
    SET nome = ?, cognome = ?, email = ?, telefono = ?, data_nascita = ?, 
        indirizzo = ?, citta = ?, cap = ?, note = ?, tipo = ?
    WHERE id = ?
    ''', (nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, cliente_id))
    
    conn.commit()
    conn.close()

def delete_cliente(cliente_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM clienti WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()

# Funzioni di utilità per i pacchetti
def get_all_pacchetti():
    conn = get_db_connection()
    pacchetti = conn.execute('SELECT * FROM pacchetti ORDER BY nome').fetchall()
    conn.close()
    return pacchetti

def get_pacchetto(pacchetto_id):
    conn = get_db_connection()
    pacchetto = conn.execute('SELECT * FROM pacchetti WHERE id = ?', (pacchetto_id,)).fetchone()
    conn.close()
    return pacchetto

def add_pacchetto(nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO pacchetti (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo))
    
    conn.commit()
    pacchetto_id = cursor.lastrowid
    conn.close()
    return pacchetto_id

def update_pacchetto(pacchetto_id, nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo):
    conn = get_db_connection()
    conn.execute('''
    UPDATE pacchetti 
    SET nome = ?, descrizione = ?, prezzo = ?, numero_lezioni = ?, durata_giorni = ?, attivo = ?
    WHERE id = ?
    ''', (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pacchetto_id))
    
    conn.commit()
    conn.close()
    return pacchetto_id


# Funzioni per gli abbonamenti
def create_abbonamento(cliente_id, pacchetto_id, data_inizio, prezzo_totale, numero_rate=1):
    conn = get_db_connection()
    try:
        # Ottieni informazioni sul pacchetto
        pacchetto = get_pacchetto(pacchetto_id)
        if not pacchetto:
            return False
        
        # Inserisci l'abbonamento
        cursor = conn.execute('''
            INSERT INTO abbonamenti (
                cliente_id, 
                pacchetto_id, 
                data_inizio, 
                data_fine,
                numero_lezioni,
                lezioni_utilizzate,
                prezzo_totale,
                numero_rate
            ) VALUES (?, ?, ?, date(?, '+' || ? || ' days'), ?, 0, ?, ?)
        ''', (
            cliente_id, 
            pacchetto_id, 
            data_inizio, 
            data_inizio,
            pacchetto['durata_giorni'],
            pacchetto['numero_lezioni'],
            prezzo_totale,
            numero_rate
        ))
        
        abbonamento_id = cursor.lastrowid
        
        # Crea le rate
        importo_rata = prezzo_totale / numero_rate
        for i in range(numero_rate):
            # Calcola la data di scadenza della rata (ogni 30 giorni)
            data_scadenza = conn.execute(
                "SELECT date(?, '+' || ? || ' days')",
                (data_inizio, (i + 1) * 30)
            ).fetchone()[0]
            
            # Inserisci la rata
            conn.execute('''
                INSERT INTO rate (
                    abbonamento_id,
                    importo,
                    data_scadenza,
                    pagato,
                    numero_rata
                ) VALUES (?, ?, ?, 0, ?)
            ''', (abbonamento_id, importo_rata, data_scadenza, i + 1))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Errore durante la creazione dell'abbonamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_rate_scadenza():
    conn = get_db_connection()
    try:
        rate = conn.execute('''
            SELECT 
                r.*,
                c.nome || ' ' || c.cognome as nome_cliente,
                c.id as cliente_id,
                p.nome as tipo_pacchetto,
                a.id as abbonamento_id
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE r.pagato = 0
            ORDER BY r.data_scadenza ASC
        ''').fetchall()
        return rate
    finally:
        conn.close()

def get_rate_incassate_mese():
    mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    mese_fine = mese_fine.strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    try:
        rate = conn.execute('''
            SELECT 
                r.*,
                c.nome || ' ' || c.cognome AS nome_cliente,
                c.id AS cliente_id,
                p.nome AS tipo_pacchetto,
                a.id AS abbonamento_id
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE data_pagamento BETWEEN ? AND ? AND pagato = 1
            ORDER BY r.data_scadenza ASC;
        ''',(mese_inizio, mese_fine)).fetchall()
        return rate
    finally:
        conn.close()

def get_rate_calendario(mese=None, anno=None):
    conn = get_db_connection()
    try:
        query = '''
            SELECT 
                r.data_scadenza,
                COUNT(r.id) as rate_da_pagare,
                GROUP_CONCAT(c.nome || ' ' || c.cognome) as clienti,
                GROUP_CONCAT(c.id) as clienti_ids
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            WHERE r.pagato = 0
        '''
        params = []
        
        if mese and anno:
            query += ''' 
                AND strftime('%Y-%m', r.data_scadenza) = ?
            '''
            params.append(f"{anno:04d}-{mese:02d}")
        
        query += '''
            GROUP BY r.data_scadenza
            ORDER BY r.data_scadenza ASC
        '''
        
        scadenze = conn.execute(query, params).fetchall()
        # Convertiamo i risultati in dizionari con le chiavi corrette
        return [dict(row) for row in scadenze]
    finally:
        conn.close()

def paga_rata(rata_id):
    conn = get_db_connection()
    data_pagamento = datetime.now().strftime("%Y-%m-%d")
    
    conn.execute('''
    UPDATE rate SET pagato = 1, data_pagamento = ? WHERE id = ?
    ''', (data_pagamento, rata_id))
    
    conn.commit()
    conn.close()

def get_abbonamenti_by_cliente(cliente_id):
    conn = get_db_connection()
    try:
        abbonamenti = conn.execute('''
            SELECT 
                a.*,
                p.nome as nome_pacchetto,
                (SELECT COUNT(*) FROM rate r WHERE r.abbonamento_id = a.id AND r.pagato = 1) as rate_pagate
            FROM abbonamenti a
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE a.cliente_id = ?
            ORDER BY a.data_inizio DESC
        ''', (cliente_id,)).fetchall()
        return abbonamenti
    finally:
        conn.close()

def get_rate_by_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        rate = conn.execute('''
            SELECT 
                r.*,
                r.importo as importo_rata,
                r.data_scadenza,
                r.data_pagamento,
                r.pagato,
                r.numero_rata
            FROM rate r
            WHERE r.abbonamento_id = ?
            ORDER BY r.numero_rata ASC
        ''', (abbonamento_id,)).fetchall()
        return rate
    finally:
        conn.close()

def get_lezioni_abbonamento(abbonamento_id):
    conn = get_db_connection()
    lezioni = conn.execute('''
    SELECT * FROM lezioni
    WHERE abbonamento_id = ?
    ORDER BY data, ora_inizio
    ''', (abbonamento_id,)).fetchall()
    
    conn.close()
    return lezioni

def add_lezione(abbonamento_id, data, ora_inizio, ora_fine, note):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO lezioni (abbonamento_id, data, ora_inizio, ora_fine, note, completata)
    VALUES (?, ?, ?, ?, ?, 0)
    ''', (abbonamento_id, data, ora_inizio, ora_fine, note))
    
    conn.commit()
    lezione_id = cursor.lastrowid
    conn.close()
    return lezione_id

def completa_lezione(lezione_id):
    conn = get_db_connection()
    conn.execute('''
    UPDATE lezioni SET completata = 1 WHERE id = ?
    ''', (lezione_id,))
    
    # Aggiorna il contatore delle lezioni utilizzate
    cursor = conn.cursor()
    lezione = cursor.execute('SELECT abbonamento_id FROM lezioni WHERE id = ?', (lezione_id,)).fetchone()
    
    cursor.execute('''
    UPDATE abbonamenti 
    SET lezioni_utilizzate = lezioni_utilizzate + 1
    WHERE id = ?
    ''', (lezione['abbonamento_id'],))
    
    conn.commit()
    conn.close()

# Funzioni per la dashboard
def get_statistiche_dashboard():
    conn = get_db_connection()
    oggi = datetime.now().strftime("%Y-%m-%d")

    stats = {}
    
    # Numero totale di clienti
    stats['totale_clienti'] = conn.execute("SELECT COUNT(*) FROM clienti WHERE tipo = 'effettivo'").fetchone()[0]
    
    # Numero di leads
    stats['totale_leads'] = conn.execute("SELECT COUNT(*) FROM clienti WHERE tipo = 'lead'").fetchone()[0]
    
    # Numero di abbonamenti attivi
    oggi = datetime.now().strftime("%Y-%m-%d")
    stats['abbonamenti_attivi'] = conn.execute(
        "SELECT COUNT(*) FROM abbonamenti WHERE data_fine >= ?", (oggi,)).fetchone()[0]
    
    # Rate in scadenza oggi
    stats['rate_oggi'] = conn.execute(
        "SELECT COUNT(*) FROM rate WHERE data_scadenza = ? AND pagato = 0", (oggi,)).fetchone()[0]
    
    # Rate scadute non pagate
    stats['rate_scadute'] = conn.execute(
        "SELECT COUNT(*) FROM rate WHERE data_scadenza < ? AND pagato = 0", (oggi,)).fetchone()[0]
    
    stats['rate_scadute_importo'] = conn.execute(
        "SELECT SUM(importo) FROM rate WHERE data_scadenza < ? AND pagato = 0", (oggi,)).fetchone()[0]
    
    # Incassi del mese corrente
    mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    mese_fine = mese_fine.strftime("%Y-%m-%d")
    
    stats['incassi_mese'] = conn.execute(
        "SELECT SUM(importo) FROM rate WHERE data_pagamento BETWEEN ? AND ? AND pagato = 1",
        (mese_inizio, mese_fine)).fetchone()[0] or 0
    
    stats['previsione_mese'] = conn.execute(
        "SELECT SUM(importo) FROM rate WHERE data_scadenza BETWEEN ? AND ? AND pagato = 0",
        (mese_inizio, mese_fine)).fetchone()[0] or 0
    
    # Get the first day of next month
    prossimo_mese_inizio_dt = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
    prossimo_mese_inizio = prossimo_mese_inizio_dt.strftime("%Y-%m-%d")

    # Get the last day of next month
    prossimo_mese_fine_dt = (prossimo_mese_inizio_dt + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    prossimo_mese_fine = prossimo_mese_fine_dt.strftime("%Y-%m-%d")
    
    stats['previsione_mese_prossimo'] = conn.execute(
        "SELECT SUM(importo) FROM rate WHERE data_scadenza BETWEEN ? AND ? AND pagato = 0",
        (prossimo_mese_inizio, prossimo_mese_fine)).fetchone()[0] or 0
    
    # Prossime scadenze
    prossime_scadenze = conn.execute("""
        SELECT r.*, c.id as cliente_id, c.nome as cliente_nome, c.cognome as cliente_cognome,
               p.nome as descrizione, a.numero_rate
        FROM rate r
        JOIN abbonamenti a ON r.abbonamento_id = a.id
        JOIN clienti c ON a.cliente_id = c.id
        JOIN pacchetti p ON a.pacchetto_id = p.id                         
        WHERE r.pagato = 0
        ORDER BY r.data_scadenza 
        
    """).fetchall()

    
    stats['prossime_scadenze'] = prossime_scadenze
    
    conn.close()
    return stats

def get_scadenze_calendario():
    conn = get_db_connection()
    oggi = datetime.now().strftime("%Y-%m-%d")
    un_mese_dopo = datetime.now().replace(month=datetime.now().month + 1).strftime("%Y-%m-%d")
    
    query = '''
    SELECT r.id, r.data_scadenza, r.importo, c.nome, c.cognome
    FROM rate r
    JOIN abbonamenti a ON r.abbonamento_id = a.id
    JOIN clienti c ON a.cliente_id = c.id
    WHERE r.data_scadenza BETWEEN ? AND ?
    AND r.pagato = 0
    ORDER BY r.data_scadenza
    '''
    
    scadenze = conn.execute(query, (oggi, un_mese_dopo)).fetchall()
    conn.close()
    
    # Organizza le scadenze per data
    calendario = {}
    for scadenza in scadenze:
        data = scadenza['data_scadenza']
        if data not in calendario:
            calendario[data] = []
        calendario[data].append({
            'id': scadenza['id'],
            'cliente': f"{scadenza['nome']} {scadenza['cognome']}",
            'importo': scadenza['importo']
        })
    
    return calendario

def get_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        abbonamento = conn.execute('''
            SELECT 
                a.*,
                p.nome as tipo,
                p.descrizione as descrizione_pacchetto,
                p.numero_lezioni as numero_lezioni_pacchetto,
                p.durata_giorni,
                date(a.data_inizio, '+' || p.durata_giorni || ' days') as data_fine
            FROM abbonamenti a
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE a.id = ?
        ''', (abbonamento_id,)).fetchone()
        
        return abbonamento
    finally:
        conn.close()

def get_lezioni_by_cliente(cliente_id):
    conn = get_db_connection()
    lezioni = conn.execute('''
        SELECT l.*,
               p.nome as tipo,
               'Admin' as registrata_da_nome  -- Valore predefinito per ora
        FROM lezioni l
        JOIN abbonamenti a ON l.abbonamento_id = a.id
        JOIN pacchetti p ON a.pacchetto_id = p.id
        WHERE a.cliente_id = ?
        ORDER BY l.data DESC
    ''', (cliente_id,)).fetchall()
    conn.close()
    return lezioni

def get_lezioni_by_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        lezioni = conn.execute('''
            SELECT 
                l.*,
                COALESCE(u.nome || ' ' || u.cognome, 'Sistema') as registrata_da_nome
            FROM lezioni l
            LEFT JOIN utenti u ON l.registrata_da = u.id
            WHERE l.abbonamento_id = ?
            ORDER BY l.data DESC
        ''', (abbonamento_id,)).fetchall()
        return lezioni
    finally:
        conn.close()

def registra_lezione(abbonamento_id, data, note):
    conn = get_db_connection()
    try:
        # Verifica se l'abbonamento esiste e ha lezioni disponibili
        abbonamento = get_abbonamento(abbonamento_id)
        if not abbonamento:
            return False
        
        if abbonamento['lezioni_utilizzate'] >= abbonamento['numero_lezioni']:
            return False
        
        # Inserisci la nuova lezione con il campo registrata_da
        cursor = conn.execute('''
            INSERT INTO lezioni (abbonamento_id, data, note, registrata_da)
            VALUES (?, ?, ?, 1)
        ''', (abbonamento_id, data, note))
        
        # Aggiorna il conteggio delle lezioni utilizzate
        conn.execute('''
            UPDATE abbonamenti
            SET lezioni_utilizzate = lezioni_utilizzate + 1
            WHERE id = ?
        ''', (abbonamento_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Errore durante la registrazione della lezione: {e}")
        return False
    finally:
        conn.close()

def incrementa_lezioni_utilizzate(abbonamento_id):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE abbonamenti 
            SET lezioni_utilizzate = lezioni_utilizzate + 1
            WHERE id = ?
        ''', (abbonamento_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento delle lezioni utilizzate: {e}")
        return False
    finally:
        conn.close()

def migrate_lezioni_table():
    conn = get_db_connection()
    try:
        # Crea una tabella temporanea con la nuova struttura
        conn.execute('''
            CREATE TABLE lezioni_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abbonamento_id INTEGER NOT NULL,
                data DATE NOT NULL,
                note TEXT,
                registrata_da INTEGER DEFAULT 1,
                FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti (id),
                FOREIGN KEY (registrata_da) REFERENCES utenti (id)
            )
        ''')
        
        # Copia i dati esistenti
        conn.execute('''
            INSERT INTO lezioni_new (id, abbonamento_id, data, note)
            SELECT id, abbonamento_id, data, note FROM lezioni
        ''')
        
        # Elimina la vecchia tabella
        conn.execute('DROP TABLE lezioni')
        
        # Rinomina la nuova tabella
        conn.execute('ALTER TABLE lezioni_new RENAME TO lezioni')
        
        conn.commit()
        print("Migrazione completata con successo")
        
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_statistiche_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        # Ottieni il numero di abbonamenti attivi
        abbonamenti_attivi = conn.execute('''
            SELECT COUNT(*) as count
            FROM abbonamenti
            WHERE pacchetto_id = ? AND data_fine >= date('now')
        ''', (pacchetto_id,)).fetchone()['count']

        # Ottieni il numero totale di abbonamenti
        totale_abbonamenti = conn.execute('''
            SELECT COUNT(*) as count
            FROM abbonamenti
            WHERE pacchetto_id = ?
        ''', (pacchetto_id,)).fetchone()['count']

        # Calcola l'incasso totale
        incasso_totale = conn.execute('''
            SELECT COALESCE(SUM(prezzo_totale), 0) as total
            FROM abbonamenti
            WHERE pacchetto_id = ?
        ''', (pacchetto_id,)).fetchone()['total']

        return {
            'abbonamenti_attivi': abbonamenti_attivi,
            'totale_abbonamenti': totale_abbonamenti,
            'incasso_totale': incasso_totale
        }

    finally:
        conn.close()

def get_vendite_mensili_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        # Ottieni le vendite degli ultimi 6 mesi
        vendite = conn.execute('''
            SELECT 
                strftime('%Y-%m', data_inizio) as mese,
                COUNT(*) as vendite
            FROM abbonamenti
            WHERE pacchetto_id = ?
            AND data_inizio >= date('now', '-6 months')
            GROUP BY mese
            ORDER BY mese ASC
        ''', (pacchetto_id,)).fetchall()

        # Prepara i dati per il grafico
        mesi = []
        vendite_mensili = []
        
        # Converti i nomi dei mesi in italiano
        mesi_ita = {
            '01': 'Gennaio', '02': 'Febbraio', '03': 'Marzo',
            '04': 'Aprile', '05': 'Maggio', '06': 'Giugno',
            '07': 'Luglio', '08': 'Agosto', '09': 'Settembre',
            '10': 'Ottobre', '11': 'Novembre', '12': 'Dicembre'
        }

        for v in vendite:
            anno, mese = v['mese'].split('-')
            mesi.append(f"{mesi_ita[mese]} {anno}")
            vendite_mensili.append(v['vendite'])

        return mesi, vendite_mensili

    finally:
        conn.close()

def get_abbonamenti_by_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        abbonamenti = conn.execute('''
            SELECT 
                a.id,
                a.cliente_id,
                a.data_inizio,
                a.data_fine,
                c.nome || ' ' || c.cognome as nome_cliente
            FROM abbonamenti a
            JOIN clienti c ON a.cliente_id = c.id
            WHERE a.pacchetto_id = ?
            ORDER BY a.data_inizio DESC
            LIMIT 10
        ''', (pacchetto_id,)).fetchall()
        
        return abbonamenti

    finally:
        conn.close()

def registra_pagamento_rata(rata_id, data_pagamento):
    conn = get_db_connection()
    try:
        # Aggiorna lo stato della rata
        conn.execute('''
            UPDATE rate 
            SET pagato = 1,
                data_pagamento = ?
            WHERE id = ?
        ''', (data_pagamento, rata_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la registrazione del pagamento: {e}")
        return False
    finally:
        conn.close()

def get_rata(rata_id):
    conn = get_db_connection()
    try:
        rata = conn.execute('''
            SELECT r.*,
                   a.cliente_id,
                   c.nome || ' ' || c.cognome as nome_cliente,
                   p.nome as tipo_pacchetto
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            JOIN pacchetti p ON a.pacchetto_id = p.id
            WHERE r.id = ?
        ''', (rata_id,)).fetchone()
        return rata
    finally:
        conn.close()

def migrate_abbonamenti():
    conn = get_db_connection()
    try:
        # Verifica se la colonna esiste già
        columns = conn.execute("PRAGMA table_info(abbonamenti)").fetchall()
        if not any(col[1] == 'numero_rate' for col in columns):
            # Aggiungi la colonna numero_rate
            conn.execute('ALTER TABLE abbonamenti ADD COLUMN numero_rate INTEGER DEFAULT 1')
            conn.commit()
            print("Migrazione completata con successo")
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
    finally:
        conn.close()

def migrate_database():
    conn = get_db_connection()
    try:
        # Verifica e aggiunge la colonna numero_rate in abbonamenti
        columns_abbonamenti = conn.execute("PRAGMA table_info(abbonamenti)").fetchall()
        if not any(col[1] == 'numero_rate' for col in columns_abbonamenti):
            conn.execute('ALTER TABLE abbonamenti ADD COLUMN numero_rate INTEGER DEFAULT 1')
            print("Aggiunta colonna numero_rate alla tabella abbonamenti")

        # Verifica e aggiunge la colonna numero_rata in rate
        columns_rate = conn.execute("PRAGMA table_info(rate)").fetchall()
        if not any(col[1] == 'numero_rata' for col in columns_rate):
            # In SQLite non possiamo aggiungere una colonna NOT NULL con un valore di default
            # quindi dobbiamo ricreare la tabella
            conn.execute('''
                CREATE TABLE rate_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    abbonamento_id INTEGER NOT NULL,
                    importo DECIMAL(10,2) NOT NULL,
                    data_scadenza DATE NOT NULL,
                    data_pagamento DATE,
                    pagato BOOLEAN DEFAULT 0,
                    numero_rata INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti (id)
                )
            ''')
            
            # Copia i dati esistenti
            conn.execute('''
                INSERT INTO rate_new (id, abbonamento_id, importo, data_scadenza, 
                                    data_pagamento, pagato, numero_rata)
                SELECT id, abbonamento_id, importo, data_scadenza, 
                       data_pagamento, pagato, 1
                FROM rate
            ''')
            
            # Elimina la vecchia tabella e rinomina la nuova
            conn.execute('DROP TABLE rate')
            conn.execute('ALTER TABLE rate_new RENAME TO rate')
            print("Aggiunta colonna numero_rata alla tabella rate")

        # Verifica se la tabella utenti esiste
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='utenti'"
        ).fetchall()
        
        if not any(table['name'] == 'utenti' for table in tables):
            # Crea la tabella utenti
            conn.execute('''
            CREATE TABLE utenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cognome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                ruolo TEXT NOT NULL DEFAULT 'staff',
                attivo BOOLEAN NOT NULL DEFAULT 1,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Inserisci un utente admin di default
            conn.execute('''
            INSERT INTO utenti (nome, cognome, email, password, ruolo)
            VALUES ('Admin', 'System', 'admin@gym.com', 'admin123', 'admin')
            ''')

            print("Tabella utenti creata con successo")

        conn.commit()
        print("Migrazione completata con successo")
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_abbonamento(abbonamento_id):
    conn = get_db_connection()
    try:
        # Prima elimina tutte le rate associate
        conn.execute('DELETE FROM rate WHERE abbonamento_id = ?', (abbonamento_id,))
        
        # Poi elimina tutte le lezioni associate
        conn.execute('DELETE FROM lezioni WHERE abbonamento_id = ?', (abbonamento_id,))
        
        # Infine elimina l'abbonamento
        conn.execute('DELETE FROM abbonamenti WHERE id = ?', (abbonamento_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'eliminazione dell'abbonamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def promuovi_cliente(cliente_id):
    conn = get_db_connection()
    try:
        # Verifichiamo prima che il cliente sia effettivamente un lead
        cliente = conn.execute('SELECT tipo FROM clienti WHERE id = ?', (cliente_id,)).fetchone()
        if not cliente or cliente['tipo'] != 'lead':
            return False, "Il cliente non è un lead o non esiste"
        
        # Aggiorniamo il tipo del cliente
        conn.execute('''
            UPDATE clienti 
            SET tipo = 'effettivo'
            WHERE id = ?
        ''', (cliente_id,))
        conn.commit()
        return True, "Cliente promosso con successo"
    except Exception as e:
        conn.rollback()
        return False, f"Errore durante la promozione: {str(e)}"
    finally:
        conn.close()