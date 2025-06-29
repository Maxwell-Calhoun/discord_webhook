FROM python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# explicitly copy env variables just in case :)
COPY .env .

# Port should be the same as .env port variable
EXPOSE 8000

CMD [ "python", "./main.py" ]