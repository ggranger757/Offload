# Offload inbox server (for Siri capture)

A tiny Cloudflare Worker that receives what you say to Siri and holds it until the Offload app picks it up.
Runs on Cloudflare's free plan. Stores only a SHA-256 hash of each capture key, and deletes each item once the app has synced it.

## Deploy (about 5 minutes)

You need a free Cloudflare account and Node.js 18 or newer.

    cd server
    npm install
    npx wrangler login                 # opens a browser to sign in to Cloudflare
    npm run db:create                  # prints a database_id
    # paste that database_id into wrangler.toml
    npm run db:schema                  # creates the table
    npm run deploy                     # prints your address, e.g. https://offload-inbox.yourname.workers.dev

Open that address in a browser: it should say "Offload capture inbox is running."

## Connect the app

Either paste the address into Offload → Settings → Siri → Inbox server address,
or bake it into the build so every user gets it automatically:

    OFFLOAD_SERVER=https://offload-inbox.yourname.workers.dev python3 build.py

## API

All requests need `Authorization: Bearer <capture key>` (the key shown in the app's Settings).

| Request | Body | Response |
|---|---|---|
| `POST /capture` | JSON `{"text": "..."}`, form field `text`, or plain text | `Saved to Offload.` (Siri reads this out) |
| `GET /inbox` | | `{"items":[{"id","text","source","created"}]}` |
| `DELETE /inbox` | `{"ids": [...]}` | `{"deleted": n}` |

Limits: 4,000 characters per capture, 500 unsynced items per key.

## Skip the manual Shortcut setup for your users

Build the shortcut once on your own iPhone following the steps in the app, then:
1. In the shortcut's details, add an **Import Question** for the Authorization header value
   (prompt: "Paste your capture key from Offload → Settings → Siri", default "Bearer ").
2. Share it as an iCloud link.
3. Put that link on your site or in the app. Users tap it, paste their key once, and they're done.
