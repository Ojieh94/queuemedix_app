FROM python:3.11-slim

# set workdir
WORKDIR /usr/src/app

# install system deps
RUN apt-get update && apt-get install -y build-essential 

# copy dependencies
COPY requirements.txt .

# install dependencies
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# copy app
COPY . .

# default command (can be overridden by docker-compose)
CMD ["uvicorn", "src:app", "--host", "0.0.0.0", "--port", "8000"]
