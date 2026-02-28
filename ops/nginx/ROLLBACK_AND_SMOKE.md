# E4 Rollback and Smoke (VPN-safe)

## Pre-checks
1. Backup current config:
```bash
TS=$(date +%Y%m%d-%H%M%S)
cp /root/vpnbot/config/override.conf /root/vpnbot/config/override.conf.bak-$TS
```
2. Add ONLY new server blocks for site/api domains.

## Apply
```bash
docker exec nginx-server nginx -t
# if OK:
docker exec nginx-server nginx -s reload
```

## Smoke
```bash
curl -I https://site.teplo-v-arkhyze.ru
curl -I https://api.teplo-v-arkhyze.ru/health
```

## Rollback
```bash
cp /root/vpnbot/config/override.conf.bak-<TS> /root/vpnbot/config/override.conf
docker exec nginx-server nginx -t && docker exec nginx-server nginx -s reload
```

## Hard rule
- Never edit VPN core `location.conf` and default wildcard route blocks.
