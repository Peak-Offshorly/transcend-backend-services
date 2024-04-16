# 
FROM python:3.10

# 
WORKDIR /transcend-backend-services

# 
COPY ./requirements.txt /transcend-backend-services/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /transcend-backend-services/requirements.txt

# 
COPY ./app /transcend-backend-services/app

# 
COPY ./transcend-service-account-key.json /transcend-backend-services/transcend-service-account-key.json

COPY ./.env /transcend-backend-services/.env

# 
CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]