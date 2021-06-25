FROM python:3.9.2-slim

RUN apt update && apt install -y build-essential

WORKDIR /tmp/project

COPY . /tmp/project

RUN pip install -r requirements.txt

CMD ["jupyter", "notebook", "--allow-root", "--ip", "0.0.0.0", "--port", "8888"]