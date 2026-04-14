FROM python:3.14-slim


RUN pip install --upgrade pip

WORKDIR /app
RUN pip install markdown-it-py markdownify nicegui pyyaml rich-click
COPY . ./
RUN pip install .

EXPOSE 80
RUN mkdir -p /root/Documents/Notely
ENTRYPOINT ["python", "notely", "server", "start"]