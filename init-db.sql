-- Create database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'GYMTRACK')
BEGIN
    CREATE DATABASE GYMTRACK;
END
GO

USE GYMTRACK;
GO

-- Create login and user
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'gymtrack')
BEGIN
    CREATE LOGIN gymtrack WITH PASSWORD = 'gymtrack';
END
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'gymtrack')
BEGIN
    CREATE USER gymtrack FOR LOGIN gymtrack;
    ALTER ROLE db_owner ADD MEMBER gymtrack;
END
GO

-- Create sede table (referenced by clienti)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'sede')
BEGIN
    CREATE TABLE sede (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nome NVARCHAR(255) NOT NULL,
        indirizzo NVARCHAR(500),
        citta NVARCHAR(255),
        cap NVARCHAR(10),
        telefono NVARCHAR(50),
        email NVARCHAR(255)
    );
END
GO

-- Create clienti table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'clienti')
BEGIN
    CREATE TABLE clienti (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nome NVARCHAR(255) NOT NULL,
        cognome NVARCHAR(255) NOT NULL,
        email NVARCHAR(255),
        telefono NVARCHAR(50),
        data_nascita NVARCHAR(50),
        indirizzo NVARCHAR(500),
        citta NVARCHAR(255),
        cap NVARCHAR(10),
        note NVARCHAR(MAX),
        tipo NVARCHAR(50) NOT NULL,
        codice_fiscale NVARCHAR(50),
        data_registrazione NVARCHAR(50) NOT NULL,
        taglia_giubotto NVARCHAR(50),
        taglia_cintura NVARCHAR(50),
        taglia_braccia NVARCHAR(50),
        taglia_gambe NVARCHAR(50),
        obiettivo_cliente NVARCHAR(MAX),
        sede_id INT NOT NULL,
        FOREIGN KEY (sede_id) REFERENCES sede(id)
    );
END
GO

-- Create pacchetti table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'pacchetti')
BEGIN
    CREATE TABLE pacchetti (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nome NVARCHAR(255) NOT NULL,
        descrizione NVARCHAR(MAX),
        prezzo DECIMAL(10,2) NOT NULL,
        numero_lezioni INT NOT NULL,
        durata_giorni INT NOT NULL,
        attivo BIT NOT NULL DEFAULT 1,
        pagamento_unico BIT NOT NULL DEFAULT 0
    );
END
GO

-- Create abbonamenti table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'abbonamenti')
BEGIN
    CREATE TABLE abbonamenti (
        id INT IDENTITY(1,1) PRIMARY KEY,
        cliente_id INT NOT NULL,
        pacchetto_id INT NOT NULL,
        data_inizio DATE NOT NULL,
        data_fine DATE NOT NULL,
        numero_lezioni INT NOT NULL,
        lezioni_utilizzate INT DEFAULT 0,
        prezzo_totale DECIMAL(10,2) NOT NULL,
        numero_rate INT DEFAULT 1,
        FOREIGN KEY (cliente_id) REFERENCES clienti(id),
        FOREIGN KEY (pacchetto_id) REFERENCES pacchetti(id)
    );
END
GO

-- Create rate table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'rate')
BEGIN
    CREATE TABLE rate (
        id INT IDENTITY(1,1) PRIMARY KEY,
        abbonamento_id INT NOT NULL,
        importo DECIMAL(10,2) NOT NULL,
        data_scadenza DATE NOT NULL,
        data_pagamento DATE,
        pagato BIT DEFAULT 0,
        numero_rata INT NOT NULL,
        metodo_pagamento NVARCHAR(100),
        FOREIGN KEY (abbonamento_id) REFERENCES abbonamenti(id)
    );
END
GO

-- Insert a default sede for testing
IF NOT EXISTS (SELECT * FROM sede)
BEGIN
    INSERT INTO sede (nome, indirizzo, citta, cap, telefono, email)
    VALUES ('Sede Principale', 'Via Roma 1', 'Milano', '20100', '02-1234567', 'info@gym.com');
END
GO