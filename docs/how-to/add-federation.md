# How to Add a Federation

This guide shows you how to add a federation, a set of clients with their own synthetic
grid data, so that you can run experiments on it with `gridfm`.

Prerequisites:

- Docker with Docker Compose
- The project dependencies, installed with `uv sync`

## Steps

1. Choose a name `<name>` for the federation. It becomes the folder name and the Docker
   Compose project name, so use lowercase letters, digits and underscores, such as
   `case30_3clients`.

2. Create a folder for the federation:

   ```bash
   mkdir -p federations/<name>/datakit_config
   ```

3. Write one [gridfm-datakit](https://github.com/gridfm/gridfm-datakit) config per
   client in `federations/<name>/datakit_config/`. Write as many as the experiments you
   plan to run need. Name them `client_0.yaml`, `client_1.yaml` and so on, counting
   from 0. In each config:
   - Set `network.name` to the grid of that client, such as `case14_ieee`.
   - Set `settings.data_dir` to `federations/<name>/data/client_<i>`, where `<i>` is the
     number in the file name.
   - Set `settings.seed` to a value no other client uses, unless you want two clients
     with identical data.

   If you want the clients to differ in more than their seed, change their load,
   topology, generation or admittance settings. Refer to `docs/examples/datakit/` and
   the gridfm-datakit documentation for all options.

4. Generate the data for every client:

   ```bash
   uv run gridfm data <name>
   ```

   The data is written to `federations/<name>/data/`, which Git ignores. Clients that
   already have data are skipped. If you change a config afterwards, run
   `uv run gridfm data <name> --force` to regenerate the data.

5. Count the scenarios for each client. It is the number of `data_index_*.pt` files in
   `federations/<name>/data/client_<i>/<network.name>/processed/`, or `load.scenarios`
   times `topology_perturbation.n_topology_variants` from the config:

   ```bash
   ls federations/<name>/data/client_0/<network.name>/processed/data_index_*.pt | wc -l
   ```

6. Write `federations/<name>/compose.yml` with the SuperLink, the ServerApp and their
   network. Do not set a top-level `name:`, so that Docker Compose names the project
   after the folder and `gridfm` can tell whether the federation is up:

   ```yaml
   services:
     superlink:
       image: flwr/superlink:1.23.0
       command: [--insecure, --isolation, process]
       ports:
         - "127.0.0.1:9093:9093"
       networks:
         - flwr-network

     serverapp:
       image: gridfm-flower-serverapp:1.23.0
       build:
         context: ../../build/server
       command:
         [--insecure, --plugin-type, serverapp, --appio-api-address, superlink:9091]
       volumes:
         - ../../outputs/<name>:/outputs
       networks:
         - flwr-network
       depends_on:
         - superlink

   networks:
     flwr-network:
       driver: bridge
   ```

7. Add a SuperNode and a ClientApp under `services:` for each client, and replace the
   placeholders in them:

   | Placeholder | Replace with                   | Client 0      |
   | ----------- | ------------------------------ | ------------- |
   | `<i>`       | Number in the config file name | `0`           |
   | `<n>`       | `<i>` plus 1                   | `1`           |
   | `<port>`    | 9094 plus `<i>`                | `9094`        |
   | `<network>` | `network.name` of the client   | `case14_ieee` |
   | `<count>`   | Scenario count from step 5     | `40`          |

   ```yaml
   supernode-<n>:
     image: flwr/supernode:1.23.0
     command:
       - --insecure
       - --superlink
       - superlink:9092
       - --clientappio-api-address
       - 0.0.0.0:<port>
       - --isolation
       - process
       - --node-config
       - "client-id=<i> data-dir='/data/client_<i>' networks='<network>'
         scenarios='<count>'"
     networks:
       - flwr-network
     depends_on:
       - superlink

   clientapp-<n>:
     image: gridfm-flower-clientapp:1.23.0
     build:
       context: ../../build/client
     command:
       - --insecure
       - --plugin-type
       - clientapp
       - --appio-api-address
       - supernode-<n>:<port>
     environment:
       OMP_NUM_THREADS: 1
       MKL_NUM_THREADS: 1
     volumes:
       - ./data/client_<i>:/data/client_<i>
     networks:
       - flwr-network
     depends_on:
       - serverapp
       - supernode-<n>
   ```

   Leave out `build:` in every ClientApp except `clientapp-1`, so that the image is
   built once. If a client has several networks, list their names in `networks` and
   their scenario counts in `scenarios`, separated by commas and in the same order.

8. Do not change a client ID after the first run. An experiment can use the ID, for
   example to seed training, so a new ID can change the results of later runs.

9. Describe the federation under `### Federations` in `README.md`: its grid, its number
   of clients and how their data differs.

## Confirm the Federation Works

Start the federation and list its containers:

```bash
uv run gridfm up <name>
docker compose -f federations/<name>/compose.yml ps
```

You should see `superlink`, `serverapp` and one `supernode-<i+1>` and `clientapp-<i+1>`
per client, all running. If `gridfm up` stops with a list of clients without data, run
step 4 again.

Then run an experiment and check that its results appear in
`outputs/<name>/<experiment>/`:

```bash
uv run gridfm run <experiment>
```

Stop the federation when you are done:

```bash
uv run gridfm down <name>
```
