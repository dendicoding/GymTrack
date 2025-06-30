# Use the official Microsoft SQL Server image
FROM mcr.microsoft.com/mssql/server:2019-latest

# Set environment variables for SQL Server
ENV ACCEPT_EULA=Y
ENV SA_PASSWORD=StrongPassword123!
ENV MSSQL_PID=Express

# Switch to root to install additional tools
USER root

# Install sqlcmd and other utilities
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    gnupg2 \
    apt-transport-https \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add sqlcmd to PATH
ENV PATH="$PATH:/opt/mssql-tools/bin"

# Create directory for SQL scripts
RUN mkdir -p /usr/src/app

# Copy initialization script
COPY init-db.sql /usr/src/app/

# Create a script to initialize the database
RUN echo '#!/bin/bash' > /usr/src/app/initialize-db.sh && \
    echo 'sleep 30' >> /usr/src/app/initialize-db.sh && \
    echo '/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P StrongPassword123! -i /usr/src/app/init-db.sql' >> /usr/src/app/initialize-db.sh && \
    chmod +x /usr/src/app/initialize-db.sh

# Switch back to mssql user
USER mssql

# Expose SQL Server port
EXPOSE 1433

# Start SQL Server and run initialization
CMD /opt/mssql/bin/sqlservr & /usr/src/app/initialize-db.sh & wait
