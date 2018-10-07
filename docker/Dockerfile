FROM python:3.6.2

# Metadata
LABEL container.base.image="python:3.6.2"
LABEL software.name="daily_digest_alexa"
LABEL software.version="1.0.0"
LABEL software.description="A lazy way to crunch the latest Chinese news"
LABEL software.website="https://github.com/haoeric/Alexa-skill-Daily-Digest"
LABEL software.documentation="https://github.com/haoeric/Alexa-skill-Daily-Digest"
LABEL software.license="GPLv3 or later"
LABEL maintainer="Hao Chen <haoeric@hotmail.com>"
LABEL tags="daily_digest_alexa"

# Set the destination directory for softwares installation
ENV DST=/tmp

# Do a few updates of the base system and install R (via the r-base package)
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y zlib1g-dev gnuplot && \
    apt-get install -y unzip gcc libncurses5-dev && \
    apt-get install -y git && \
    apt-get clean

# install python 2.7 modulars
RUN pip install boto3 awscli scrapy

# copy scripts from host to image
COPY src /daily_digest

# export scrapy crawler setting and path
ENV SCRAPY_SETTINGS_MODULE readhub_news_crawler.settings
ENV PYTHONPATH /daily_digest/readhub_news_crawler

# install xunfei tts
RUN cd /daily_digest/xunfei_tts/mytts/ && \
    bash /daily_digest/xunfei_tts/mytts/64bit_make.sh

ENV LD_LIBRARY_PATH /daily_digest/xunfei_tts/libs/x64/

## install lame
RUN cd /daily_digest/lame-3.100/ && \
    make -f Makefile.unix

# export env path
ENV PATH /usr/local/bin:$PATH
ENV PATH /daily_digest/xunfei_tts/bin:$PATH
ENV PATH /daily_digest/lame-3.100/frontend:$PATH

RUN chmod 555 /daily_digest/*

# create ENTRYPOINT
ENTRYPOINT ["python", "/daily_digest/auto_news_loader.py"]





