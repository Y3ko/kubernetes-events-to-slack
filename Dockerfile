FROM python:3.9-alpine

# Gerekli paketleri kur
RUN apk add --no-cache --virtual .build-deps build-base \
    && apk add --no-cache libffi-dev gcc musl-dev \
    && pip install dumb-init==1.2.5 \
    && apk del .build-deps

# Uygulama için bir dizin oluştur ve gerekli dosyaları kopyala
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
RUN pip install --upgrade kubernetes
# Ana Python dosyasını kopyala
COPY k8s-events-to-slack-streamer.py /app/

# Yeni bir kullanıcı oluştur ve uygulama klasörüne sahip olmasını sağla
RUN addgroup -S app && adduser -S -G app app
RUN chown -R app:app /app
USER app

# Çalışma dizini ve giriş noktası ayarla
WORKDIR /app
ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]
CMD ["python3", "/app/k8s-events-to-slack-streamer.py"]
