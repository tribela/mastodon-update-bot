FROM python:3.9

ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=1
ENV PYTHONFAULTHANDLER=1

WORKDIR /src
COPY poetry.lock pyproject.toml /src/
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi \
    && pip uninstall --yes poetry
ADD . /src

RUN useradd -m user
USER user

CMD ["python", "-u", "-m", "bot"]
