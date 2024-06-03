FROM python:3.11.5 
WORKDIR /app
RUN apt-get update
COPY ..
COPY .env .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
