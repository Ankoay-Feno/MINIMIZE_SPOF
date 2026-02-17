FROM alpine:3.20

RUN apk add --no-cache pgpool postgresql16-client bash

COPY pgpool.conf /etc/pgpool/pgpool.conf

EXPOSE 5432

CMD ["pgpool", "-n", "-f", "/etc/pgpool/pgpool.conf"]
