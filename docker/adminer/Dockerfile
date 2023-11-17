FROM adminer:latest

MAINTAINER Patrick Artounian <partounian@gmail.com>

USER root

RUN mkdir -p /usr/local/etc/php/conf.d

# Store PHP Configs at /usr/local/etc/php/conf.d
RUN echo "upload_max_filesize = 500M" >> /usr/local/etc/php/conf.d/upload_large_dumps.ini \
    && echo "post_max_size = 500M"       >> /usr/local/etc/php/conf.d/upload_large_dumps.ini \
    && echo "memory_limit = -1"           >> /usr/local/etc/php/conf.d/upload_large_dumps.ini \
    && echo "max_execution_time = 0"      >> /usr/local/etc/php/conf.d/upload_large_dumps.ini

# Add volume for sessions to allow session persistence
VOLUME /sessions

USER adminer

# We expose Adminer on port 8080 (Adminer's default)
EXPOSE 8080

command: [ "php", "-d", "upload_max_filesize = 10G", "-d", "post_max_size = 10G", "-S", "[::]:8080", "-t", "/var/www/html" ]
