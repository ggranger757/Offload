import json, re, pathlib
from PIL import Image, ImageDraw
import os
src = pathlib.Path('app.html').read_text()
if os.environ.get('OFFLOAD_SERVER'): src = src.replace('__OFFLOAD_SERVER__', os.environ['OFFLOAD_SERVER'].rstrip('/'))
d = pathlib.Path('dist')
head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#ECEFF3">
<meta name="description" content="A private feed for everything you don't want to forget.">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Offload">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box;color-scheme:light}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
'''
src = src.replace('<div id="app">', '</head>\n<body>\n<div id="app">', 1)
(d/'index.html').write_text(head + src + '\n</body>\n</html>\n')

manifest = {
 "name":"Offload","short_name":"Offload",
 "description":"A private feed for everything you don't want to forget.",
 "start_url":"./","scope":"./","display":"standalone",
 "background_color":"#ECEFF3","theme_color":"#ECEFF3",
 "icons":[
  {"src":"icons/icon-192.png","sizes":"192x192","type":"image/png"},
  {"src":"icons/icon-512.png","sizes":"512x512","type":"image/png"},
  {"src":"icons/maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}],
 "share_target":{"action":"./","method":"GET","params":{"title":"title","text":"text","url":"url"}},
 "shortcuts":[{"name":"New note","url":"./"}]
}
(d/'manifest.webmanifest').write_text(json.dumps(manifest, indent=2))

(d/'sw.js').write_text('''// Offload service worker: caches the app shell so it opens offline.
const CACHE = 'offload-v1';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (req.mode === 'navigate') {
    // Network first for the page, so updates arrive; fall back to the cached shell offline.
    e.respondWith(fetch(req).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put('./index.html', copy)); return r; })
      .catch(() => caches.match('./index.html')));
    return;
  }
  // Cache first for everything else (icons, fonts).
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok && (req.url.startsWith(self.location.origin) || req.url.includes('fonts.g'))) {
      const copy = r.clone(); caches.open(CACHE).then(c => c.put(req, copy));
    }
    return r;
  }).catch(() => hit)));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: 'window' }).then(cs => cs.length ? cs[0].focus() : self.clients.openWindow('./')));
});
''')

def icon(size, pad_frac, name, radius=True):
    S = size*4
    im = Image.new('RGBA', (S,S), (0,0,0,0) if radius else (47,67,224,255))
    dr = ImageDraw.Draw(im)
    if radius: dr.rounded_rectangle([0,0,S-1,S-1], radius=int(S*0.22), fill=(47,67,224,255))
    p = S*pad_frac
    # speech bubble
    bx0,by0,bx1,by1 = p, p*1.05, S-p, S-p*1.35
    dr.rounded_rectangle([bx0,by0,bx1,by1], radius=int((by1-by0)*0.32), fill=(255,255,255,255))
    tw = (bx1-bx0)*0.16
    dr.polygon([(bx0+(bx1-bx0)*0.22,by1-2),(bx0+(bx1-bx0)*0.22+tw,by1-2),(bx0+(bx1-bx0)*0.16,by1+tw*0.9)], fill=(255,255,255,255))
    # three lines of text + yellow dot
    lh = (by1-by0)*0.11; lx = bx0+(bx1-bx0)*0.17
    for i,w in enumerate([0.62,0.46]):
        y = by0+(by1-by0)*(0.32+i*0.24)
        dr.rounded_rectangle([lx,y,lx+(bx1-bx0)*w,y+lh], radius=int(lh/2), fill=(19,22,28,255))
    r = (by1-by0)*0.11; cx = bx1-(bx1-bx0)*0.2; cy = by0+(by1-by0)*0.62
    dr.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(255,227,107,255), outline=(19,22,28,255), width=int(r*0.35))
    im.resize((size,size), Image.LANCZOS).save(d/'icons'/name)
icon(192,0.2,'icon-192.png'); icon(512,0.2,'icon-512.png')
icon(512,0.27,'maskable-512.png',radius=False); icon(180,0.2,'apple-touch-icon.png',radius=False)

(d/'README.md').write_text('''# Offload

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
''')
