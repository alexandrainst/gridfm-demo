FROM flwr/superexec:1.23.0

COPY pyproject.toml ./
RUN python -m pip install -U --no-cache-dir .

ENTRYPOINT ["flower-superexec"]
