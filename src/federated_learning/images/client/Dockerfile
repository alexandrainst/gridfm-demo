FROM flwr/superexec:1.23.0

USER root
RUN apt-get update && apt-get install -y --no-install-recommends git g++ python3-dev

RUN pip install torch==2.14.0
RUN pip install torch-scatter --no-build-isolation
# pyproject.toml pins pandas < 3. Pandas 3 defaults to Copy-on-Write, so
# df[cols].values returns a read-only view over the internal block. Then
# gridfm-graphkit's torch.tensor(branch_df[[...]].values.T, ...) call in
# HeteroGridDatasetDisk.process() fails with a negative-strides ValueError.
# Drop the pin once graphkit stops handing raw pandas views to torch.tensor.
COPY pyproject.toml ./
RUN pip install .

ENTRYPOINT ["flower-superexec"]
