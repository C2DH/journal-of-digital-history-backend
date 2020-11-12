FROM python:3.8.0-alpine
WORKDIR /journal-of-digital-history-backend

ARG GIT_TAG
ARG GIT_BRANCH
ARG GIT_REVISION

RUN pip install --upgrade pip

# COPY journal-of-digital-history-backend ./journal-of-digital-history-backend
# COPY manage.py .
COPY requirements.txt .

RUN pip install -r requirements.txt
RUN mkdir -p logs

ENV GIT_TAG=${GIT_TAG}
ENV GIT_BRANCH=${GIT_BRANCH}
ENV GIT_REVISION=${GIT_REVISION}

ENTRYPOINT python ./manage.py runserver
