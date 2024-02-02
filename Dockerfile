FROM obolibrary/odklite

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install tzdata
RUN apt-get install -y postgresql git aha

COPY requirements.txt /tools/ontie-requirements.txt
RUN pip install -r /tools/ontie-requirements.txt
