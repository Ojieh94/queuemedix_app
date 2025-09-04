""""
.env.local (file name)
ENV=local

DATABASE_URL= postgresql+asyncpg://postgres:prevaildb@localhost:5432/queuemed
JWT_SECRET=fe7f374a3dbff97577a63ceb17acbf03e6962cd87b8ea6975aab0e8bfc26c86c
JWT_ALGORITHM = HS256
EMAIL_SERVER= smtp.zoho.com
EMAIL_PORT=587
EMAIL_USERNAME=noreply@queuemedix.com
EMAIL_PASSWORD=Queuemedix@20$
EMAIL_FROM=noreply@queuemedix.com
MAIL_FROM_NAME= QueueMedix
REDIS_URL = redis://redis:6379/0
DOMAIN = localhost:8000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=queuemedix
POSTGRES_PORT=5432

I'M NOT SURE YOU WILL BE NEEDING THE LOCAL .ENV CAUSE YOU WILL BASICALLY WORKING WITH DOCKER DUE TO THE EXTRA SERVICES.



.env.docker (file name)
ENV=docker

DATABASE_URL= postgresql+asyncpg://postgres:postgres@db:5432/queuemedix
JWT_SECRET=fe7f374a3dbff97577a63ceb17acbf03e6962cd87b8ea6975aab0e8bfc26c86c
JWT_ALGORITHM = HS256
EMAIL_SERVER= smtp.zoho.com
EMAIL_PORT=465
EMAIL_USERNAME=noreply@queuemedix.com
EMAIL_PASSWORD=Queuemedix@20$
EMAIL_FROM=noreply@queuemedix.com
MAIL_FROM_NAME= QueueMedix
REDIS_URL = redis://redis:6379/0
DOMAIN = localhost:8000

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=queuemedix
POSTGRES_PORT=5432

"""