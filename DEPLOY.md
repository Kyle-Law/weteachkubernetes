# Deploying weteachkubernetes.com

Two phases. **Phase 1 puts the site live and needs no credentials beyond your Cloudflare
login.** Phase 2 turns on sign-in and one-click contributions, and needs a GitHub App that
only you can create.

Everything in `public/` is verified working locally. `AUTH_ENABLED` in `public/index.html`
is `false`, so nothing on the live site points at an endpoint that does not exist yet.

---

## Phase 1 - the site, live on the domain

### 1. Log in to Cloudflare

```sh
npx wrangler login
```

Opens a browser. I cannot do this step for you: it is an interactive consent screen, and the
token it writes belongs to your account. Confirm it worked:

```sh
npx wrangler whoami            # should show kylelaw1121@gmail.com
```

### 2. Create the Pages project and deploy

```sh
npx wrangler pages project create weteachkubernetes --production-branch=main
npx wrangler pages deploy public --project-name=weteachkubernetes
```

The second command prints a `*.pages.dev` URL. Open it. That is the real site.

### 3. Point the domain at it

Wrangler 4 has no `pages domain` command, so this is either the dashboard
(**Workers & Pages -> weteachkubernetes -> Custom domains -> Set up a custom domain**) or the
API directly:

```sh
source .env.deploy        # CF_ACCOUNT_ID, CF_ZONE_ID
for D in weteachkubernetes.com www.weteachkubernetes.com; do
  curl -s -X POST \
    "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/pages/projects/weteachkubernetes/domains" \
    -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
    --data "{\"name\":\"$D\"}"
done
```

**Gotcha hit on the first run:** the `POST /domains` call succeeds and the domain shows up on
the project as `pending`, but the CNAME is *not* created if the calling token lacks
`dns_records:write`. The `wrangler login` OAuth token has `pages (write)` and `zone (read)`
only, so the two records have to be added separately - dashboard, or an API token with
**Zone -> DNS -> Edit**:

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `@` | `weteachkubernetes.pages.dev` | Proxied |
| CNAME | `www` | `weteachkubernetes.pages.dev` | Proxied |

Apex CNAMEs are fine here - Cloudflare flattens them. Once the records exist, validation
flips to active and the certificate issues within a few minutes.

Then check it resolves and serves:

```sh
dig +short weteachkubernetes.com
curl -sI https://weteachkubernetes.com | head -3
```

### 4. Analytics, without a cookie banner

Dashboard -> **Analytics & Logs -> Web Analytics -> Add a site**. It gives you a snippet with
a token. Paste it just before `</body>` in `public/index.html`, and add
`https://static.cloudflareinsights.com` to the `script-src` and `connect-src` lists in
`public/_headers`. It sets no cookies, so no banner is needed.

**Phase 1 is done.** The roadmap is public and indexable, and contributions arrive as
hand-written pull requests against `public/data/roadmap.json`.

---

## Phase 2 - sign-in, synced progress, one-click contributions

### 1. Put the repo on GitHub

```sh
git init -b main
git add .
git commit -m "weteachkubernetes.com: roadmap, data and deploy config"
gh repo create weteachkubernetes --public --source=. --push
```

### 2. KV, for sessions and progress

Already done - both namespaces exist and their ids are in `wrangler.toml`:

Both ids are in `wrangler.toml`. They are bindings, not credentials - a namespace id is
useless without an authenticated token, which is why Cloudflare's own docs commit them.

`/api/me` already answers `{"handle":null}` on the live site, which means the binding and the
session code work against the real runtime. What is missing is only the GitHub App.

### 3. Create the GitHub App

**GitHub -> Settings -> Developer settings -> GitHub Apps -> New GitHub App**

| Field | Value |
|---|---|
| Name | `weteachkubernetes-site` |
| Homepage URL | `https://weteachkubernetes.com` |
| Callback URL | `https://weteachkubernetes.com/api/auth/callback` |
| Request user authorization (OAuth) during installation | off |
| Webhook | uncheck **Active** |
| Repository permissions | **Contents: Read & write**, **Pull requests: Read & write**, **Issues: Read & write** |
| Account permissions | none |
| Where can it be installed | Only on this account |

Create it, then:

- **Generate a private key** - downloads a `.pem`. Keep it out of the repo.
- **Install App** -> only the `weteachkubernetes` repository. The URL you land on ends in
  `/installations/<number>`; that number is your installation id.
- Note the **App ID** and the **Client ID**, and **generate a client secret**.

A GitHub App rather than a personal access token because its installation token is scoped to
this one repo, expires in an hour, and can be revoked without touching your own account.

### 4. Set the secrets

```sh
P=weteachkubernetes
npx wrangler pages secret put GITHUB_CLIENT_ID       --project-name=$P
npx wrangler pages secret put GITHUB_CLIENT_SECRET   --project-name=$P
npx wrangler pages secret put GITHUB_APP_ID          --project-name=$P
npx wrangler pages secret put GITHUB_INSTALLATION_ID --project-name=$P
npx wrangler pages secret put GITHUB_APP_PRIVATE_KEY --project-name=$P < path/to/key.pem
```

None of these belong in the repo or in `wrangler.toml`. For local testing put them in
`.dev.vars`, which `.gitignore` already excludes.

### 5. Flip the flag and ship

In `public/index.html`, change `const AUTH_ENABLED=false;` to `true`, then:

```sh
npm run deploy
```

### 6. Check it end to end

```sh
curl -sI https://weteachkubernetes.com/api/auth/start | grep -i location   # 302 to github.com
curl -s  https://weteachkubernetes.com/api/me                              # {"handle":null}
npm run tail                                                               # live logs
```

Then sign in through the site, tick a checkpoint, reload in a private window and sign in
again - the tick should follow you. Submit a tutorial and confirm the PR appears with a
`Co-authored-by` trailer.

The functions have never run against real credentials, so expect to fix something on the
first attempt. `npm run tail` is where the error will be.

---

## Keeping it honest

- `npm run check` validates the data files, and CI runs it on every pull request: every
  tutorial credits a known handle, every tag is registered, every URL is https.
- **Never auto-merge** a submitted pull request. The review is the only editorial control
  this site has.
- Rotate the client secret and the private key if either ever lands in a log, a screenshot
  or a pasted terminal.
- `/api/progress` stores per-account data, which is the first point where you hold data about
  other people. `DELETE /api/progress` already removes it; say so on a short privacy page
  before the first real user signs in.
