FROM obolibrary/odkfull

COPY requirements.txt /tools/ontie-requirements.txt
RUN pip install -r /tools/ontie-requirements.txt

RUN add-apt-repository ppa:git-core/ppa
RUN apt-get update
RUN apt-get install -y git

RUN apt-get install -y aha
