# PortUI 🖥️✨

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach) [![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach) [![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)

A lightweight, Docker-powered portfolio/landing-page generator—fully customizable via YAML! Showcase your projects, skills, and online presence in minutes.  

![PortUI screenshot](assets/img/screenshot.png)

> 🚀 You can also pair PortUI with JavaScript for sleek, web-based desktop-style interfaces.  
> 💻 Example in action: [CyMaIS.Cloud](https://cymais.cloud/) (demo)  
> 🌐 Another live example: [veen.world](https://www.veen.world/) (Kevin’s personal site)

---

## ✨ Key Features

- **Dynamic Navigation**  
  Create dropdowns & nested menus with ease.  
- **Customizable Cards**  
  Highlight skills, projects, or services—with icons, titles, and links.  
- **Smart Cache Management**  
  Auto-cache assets for lightning-fast loading.  
- **Responsive Design**  
  Built on Bootstrap; looks great on desktop, tablet & mobile.  
- **184 Languages**  
  Every ISO 639-1 code, browser-negotiated, RTL-aware, with machine translation for your own content.  
- **YAML-Driven**  
  All content & structure defined in a simple `config.yaml`.  
- **CLI Control**  
  Manage Docker containers via the `portfolio` command.

---

## 🌐 Quick Access

- **Local Preview:**  
  [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🏁 Getting Started

### 🔧 Prerequisites

- Docker & Docker Compose  
- Basic Python & YAML knowledge  

### 🛠️ Installation via Git

1. **Clone & enter repo**  
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Configure**
   Copy `config.sample.yaml` → `config.yaml` & customize.
3. **Build & run**

   ```bash
   docker-compose up --build
   ```
4. **Browse**
   Open [http://localhost:5000](http://localhost:5000)

### 📦 Installation via Kevin’s Package Manager

```bash
pkgmgr install portui
```

Once installed, the `portui` CLI is available system-wide.

---

## 🖥️ CLI Commands

```bash
portui --help
```

* `build` Build the Docker image
* `up` Start containers (with build)
* `down` Stop & remove containers
* `run-dev` Dev mode (hot-reload)
* `run-prod` Production mode
* `logs` View container logs
* `dev` Docker-Compose dev environment
* `prod` Docker-Compose prod environment
* `cleanup` Prune stopped containers

---

## 🔧 YAML Configuration Guide

Define your site’s structure in `config.yaml`:

```yaml
accounts:
  name: Online Accounts
  description: Discover my online presence.
  icon:
    class: fa-solid fa-users
  children:
    - name: Channels
      description: Platforms where I share content.
      icon:
        class: fas fa-newspaper
      children:
        - name: Mastodon
          description: Follow me on Mastodon.
          icon:
            class: fa-brands fa-mastodon
          url: https://microblog.veen.world/@kevinveenbirkenbach
          identifier: "@kevinveenbirkenbach@microblog.veen.world"
  cards:
    - icon:
        source: https://cloud.veen.world/s/logo_agile_coach_512x512/download
      title: Agile Coach
      text: I lead agile transformations and improve team dynamics through Scrum and Agile Coaching.
      url: https://www.agile-coach.world
      link_text: www.agile-coach.world

company:
  title: Kevin Veen-Birkenbach
  subtitle: Consulting & Coaching Solutions
  logo:
    source: https://cloud.veen.world/s/logo_face_512x512/download
  favicon:
    source: https://cloud.veen.world/s/veen_world_favicon/download
  address:
    street: Afrikanische Straße 43
    postal_code: DE-13351
    city: Berlin
    country: Germany
  imprint_url: https://s.veen.world/imprint
```

* **`children`** enables multi-level menus.
* **`link`** references other YAML paths to avoid duplication.

---

## 🌍 Languages

Every ISO 639-1 language — all 184 two-letter codes — has a URL, a display
name in its own script and a writing direction. The interface ships translated
for 29 of them; the rest fall back to English string by string until a
catalogue is filled. `/` serves the best match for the visitor's
`Accept-Language` header, `/<code>/` forces one, and a switcher in the navbar
lists them all. The ten right-to-left languages get `dir="rtl"` and Bootstrap's RTL
stylesheet automatically.

Translations live in two catalogues, both keyed by the English source string:

| Path | Tracked | Holds |
| --- | --- | --- |
| `app/i18n/ui/<code>.yaml` | yes | Interface strings. Shipped for 29 languages; English is the source and has no file. |
| `app/i18n/content/<code>.yaml` | no | Your `config.yaml` prose, generated per deployment. |

A string with no catalogue entry falls back to English, so a half-filled
catalogue degrades instead of breaking.

Fill the content catalogues from a [LibreTranslate](https://libretranslate.com/)
instance — set `LIBRETRANSLATE_URL` in `.env`, then:

```bash
make i18n
```

This fills the interface strings of the languages that ship no catalogue as
well. Existing entries are never overwritten, and a string the shipped
catalogue already covers is never requested, so corrections you make by hand
survive later runs.

`name`, `title`, `description`, `text`, `warning`, `info` and `subtitel` are
translated; `url`, `link_text`, `identifier` and icon classes never are.

A machine cannot tell the menu label "Pictures" from the brand "Mastodon", so
list the brands in `app/i18n/keep.txt`, one per line — they are then stored as
themselves in every language and cost no request:

```
# Strings utils/i18n_sync.py stores as themselves instead of translating.
Mastodon
Nextcloud
freelancermap.de
```

Add one-off entries with `--keep Foo Bar`, or point somewhere else with
`--keep-file`. A protected string never replaces an entry you already wrote by
hand.

---

## 🚢 Production Deployment

* Use a reverse proxy (NGINX/Apache).
* Secure with SSL/TLS.
* Swap to a production database if needed.

Because every page carries a canonical URL and 184 `hreflang` alternates, two
details of the proxy setup now matter:

* **Set `TRUSTED_HOSTS`** in `.env` to your public hostname(s), comma-separated.
  Left empty, the app reflects whatever `Host` header arrives into its canonical,
  `hreflang` and redirect URLs — so a shared cache in front of it can be made to
  store a redirect pointing somewhere else.
* **Have the proxy send `X-Forwarded-Proto`.** Without it the app cannot know TLS
  terminated upstream and every canonical URL claims `http://`. `X-Forwarded-Host`
  is deliberately *not* trusted; set `Host` to the public name instead.

---

## 📜 License

Licensed under **GNU AGPLv3**. See [LICENSE](./LICENSE) for details.

---

## ✍️ Author

Created by [Kevin Veen-Birkenbach](https://www.veen.world/)

Enjoy building your portfolio! 🌟
