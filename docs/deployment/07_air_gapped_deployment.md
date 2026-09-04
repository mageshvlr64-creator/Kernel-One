# Air-Gapped Deployment

> Concrete deployment procedure for `NETWORK_MODE=air_gapped`
> (`architecture/17_air_gapped_architecture.md`).

## Procedure

1. On a machine WITH internet access, download all required container images, model weights,
   and dependency packages; verify checksums.
2. Transfer to the target air-gapped host via physical media or an approved one-way transfer
   mechanism (organization-specific, out of this specification's scope).
3. On the target host, load container images (`docker load`), place model weights at the
   configured path, install packages from the local bundle (never `pip install`/`npm install`
   reaching out live).
4. Physically disconnect or firewall the host's network interface before starting services.
5. Set `NETWORK_MODE=air_gapped`, run `02_startup.md`.
6. Verify via the Network Sovereignty Panel (`ui/13_network_panel.md`) and, ideally, an
   independent packet capture on the physical network segment, that zero external traffic
   occurs during a full smoke-test session.

## Ongoing operation

No live package/model updates in this mode — any update repeats steps 1-3 as a new deployment
cycle, never a live pull.
