FROM debian:stretch-slim

MAINTAINER Gluu Inc. <support@gluu.org>

RUN echo "deb http://ftp.de.debian.org/debian sid main " >> /etc/apt/sources.list

#Required for openJDK-8
RUN mkdir -p /usr/share/man/man1

RUN apt-get upgrade -y  \
    && apt-get update -y  \
    && apt-get install -y\
    git \
    ca-certificates-java \
    openjdk-8-jre-headless \
    wget \
    python-pip \ 
    python-dev \
    libffi-dev \
    libssl-dev \
    redis-server  \
    && pip install --upgrade \
    setuptools \
    influxdb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create keypair 

RUN mkdir -p $HOME/.ssh \
    && ssh-keygen -b 2048 -t rsa -q -f /~/.ssh/ -N ""  \
# Download and install Cluster Manager
    && git clone https://github.com/GluuFederation/cluster-mgr.git \
    && cd clustermgr/   \
    && python setup.py install

# Prepare database and license enforcement requirements
RUN clustermgr-cli db upgrade  \
    && mkdir -p $HOME/.clustermgr/javalibs \
    && wget http://ox.gluu.org/maven/org/xdi/oxlicense-validator/3.2.0-SNAPSHOT/oxlicense-validator-3.2.0-SNAPSHOT-jar-with-dependencies.jar -O $HOME/.clustermgr/javalibs/oxlicense-validator.jar  \
    && mkdir $HOME/.clustermgr/

EXPOSE 5000

#Run the program
RUN clustermgr-beat & clustermgr-celery & clustermgr-cli run

