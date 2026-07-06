COPY requirements.txt .

RUM pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["guni"]