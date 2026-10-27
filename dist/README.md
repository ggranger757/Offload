# Offload

A private, installable feed for notes, checklists and reminders. Everything is stored on the device (localStorage); nothing is sent to a server.

## Run it
Any static host works, but it must be served over HTTPS (or localhost) for install and offline support.

    cd dist && python3 -m http.server 8080   # then open http://localhost:8080

Free hosting: drag the `dist` folder onto Netlify Drop, or push it to GitHub Pages / Cloudflare Pages / Vercel.

## Install on a phone
- iPhone (Safari): Share → Add to Home Screen.
- Android (Chrome): menu → Install app.

## Features
- Notes, checklists (one item per line; end the first line with ":" to title it) and reminders with repeat days.
- #tags become filter chips; full-text search; pin, edit, copy, delete.
- Share sheet target on Android: share a link or text into Offload to prefill a note.
- Light/dark/system theme, Sans/Serif/Mono font, JSON backup and import.
- Works offline after the first visit.

## Limits worth knowing
- Reminders fire while the app is open or in the background tab; a fully closed PWA cannot schedule alarms without a push server.
- Siri capture: deploy the inbox server in /server (free Cloudflare plan), then follow Settings → Siri in the app.
- Data lives on one device. Use Settings → Copy backup to move it. Adding sync (Supabase/Firebase) and SMS capture (Twilio inbound webhook) is the next step if you want MindChuk-style texting.
