FROM obolibrary/odkfull

COPY requirements.txt /tools/ontie-requirements.txt
RUN pip install -r /tools/ontie-requirements.txt

RUN apt-get install -y aha
