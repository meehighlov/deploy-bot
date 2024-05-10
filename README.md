# deploy-bot

## current dependencies layout for virtual machinie

```shell
ssh root@{vm-public-ip-address}
```

```shell
cd /etc/{component_name} # executable code
```

```shell
cd /etc/systemd/system/{component_name}.service  # unit file
```

```shell
cd /root/.cache/pypoetry/virtualenvs/{poetry-hash}/bin/python  # virtual env executor
```

```shell
cd /etc/secrets{component_name}  # envs for components
```
