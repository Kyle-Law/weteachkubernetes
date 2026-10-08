#!/usr/bin/env bash
# Point weteachkubernetes.com at the Pages project.
#
# The `wrangler login` OAuth token cannot do this: it has pages(write) and zone(read) but no
# DNS permission, so POST /dns_records returns 10000 Authentication error. This needs a token
# created at dash.cloudflare.com/profile/api-tokens with the "Edit zone DNS" template, scoped
# to this one zone. Delete it afterwards - it can repoint the domain.
#
#   source .env.deploy && export CF_API_TOKEN=...   &&   bash scripts/add-dns.sh
set -euo pipefail

: "${CF_ZONE_ID:?set CF_ZONE_ID (see .env.deploy, which is gitignored)}"
ZONE=$CF_ZONE_ID
: "${CF_API_TOKEN:?set CF_API_TOKEN first (Edit zone DNS, scoped to weteachkubernetes.com)}"

api() { curl -s -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" "$@"; }

# name -> pages project hostname
declare -a RECORDS=(
  "@:weteachkubernetes.pages.dev"
  "www:weteachkubernetes.pages.dev"
  "blog:weteachkubernetes-blog.pages.dev"
)

for REC in "${RECORDS[@]}"; do
  NAME="${REC%%:*}"; TARGET="${REC#*:}"
  echo "--- CNAME $NAME -> $TARGET"
  api -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
    --data "{\"type\":\"CNAME\",\"name\":\"$NAME\",\"content\":\"$TARGET\",\"proxied\":true,\"comment\":\"Pages: weteachkubernetes\"}" \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
if d.get('success'):
    r=d['result']; print('  created:',r['type'],r['name'],'->',r['content'],'| proxied:',r['proxied'])
else:
    errs=[(e.get('code'),e.get('message')) for e in d.get('errors',[])]
    print('  not created:',errs)
    # 81053/81058 mean a record already covers this name, which is fine.
    sys.exit(0 if any(c in (81053,81057,81058) for c,_ in errs) else 1)
"
done

echo
echo "waiting for DNS…"
for i in $(seq 1 24); do
  [ -n "$(dig +short weteachkubernetes.com)" ] && break
  sleep 5
done
dig +short weteachkubernetes.com | sed 's/^/  apex: /'
dig +short www.weteachkubernetes.com | sed 's/^/  www:  /'
echo
echo "waiting for the certificate…"
for i in $(seq 1 60); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://weteachkubernetes.com/" || true)
  [ "$CODE" = "200" ] && { echo "  https://weteachkubernetes.com is live"; exit 0; }
  sleep 10
done
echo "  still provisioning — certificate issuance can take a few minutes. Re-run the last check."
