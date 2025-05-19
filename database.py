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
        codice_fiscale TEXT, -- Nuovo campo per il codice fiscale
        data_registrazione TEXT NOT NULL,
        taglia_giubotto TEXT,  -- Nuovo campo per la taglia giubotto
        taglia_cintura TEXT,   -- Nuovo campo per la taglia cintura
        taglia_braccia TEXT,   -- Nuovo campo per la taglia braccia
        taglia_gambe TEXT,     -- Nuovo campo per la taglia gambe
        obiettivo_cliente TEXT, -- Nuovo campo per l'obiettivo cliente
        sede_id INTEGER NOT NULL, -- Nuovo campo per la sede
        FOREIGN KEY (sede_id) REFERENCES sede (id)
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
        attivo BOOLEAN NOT NULL DEFAULT 1,
        pagamento_unico BOOLEAN NOT NULL DEFAULT 0
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
        metodo_pagamento TEXT,  -- Nuovo campo per il metodo di pagamento
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
def get_all_clienti(sede_ids=None):
    conn = get_db_connection()
    if sede_ids:
        placeholders = ','.join('?' for _ in sede_ids)
        query = f'SELECT * FROM clienti WHERE sede_id IN ({placeholders}) ORDER BY cognome, nome'
        clienti = conn.execute(query, sede_ids).fetchall()
    else:
        clienti = conn.execute('SELECT * FROM clienti ORDER BY cognome, nome').fetchall()
    conn.close()
    return clienti

def get_all_utenti():
    """Retrieve all users from the utenti table."""
    conn = get_db_connection()
    try:
        utenti = conn.execute('SELECT * FROM utenti ORDER BY nome, cognome').fetchall()
        return utenti
    finally:
        conn.close()

def delete_user(user_id):
    """Delete a user from the utenti table."""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM utenti WHERE id = ?', (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_cliente(cliente_id):
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clienti WHERE id = ?', (cliente_id,)).fetchone()
    conn.close()
    return cliente

def get_leads(sede_ids=None):
    conn = get_db_connection()
    if sede_ids:
        placeholders = ','.join('?' for _ in sede_ids)
        query = f"SELECT * FROM clienti WHERE tipo = 'lead' AND sede_id IN ({placeholders}) ORDER BY cognome, nome"
        leads = conn.execute(query, sede_ids).fetchall()
    else:
        leads = conn.execute("SELECT * FROM clienti WHERE tipo = 'lead' ORDER BY cognome, nome").fetchall()
    conn.close()
    return leads

def get_clienti_effettivi(sede_ids=None):
    conn = get_db_connection()
    if sede_ids:
        placeholders = ','.join('?' for _ in sede_ids)
        query = f"SELECT * FROM clienti WHERE tipo = 'effettivo' AND sede_id IN ({placeholders}) ORDER BY cognome, nome"
        clienti = conn.execute(query, sede_ids).fetchall()
    else:
        clienti = conn.execute("SELECT * FROM clienti WHERE tipo = 'effettivo' ORDER BY cognome, nome").fetchall()
    conn.close()
    return clienti

def add_cliente(nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_registrazione = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute(''' 
    INSERT INTO clienti (nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, data_registrazione, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, data_registrazione, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, sede_id))
    
    conn.commit()
    cliente_id = cursor.lastrowid
    conn.close()
    return cliente_id

def update_cliente(cliente_id, nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente):
    conn = get_db_connection()
    try:
        conn.execute(''' 
        UPDATE clienti 
        SET nome = ?, cognome = ?, email = ?, telefono = ?, data_nascita = ?, 
            indirizzo = ?, citta = ?, cap = ?, note = ?, tipo = ?, codice_fiscale = ?, 
            tipologia = ?, taglia_giubotto = ?, taglia_cintura = ?, taglia_braccia = ?, 
            taglia_gambe = ?, obiettivo_cliente = ?
        WHERE id = ?
        ''', (nome, cognome, email, telefono, data_nascita, indirizzo, citta, cap, note, tipo, codice_fiscale, tipologia, taglia_giubotto, taglia_cintura, taglia_braccia, taglia_gambe, obiettivo_cliente, cliente_id))
        conn.commit()
    except Exception as e:
        print(f"Errore durante l'aggiornamento del cliente: {e}")
        conn.rollback()
        raise
    finally:
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

def get_all_pacchetti_validi():
    conn = get_db_connection()
    oggi = datetime.now().strftime('%Y-%m-%d')
    pacchetti = conn.execute('''
    SELECT * FROM pacchetti
    WHERE data_scadenza IS NULL OR data_scadenza >= ?
    ORDER BY nome
    ''', (oggi,)).fetchall()
    conn.close()
    return pacchetti

def delete_pacchetto(pacchetto_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM pacchetti WHERE id = ?', (pacchetto_id,))
        conn.commit()
    except Exception as e:
        print(f"Errore durante l'eliminazione del pacchetto: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_pacchetto(pacchetto_id):
    conn = get_db_connection()
    pacchetto = conn.execute('SELECT * FROM pacchetti WHERE id = ?', (pacchetto_id,)).fetchone()
    conn.close()
    return pacchetto

def add_pacchetto(nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico, data_scadenza=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO pacchetti (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico, data_scadenza)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico, data_scadenza))
    conn.commit()
    pacchetto_id = cursor.lastrowid
    conn.close()
    return pacchetto_id

def update_pacchetto(pacchetto_id, nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico, data_scadenza=None):
    conn = get_db_connection()
    conn.execute('''
    UPDATE pacchetti 
    SET nome = ?, descrizione = ?, prezzo = ?, numero_lezioni = ?, durata_giorni = ?, attivo = ?, pagamento_unico = ?, data_scadenza = ?
    WHERE id = ?
    ''', (nome, descrizione, prezzo, numero_lezioni, durata_giorni, attivo, pagamento_unico, data_scadenza, pacchetto_id))
    
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

def get_rate_scadenza(sede_ids):
    conn = get_db_connection()
    if not sede_ids:
        return []

    placeholders = ','.join('?' for _ in sede_ids)
    query = f'''
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
        WHERE r.pagato = 0 AND c.sede_id IN ({placeholders})
        ORDER BY r.data_scadenza ASC
    '''
    rate = conn.execute(query, sede_ids).fetchall()
    conn.close()
    return rate

def get_rate_incassate_mese(sede_ids=None):
    mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    mese_fine = mese_fine.strftime("%Y-%m-%d")
    conn = get_db_connection()
    try:
        if sede_ids:
            placeholders = ','.join('?' for _ in sede_ids)
            query = f'''
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
                WHERE r.data_pagamento BETWEEN ? AND ? 
                AND r.pagato = 1 
                AND c.sede_id IN ({placeholders})
                ORDER BY r.data_pagamento ASC;
            '''
            rate = conn.execute(query, [mese_inizio, mese_fine] + sede_ids).fetchall()
        else:
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
                WHERE r.data_pagamento BETWEEN ? AND ? 
                AND r.pagato = 1
                ORDER BY r.data_pagamento ASC;
            ''', (mese_inizio, mese_fine)).fetchall()
        return rate
    finally:
        conn.close()

def get_rate_calendario(mese=None, anno=None, sede_ids=None):
    conn = get_db_connection()
    try:
        if not sede_ids:
            return []

        placeholders = ','.join('?' for _ in sede_ids)
        query = f'''
            SELECT 
                r.data_scadenza,
                COUNT(r.id) as rate_da_pagare,
                GROUP_CONCAT(c.nome || ' ' || c.cognome) as clienti,
                GROUP_CONCAT(c.id) as clienti_ids
            FROM rate r
            JOIN abbonamenti a ON r.abbonamento_id = a.id
            JOIN clienti c ON a.cliente_id = c.id
            WHERE r.pagato = 0 AND c.sede_id IN ({placeholders})
        '''
        params = sede_ids
        
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
        return [dict(row) for row in scadenze]
    finally:
        conn.close()

def paga_rata(rata_id, metodo_pagamento, importo_pagato):
    conn = get_db_connection()
    data_pagamento = datetime.now().strftime("%Y-%m-%d")
    
    try:
        conn.execute('''
        UPDATE rate SET pagato = 1, data_pagamento = ?, metodo_pagamento = ?, importo = ? WHERE id = ?
        ''', (data_pagamento, metodo_pagamento, importo_pagato, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la registrazione del pagamento: {e}")
        conn.rollback()
        return False
    finally:
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

def add_lezione(abbonamento_id, data, note, registrata_da):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Inserisci la nuova lezione
        cursor.execute('''
        INSERT INTO lezioni (abbonamento_id, data, note, registrata_da)
        VALUES (?, ?, ?, ?)
        ''', (abbonamento_id, data, note, registrata_da))
        
        # Incrementa il numero di lezioni utilizzate per l'abbonamento
        cursor.execute('''
        UPDATE abbonamenti
        SET lezioni_utilizzate = lezioni_utilizzate + 1
        WHERE id = ?
        ''', (abbonamento_id,))
        
        conn.commit()
        lezione_id = cursor.lastrowid
        return lezione_id
    except Exception as e:
        print(f"Errore durante l'aggiunta della lezione: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def modifica_rata_pagata(rata_id, data_pagamento, metodo_pagamento):
    conn = get_db_connection()
    try:
        conn.execute('''
        UPDATE rate
        SET data_pagamento = ?, metodo_pagamento = ?
        WHERE id = ?
        ''', (data_pagamento, metodo_pagamento, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la modifica della rata pagata: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modifica_rata_non_pagata(rata_id, importo, data_scadenza):
    conn = get_db_connection()
    try:
        conn.execute('''
        UPDATE rate
        SET importo = ?, data_scadenza = ?
        WHERE id = ?
        ''', (importo, data_scadenza, rata_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante la modifica della rata non pagata: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

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
def get_statistiche_dashboard(sede_ids=None):
    conn = get_db_connection()
    oggi = datetime.now().strftime("%Y-%m-%d")
    
    stats = {}
    if sede_ids:
        placeholders = ','.join('?' for _ in sede_ids)
        stats['totale_clienti'] = len(get_clienti_effettivi(sede_ids))
        stats['totale_leads'] = len(get_leads(sede_ids))
        stats['abbonamenti_attivi'] = conn.execute(f"SELECT COUNT(*) FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders})) AND data_fine >= ?", sede_ids + [oggi]).fetchone()[0]
        stats['rate_oggi'] = conn.execute(f"SELECT COUNT(*) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza = ? AND pagato = 0", sede_ids + [oggi]).fetchone()[0]
        stats['rate_scadute'] = conn.execute(f"SELECT COUNT(*) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza < ? AND pagato = 0", sede_ids + [oggi]).fetchone()[0]
        stats['rate_scadute_importo'] = conn.execute(f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza < ? AND pagato = 0", sede_ids + [oggi]).fetchone()[0]
        
        # Previsione mese corrente
        mese_inizio = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        mese_fine = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        mese_fine = mese_fine.strftime("%Y-%m-%d")
        stats['incassi_mese'] = conn.execute(f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_pagamento BETWEEN ? AND ? AND pagato = 1", sede_ids + [mese_inizio, mese_fine]).fetchone()[0] or 0
        stats['previsione_mese'] = conn.execute(f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza BETWEEN ? AND ? AND pagato = 0", sede_ids + [mese_inizio, mese_fine]).fetchone()[0] or 0
        
        # Previsione mese prossimo
        current_date = datetime.now()
        prossimo_mese_inizio = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d")
        prossimo_mese_fine = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) + timedelta(days=31)
        prossimo_mese_fine = prossimo_mese_fine.replace(day=1) - timedelta(days=1)
        prossimo_mese_fine = prossimo_mese_fine.strftime("%Y-%m-%d")
        stats['previsione_mese_prossimo'] = conn.execute(f"SELECT SUM(importo) FROM rate WHERE abbonamento_id IN (SELECT id FROM abbonamenti WHERE cliente_id IN (SELECT id FROM clienti WHERE sede_id IN ({placeholders}))) AND data_scadenza BETWEEN ? AND ? AND pagato = 0", sede_ids + [prossimo_mese_inizio, prossimo_mese_fine]).fetchone()[0] or 0
    else:
        stats = {
            'totale_clienti': 0,
            'totale_leads': 0,
            'abbonamenti_attivi': 0,
            'rate_oggi': 0,
            'rate_scadute': 0,
            'rate_scadute_importo': 0,
            'incassi_mese': 0,
            'previsione_mese': 0,
            'previsione_mese_prossimo': 0
        }

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
        
        if (abbonamento['lezioni_utilizzate'] >= abbonamento['numero_lezioni']):
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
        # Add the registrata_da column if it doesn't exist
        conn.execute('''
            ALTER TABLE lezioni ADD COLUMN registrata_da TEXT DEFAULT NULL
        ''')
        conn.commit()
        print("Migrazione completata con successo")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("La colonna 'registrata_da' esiste già.")
        else:
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
    cursor = conn.cursor()
    try:
        # Aggiungi il campo data_scadenza alla tabella pacchetti
        cursor.execute('''
        ALTER TABLE pacchetti ADD COLUMN data_scadenza DATE
        ''')
    except Exception as e:
        print(f"Errore durante la migrazione del database: {e}")
    finally:
        conn.commit()
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

#----------------------------------------------------------------------------
def create_user_tables():
    """Crea le tabelle per la gestione degli utenti e della gerarchia"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabella per i franchisor
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS franchisor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabella per gli area manager
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS area_manager (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        franchisor_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (franchisor_id) REFERENCES franchisor(id)
    )
    ''')
    
    # Tabella per le società
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS societa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_manager_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        indirizzo TEXT,  -- Nuovo campo per l'indirizzo
        comune TEXT,     -- Nuovo campo per il comune
        provincia TEXT,  -- Nuovo campo per la provincia
        FOREIGN KEY (area_manager_id) REFERENCES area_manager(id)
    )
    ''')
    
    # Tabella per le sedi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sede (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        societa_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        indirizzo TEXT,
        citta TEXT,
        cap TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        attivo BOOLEAN DEFAULT 1,
        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (societa_id) REFERENCES societa(id)
    )
    ''')
    
    # Aggiungi una colonna sede_id a tutte le tabelle esistenti
    tables = ['clienti', 'pacchetti', 'abbonamenti', 'lezioni', 'rate']
    for table in tables:
        try:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN sede_id INTEGER DEFAULT 1')
        except:
            pass  # La colonna potrebbe già esistere
    
    # Crea una sede fittizia per i dati esistenti
    cursor.execute('''
    INSERT OR IGNORE INTO franchisor (id, nome, email, password) 
    VALUES (1, 'Franchisor Default', 'franchisor@example.com', 'password')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO area_manager (id, franchisor_id, nome, email, password) 
    VALUES (1, 1, 'Area Manager Default', 'area@example.com', 'password')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO societa (id, area_manager_id, nome, email, password) 
    VALUES (1, 1, 'Società Default', 'societa@example.com', 'password')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO sede (id, societa_id, nome, email, password) 
    VALUES (1, 1, 'Sede Default', 'sede@example.com', 'password')
    ''')
    
    conn.commit()
    conn.close()

def authenticate_user(email, password):
    """Autentica un utente dalla tabella utenti in base a email e password."""
    conn = get_db_connection()
    try:
        query = '''
        SELECT id, nome, cognome, email, ruolo 
        FROM utenti 
        WHERE email = ? AND password = ? AND attivo = 1
        '''
        user = conn.execute(query, (email, password)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def get_franchisor(franchisor_id):
    conn = get_db_connection()
    franchisor = conn.execute('SELECT * FROM franchisor WHERE id = ?', (franchisor_id,)).fetchone()
    conn.close()
    return franchisor

def get_area_managers_by_franchisor(franchisor_id):
    conn = get_db_connection()
    managers = conn.execute('SELECT * FROM area_manager WHERE franchisor_id = ?', (franchisor_id,)).fetchall()
    conn.close()
    return managers

def get_societa_by_area_manager(area_manager_id):
    conn = get_db_connection()
    societa = conn.execute('SELECT * FROM societa WHERE area_manager_id = ?', (area_manager_id,)).fetchall()
    conn.close()
    return societa

def get_sedi_by_societa(societa_id):
    conn = get_db_connection()
    sedi = conn.execute('SELECT * FROM sede WHERE societa_id = ?', (societa_id,)).fetchall()
    conn.close()
    return sedi

def get_franchisors():
    conn = get_db_connection()
    try:
        return conn.execute('SELECT * FROM franchisor').fetchall()
    finally:
        conn.close()

def get_all_data():
    """Retrieve all franchisors, area managers, companies, and locations."""
    conn = get_db_connection()
    try:
        # Get all franchisors
        franchisors = conn.execute('SELECT * FROM franchisor').fetchall()
        
        # Get all area managers
        area_managers = conn.execute('SELECT * FROM area_manager').fetchall()
        
        # Get all companies
        societa = conn.execute('SELECT * FROM societa').fetchall()
        
        # Get all locations
        sedi = conn.execute('SELECT * FROM sede').fetchall()
        
        return franchisors, area_managers, societa, sedi
    finally:
        conn.close()

def build_hierarchy(user_role=None, user_email=None):
    """Build a filtered hierarchy based on the user's role and email."""
    hierarchy = []

    # Determine the franchisor ID for the logged-in user
    franchisor_id = None
    if user_role == 'franchisor':
        franchisor = get_franchisor_by_email(user_email)
        if franchisor:
            franchisor_id = franchisor['id']
    elif user_role == 'area manager':
        conn = get_db_connection()
        try:
            area_manager = conn.execute('SELECT * FROM area_manager WHERE email = ?', (user_email,)).fetchone()
            if area_manager:
                franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    elif user_role == 'societa':
        conn = get_db_connection()
        try:
            societa = conn.execute('SELECT * FROM societa WHERE email = ?', (user_email,)).fetchone()
            if societa:
                area_manager = conn.execute('SELECT * FROM area_manager WHERE id = ?', (societa['area_manager_id'],)).fetchone()
                if area_manager:
                    franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    elif user_role == 'sede':
        conn = get_db_connection()
        try:
            sede = conn.execute('SELECT * FROM sede WHERE email = ?', (user_email,)).fetchone()
            if sede:
                societa = conn.execute('SELECT * FROM societa WHERE id = ?', (sede['societa_id'],)).fetchone()
                if societa:
                    area_manager = conn.execute('SELECT * FROM area_manager WHERE id = ?', (societa['area_manager_id'],)).fetchone()
                    if area_manager:
                        franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()
    elif user_role == 'trainer':
        conn = get_db_connection()
        try:
            trainer = conn.execute('SELECT * FROM trainer WHERE email = ?', (user_email,)).fetchone()
            if trainer:
                sede = conn.execute('SELECT * FROM sede WHERE id = ?', (trainer['sede_id'],)).fetchone()
                if sede:
                    societa = conn.execute('SELECT * FROM societa WHERE id = ?', (sede['societa_id'],)).fetchone()
                    if societa:
                        area_manager = conn.execute('SELECT * FROM area_manager WHERE id = ?', (societa['area_manager_id'],)).fetchone()
                        if area_manager:
                            franchisor_id = area_manager['franchisor_id']
        finally:
            conn.close()

    # Build the hierarchy for the determined franchisor
    if franchisor_id:
        franchisor = get_franchisor(franchisor_id)
        if franchisor:
            franchisor_dict = {
                'id': franchisor['id'],
                'nome': franchisor['nome'],
                'email': franchisor['email'],
                'type': 'franchisor',
                'area_managers': []
            }
            area_managers = get_area_managers_by_franchisor(franchisor['id'])
            for area_manager in area_managers:
                area_manager_dict = {
                    'id': area_manager['id'],
                    'nome': area_manager['nome'],
                    'cognome': area_manager['cognome'],
                    'email': area_manager['email'],
                    'type': 'area_manager',
                    'societa': []
                }
                societa = get_societa_by_area_manager(area_manager['id'])
                for company in societa:
                    company_dict = {
                        'id': company['id'],
                        'nome': company['nome'],
                        'type': 'societa',
                        'sedi': []
                    }
                    sedi = get_sedi_by_societa(company['id'])
                    for sede in sedi:
                        sede_dict = {
                            'id': sede['id'],
                            'nome': sede['nome'],
                            'indirizzo': sede['indirizzo'],
                            'citta': sede['citta'],
                            'cap': sede['cap'],
                            'type': 'sede',
                            'trainers': get_trainers_by_sede(sede['id'])
                        }
                        company_dict['sedi'].append(sede_dict)
                    area_manager_dict['societa'].append(company_dict)
                franchisor_dict['area_managers'].append(area_manager_dict)
            hierarchy.append(franchisor_dict)
        else:
            hierarchy.append({'area_managers': []})  # Ensure consistent structure for franchisor

    return hierarchy



def get_user_by_email(email):
    """Retrieve a user by their email."""
    conn = get_db_connection()
    try:
        query = 'SELECT * FROM utenti WHERE email = ?'
        user = conn.execute(query, (email,)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def update_franchisor(franchisor_id, nome, email, password):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE franchisor 
            SET nome = ?, email = ?, password = ?
            WHERE id = ?
        ''', (nome, email, password, franchisor_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating franchisor: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_franchisor(franchisor_id):
    conn = get_db_connection()
    try:
        # First, get all area managers associated with the franchisor
        area_managers = conn.execute('SELECT id FROM area_manager WHERE franchisor_id = ?', (franchisor_id,)).fetchall()
        
        # Delete all associated companies and their locations
        for area_manager in area_managers:
            area_manager_id = area_manager['id']
            # Delete all associated locations
            conn.execute('DELETE FROM sede WHERE societa_id IN (SELECT id FROM societa WHERE area_manager_id = ?)', (area_manager_id,))
            # Delete all associated companies
            conn.execute('DELETE FROM societa WHERE area_manager_id = ?', (area_manager_id,))
        
        # Finally, delete the area managers
        conn.execute('DELETE FROM area_manager WHERE franchisor_id = ?', (franchisor_id,))
        
        # Then, delete the franchisor
        conn.execute('DELETE FROM franchisor WHERE id = ?', (franchisor_id,))
        
        conn.commit()
    except Exception as e:
        print(f"Error deleting franchisor: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_area_manager(area_manager_id, nome, cognome, email, password):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE area_manager 
            SET nome = ?, cognome = ?, email = ?, password = ?
            WHERE id = ?
        ''', (nome, cognome, email, password, area_manager_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating area manager: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_area_manager(area_manager_id):
    conn = get_db_connection()
    try:
        # First, get all companies associated with the area manager
        companies = conn.execute('SELECT id FROM societa WHERE area_manager_id = ?', (area_manager_id,)).fetchall()
        
        # Delete all associated locations for each company
        for company in companies:
            company_id = company['id']
            conn.execute('DELETE FROM sede WHERE societa_id = ?', (company_id,))
        
        # Delete all associated companies
        conn.execute('DELETE FROM societa WHERE area_manager_id = ?', (area_manager_id,))
        
        # Finally, delete the area manager
        conn.execute('DELETE FROM area_manager WHERE id = ?', (area_manager_id,))
        
        conn.commit()
    except Exception as e:
        print(f"Error deleting area manager: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_company(company_id, nome, email, password, indirizzo, provincia, comune):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE societa 
            SET nome = ?, email = ?, password = ?, indirizzo = ?, provincia = ?, comune = ?
            WHERE id = ?
        ''', (nome, email, password, indirizzo, provincia, comune, company_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating company: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_company(company_id):
    conn = get_db_connection()
    try:
        # First, delete all associated locations
        conn.execute('DELETE FROM sede WHERE societa_id = ?', (company_id,))
        # Then, delete the company
        conn.execute('DELETE FROM societa WHERE id = ?', (company_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting company: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_sede(sede_id, nome, indirizzo, citta, cap, email, password):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE sede 
            SET nome = ?, indirizzo = ?, citta = ?, cap = ?, email = ?, password = ?
            WHERE id = ?
        ''', (nome, indirizzo, citta, cap, email, password, sede_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating sede: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_sede(sede_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM sede WHERE id = ?', (sede_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting sede: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_trainer(trainer_id):
    """Delete a trainer from the database."""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM trainer WHERE id = ?', (trainer_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting trainer: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    return True

def update_trainer(trainer_id, nome, cognome, email, password):
    """Update trainer details in the database."""
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE trainer
            SET nome = ?, cognome = ?, email = ?, password = ?
            WHERE id = ?
        ''', (nome, cognome, email, password, trainer_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating trainer: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    return True

def register_franchisor(nome, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert the franchisor into the franchisor table
        cursor.execute('INSERT INTO franchisor (nome, email, password) VALUES (?, ?, ?)', 
                       (nome, email, password))
        franchisor_id = cursor.lastrowid
        
        # Create a new user with the provided credentials using the same connection
        user_created = create_user(cursor, nome, '', email, password, 'franchisor')  # Pass cursor instead of creating a new connection
        
        conn.commit()
        return franchisor_id if user_created else None
    except Exception as e:
        conn.rollback()
        print(f"Errore durante la registrazione del franchisor: {e}")
        return None
    finally:
        conn.close()

def register_area_manager(franchisor_id, nome, cognome, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO area_manager (franchisor_id, nome, cognome, email, password) VALUES (?, ?, ?, ?, ?)', 
                      (franchisor_id, nome, cognome, email, password))
        area_manager_id = cursor.lastrowid
        user_created = create_user(cursor, nome, cognome, email, password, 'area manager')  # Pass cursor instead of creating a new connection

        conn.commit()
        return area_manager_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione dell'area manager: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def register_societa(area_manager_id, nome, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO societa (area_manager_id, nome, email, password) VALUES (?, ?, ?, ?)', 
                      (area_manager_id, nome, email, password))
        societa_id = cursor.lastrowid
        user_created = create_user(cursor, nome, '', email, password, 'societa')  # Pass cursor instead of creating a new connection

        conn.commit()
        return societa_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione della società: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def register_sede(societa_id, nome, indirizzo, citta, cap, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO sede (societa_id, nome, indirizzo, citta, cap, email, password) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (societa_id, nome, indirizzo, citta, cap, email, password))
        sede_id = cursor.lastrowid
        user_created = create_user(cursor, nome, '', email, password, 'sede')  # Pass cursor instead of creating a new connection

        conn.commit()
        return sede_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione della sede: {e}")

        conn.rollback()
        return None
    finally:
        conn.close()

def register_trainer(sede_id, nome, cognome, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert the trainer into the trainer table
        cursor.execute(''' 
        INSERT INTO trainer (sede_id, nome, cognome, email, password) 
        VALUES (?, ?, ?, ?, ?)
        ''', (sede_id, nome, cognome, email, password))
        
        trainer_id = cursor.lastrowid
        
        # Create a new user with the provided credentials using the same connection
        user_created = create_user(cursor, nome, cognome, email, password, 'trainer')  # Pass cursor instead of creating a new connection

        conn.commit()
        return trainer_id if user_created else None
    except Exception as e:
        print(f"Errore durante la registrazione del trainer: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def create_user(cursor, nome, cognome, email, password, role):
    try:
        cursor.execute('''
            INSERT INTO utenti (nome, cognome, email, password, ruolo)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, cognome, email, password, role))  # Use the passed cursor
        
        return True
    except Exception as e:
        print(f"Errore durante la creazione dell'utente: {e}")
        return False

def get_trainers_by_sede(sede_id):
    conn = get_db_connection()
    try:
        trainers = conn.execute('SELECT * FROM trainer WHERE sede_id = ?', (sede_id,)).fetchall()
        return trainers
    finally:
        conn.close()

def crea_nuova_rata(abbonamento_id, importo, data_scadenza):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO rate (abbonamento_id, importo, data_scadenza, pagato, numero_rata)
            VALUES (?, ?, ?, 0, (SELECT COALESCE(MAX(numero_rata), 0) + 1 FROM rate WHERE abbonamento_id = ?))
        ''', (abbonamento_id, importo, data_scadenza, abbonamento_id))
        conn.commit()
    except Exception as e:
        print(f"Errore durante la creazione della nuova rata: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_franchisor_by_email(email):
    conn = get_db_connection()
    franchisor = conn.execute('SELECT * FROM franchisor WHERE email = ?', (email,)).fetchone()
    conn.close()
    return franchisor

def get_sede_by_email(email):
    """Fetch the sede details by email."""
    conn = get_db_connection()
    sede = conn.execute('SELECT * FROM sede WHERE email = ?', (email,)).fetchone()
    conn.close()
    return sede

def get_sedi_by_societa_email(email):
    """Fetch all sedi under a societa by the societa's email."""
    conn = get_db_connection()
    societa = conn.execute('SELECT * FROM societa WHERE email = ?', (email,)).fetchone()
    if societa:
        sedi = conn.execute('SELECT * FROM sede WHERE societa_id = ?', (societa['id'],)).fetchall()
    else:
        sedi = []
    conn.close()
    return sedi

def get_societa_by_area_manager_email(email):
    """Fetch all societa under an area manager by the area manager's email."""
    conn = get_db_connection()
    area_manager = conn.execute('SELECT * FROM area_manager WHERE email = ?', (email,)).fetchone()
    if area_manager:
        societa = conn.execute('SELECT * FROM societa WHERE area_manager_id = ?', (area_manager['id'],)).fetchall()
    else:
        societa = []
    conn.close()
    return societa

def get_area_managers_by_franchisor_email(email):
    """Fetch all area managers under a franchisor by the franchisor's email."""
    conn = get_db_connection()
    franchisor = conn.execute('SELECT * FROM franchisor WHERE email = ?', (email,)).fetchone()
    if franchisor:
        area_managers = conn.execute('SELECT * FROM area_manager WHERE franchisor_id = ?', (franchisor['id'],)).fetchall()
    else:
        area_managers = []
    conn.close()
    return area_managers

def get_sedi_by_franchisor_email(email):
    """Fetch all sedi under a franchisor by the franchisor's email."""
    conn = get_db_connection()
    try:
        franchisor = conn.execute('SELECT id FROM franchisor WHERE email = ?', (email,)).fetchone()
        if franchisor:
            sedi = conn.execute('''
                SELECT s.* 
                FROM sede s
                JOIN societa so ON s.societa_id = so.id
                JOIN area_manager am ON so.area_manager_id = am.id
                WHERE am.franchisor_id = ?
            ''', (franchisor['id'],)).fetchall()
            return sedi
        return []
    finally:
        conn.close()

def get_area_manager_by_email(email):
    """Fetch the area manager details by email."""
    conn = get_db_connection()
    try:
        area_manager = conn.execute('SELECT * FROM area_manager WHERE email = ?', (email,)).fetchone()
        return area_manager
    finally:
        conn.close()

def get_sede_by_trainer_email(email):
    """Fetch the sede associated with a trainer by their email."""
    conn = get_db_connection()
    trainer = conn.execute('SELECT * FROM trainer WHERE email = ?', (email,)).fetchone()
    if trainer:
        sede = conn.execute('SELECT * FROM sede WHERE id = ?', (trainer['sede_id'],)).fetchone()
    else:
        sede = None
    conn.close()
    return sede

def get_societa_by_email(email):
    """Fetch the societa details by email."""
    conn = get_db_connection()
    societa = conn.execute('SELECT * FROM societa WHERE email = ?', (email,)).fetchone()
    conn.close()
    return societa

def get_user_email_by_id(user_id):
    """
    Fetch the email of a user based on their ID.
    """
    conn = get_db_connection()
    user_email = conn.execute('SELECT email FROM utenti WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user_email['email'] if user_email else None

def log_event(utente_id, email, azione, dettagli=None):
    """Inserisce un evento nella tabella eventi."""
    conn = get_db_connection()
    try:
        conn.execute('''
        INSERT INTO eventi (utente_id, email, azione, dettagli)
        VALUES (?, ?, ?, ?)
        ''', (utente_id, email, azione, dettagli))
        conn.commit()
    finally:
        conn.close()

def get_all_eventi():
    """Recupera tutti gli eventi dalla tabella eventi."""
    conn = get_db_connection()
    try:
        eventi = conn.execute('SELECT * FROM eventi ORDER BY data_evento DESC').fetchall()
        return eventi
    finally:
        conn.close()

def is_trainer_present(trainer_id):
    """Check if the trainer's last action was 'entra'."""
    conn = get_db_connection()
    try:
        last_event = conn.execute('''
        SELECT azione FROM eventi
        WHERE utente_id = ? AND (azione = 'entra' OR azione = 'esci')
        ORDER BY data_evento DESC LIMIT 1
        ''', (trainer_id,)).fetchone()
        return last_event and last_event['azione'] == 'entra'
    finally:
        conn.close()

def get_trainers_with_status(sede_ids):
    """Fetch trainers and their current status (entered or not) for the given sede_ids."""
    conn = get_db_connection()
    try:
        placeholders = ','.join('?' for _ in sede_ids)
        query = f'''
            SELECT 
                t.id, 
                t.nome, 
                t.cognome, 
                t.email,
                COALESCE((
                    SELECT e.azione 
                    FROM eventi e 
                    WHERE e.email = t.email AND (e.azione = 'entra' OR e.azione = 'esci') 
                    ORDER BY e.data_evento DESC LIMIT 1
                ), 'esci') AS stato
            FROM trainer t
            WHERE t.sede_id IN ({placeholders})
            ORDER BY t.cognome, t.nome
        '''
        trainers = conn.execute(query, sede_ids).fetchall()
        return [dict(trainer) for trainer in trainers]
    finally:
        conn.close()

def add_resoconto(trainer_id, data, ore_lavoro, ore_buca, attivita_buca):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO resoconti (trainer_id, data, ore_lavoro, ore_buca, attivita_buca)
        VALUES (?, ?, ?, ?, ?)
    ''', (trainer_id, data, ore_lavoro, ore_buca, attivita_buca))
    conn.commit()
    conn.close()

def get_resoconti_by_trainer(trainer_id):
    conn = get_db_connection()
    resoconti = conn.execute('''
        SELECT * FROM resoconti WHERE trainer_id = ? ORDER BY data DESC
    ''', (trainer_id,)).fetchall()
    conn.close()
    return resoconti

def get_resoconto(resoconto_id):
    conn = get_db_connection()
    resoconto = conn.execute('''
        SELECT * FROM resoconti WHERE id = ?
    ''', (resoconto_id,)).fetchone()
    conn.close()
    return resoconto

def create_appointments_table():
    conn = get_db_connection()
    try:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            notes TEXT,
            date_time DATETIME NOT NULL,
            appointment_type TEXT NOT NULL,
            status TEXT NOT NULL,
            is_trial BOOLEAN DEFAULT 0,
            is_recovery BOOLEAN DEFAULT 0,
            is_lesson_zero BOOLEAN DEFAULT 0,
            FOREIGN KEY (trainer_id) REFERENCES trainer (id),
            FOREIGN KEY (client_id) REFERENCES clienti (id)
        )
        ''')
        conn.commit()
    finally:
        conn.close()

from dateutil.parser import parse  # Importa il parser per gestire i formati ISO 8601

def get_appointments_by_users(user_ids, start_date):
    """Retrieve appointments for multiple users starting from a specific date."""
    conn = get_db_connection()
    try:
        # Calculate the end date (7 days from the start date)
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=60)).strftime('%Y-%m-%d')

        # Query to fetch appointments
        query = '''
            SELECT DISTINCT a.*, c.nome || ' ' || c.cognome AS client_name, u.nome || ' ' || u.cognome AS trainer_name,
            ab.numero_lezioni,
            ab.lezioni_utilizzate,
            ab.pacchetto_id
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            JOIN utenti u ON a.trainer_id = u.id
            LEFT JOIN abbonamenti ab ON a.client_id = ab.cliente_id AND a.package_id = ab.id
            WHERE a.trainer_id IN ({})
            AND a.date_time BETWEEN ? AND ?
            ORDER BY a.date_time ASC
        '''.format(','.join('?' for _ in user_ids))
        params = user_ids + [start_date, end_date]
        appointments = conn.execute(query, params).fetchall()
        print("SECONDA-------------")
        print(appointments)

        # Parse date_time and end_date_time into datetime objects
        parsed_appointments = []
        lesson_counter = {}  # Dizionario per tracciare il numero progressivo delle lezioni per ogni abbonamento

        for appointment in appointments:
            appointment = dict(appointment)
            package_id = appointment.get('package_id')
            if package_id:
                if package_id not in lesson_counter:
                    # Inizializza il contatore con il numero di lezioni già registrate
                    lesson_counter[package_id] = appointment['lezioni_utilizzate']
                lesson_counter[package_id] += 1
                appointment['lezione_numero'] = lesson_counter[package_id]
            else:
                appointment['lezione_numero'] = None
            try:
                appointment['date_time'] = datetime.strptime(appointment['date_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['date_time'] = datetime.strptime(appointment['date_time'], '%Y-%m-%dT%H:%M')
            try:
                appointment['end_date_time'] = datetime.strptime(appointment['end_date_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['end_date_time'] = datetime.strptime(appointment['end_date_time'], '%Y-%m-%dT%H:%M')
            parsed_appointments.append(appointment)

        return parsed_appointments
    finally:
        conn.close()


def add_appointment(trainer_id, client_id, title, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        conn.execute('''
            INSERT INTO appointments (trainer_id, client_id, title, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (trainer_id, client_id, title, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, package_id))
        conn.commit()
        appointment_id = cursor.lastrowid  # Ottieni l'ID dell'appuntamento appena creato
        return appointment_id
    except Exception as e:
        print(f"Errore durante l'aggiunta dell'appuntamento: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_appointment_by_id(appointment_id):
    conn = get_db_connection()
    try:
        appointment = conn.execute('''
        SELECT 
            a.*, 
            c.nome || ' ' || c.cognome AS client_name, 
            u.nome || ' ' || u.cognome AS trainer_name,
            ab.id AS package_id,
            ab.numero_lezioni,
            ab.lezioni_utilizzate
        FROM appointments a
        JOIN clienti c ON a.client_id = c.id
        JOIN utenti u ON a.trainer_id = u.id
        LEFT JOIN abbonamenti ab ON a.package_id = ab.id
        WHERE a.id = ?
        ''', (appointment_id,)).fetchone()
        
        if appointment:
            appointment = dict(appointment)
            try:
                appointment['date_time'] = datetime.strptime(appointment['date_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['date_time'] = datetime.strptime(appointment['date_time'], '%Y-%m-%dT%H:%M')
            try:
                appointment['end_date_time'] = datetime.strptime(appointment['end_date_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['end_date_time'] = datetime.strptime(appointment['end_date_time'], '%Y-%m-%dT%H:%M')
        
        return appointment
    finally:
        conn.close()

def delete_appointment(appointment_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore eliminazione appuntamento: {e}")
        return False
    finally:
        conn.close()


def get_appointments_by_trainers(trainer_ids, start_date):
    """Retrieve appointments for multiple trainers starting from a specific date."""
    conn = get_db_connection()
    try:
        # Calculate the end date (7 days from the start date)
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')

        # Query to fetch appointments
        query = '''
            SELECT a.*, c.nome || ' ' || c.cognome AS client_name
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            WHERE a.trainer_id IN ({})
            AND a.date_time BETWEEN ? AND ?
            ORDER BY a.date_time ASC
        '''.format(','.join('?' for _ in trainer_ids))
        params = trainer_ids + [start_date, end_date]
        appointments = conn.execute(query, params).fetchall()

        # Parse date_time and end_date_time into datetime objects
        parsed_appointments = []
        for appointment in appointments:
            appointment = dict(appointment)
            try:
                appointment['date_time'] = datetime.strptime(appointment['date_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['date_time'] = datetime.strptime(appointment['date_time'], '%Y-%m-%dT%H:%M')
            try:
                appointment['end_date_time'] = datetime.strptime(appointment['end_date_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                appointment['end_date_time'] = datetime.strptime(appointment['end_date_time'], '%Y-%m-%dT%H:%M')
            parsed_appointments.append(appointment)

        return parsed_appointments
    finally:
        conn.close()
def migrate_appointments_table():
    conn = get_db_connection()
    try:
        conn.execute('''
        ALTER TABLE appointments ADD COLUMN package_id INTEGER
        ''')
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("La colonna 'package_id' esiste già.")
        else:
            print(f"Errore durante la migrazione: {e}")
    finally:
        conn.close()

def update_appointment(appointment_id, title, client_id, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero):
    """
    Aggiorna un appuntamento esistente nel database.
    """
    conn = get_db_connection()
    try:
        conn.execute('''
        UPDATE appointments
        SET title = ?,
            client_id = ?,          
            notes = ?, 
            date_time = ?, 
            end_date_time = ?, 
            appointment_type = ?, 
            status = ?, 
            is_trial = ?, 
            is_recovery = ?, 
            is_lesson_zero = ?
        WHERE id = ?
        ''', (title, client_id, notes, date_time, end_date_time, appointment_type, status, is_trial, is_recovery, is_lesson_zero, appointment_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiornamento dell'appuntamento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_appointments_by_sedi(sede_ids, start_date):
    """
    Recupera gli appuntamenti per un elenco di sedi a partire da una data specifica.
    
    :param sede_ids: Lista di ID delle sedi.
    :param start_date: Data di inizio (stringa in formato 'YYYY-MM-DD').
    :return: Lista di appuntamenti.
    """
    conn = get_db_connection()
    try:
        # Calcola la data di fine (7 giorni dopo la data di inizio)
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')

        # Costruisci la query per recuperare gli appuntamenti
        placeholders = ','.join('?' for _ in sede_ids)
        query = f'''
            SELECT 
                a.*, 
                c.nome || ' ' || c.cognome AS client_name, 
                t.nome || ' ' || t.cognome AS trainer_name
            FROM appointments a
            JOIN clienti c ON a.client_id = c.id
            JOIN trainer t ON a.trainer_id = t.id
            WHERE c.sede_id IN ({placeholders})
            AND a.date_time BETWEEN ? AND ?
            ORDER BY a.date_time ASC
        '''
        params = sede_ids + [start_date, end_date]
        appointments = conn.execute(query, params).fetchall()

        # Converte i risultati in un elenco di dizionari
        return [dict(appointment) for appointment in appointments]
    finally:
        conn.close()