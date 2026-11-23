# MD. Asif Hossain — Portfolio

[![Live Website](https://img.shields.io/badge/Website-dm--asif.github.io-9d3a52?style=for-the-badge)](https://dm-asif.github.io/)
[![React](https://img.shields.io/badge/React-19-20232A?style=for-the-badge&logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![GitHub Pages](https://img.shields.io/badge/Deployed-GitHub%20Pages-181717?style=for-the-badge&logo=github)](https://pages.github.com/)

The personal portfolio of **MD. Asif Hossain**, a Software Engineering student at Green University of Bangladesh.

**Live site:** https://dm-asif.github.io/

## Overview

This portfolio presents Asif's background, technical skills, projects, education, activities, and contact information in a responsive, dark maroon interface with liquid-glass visual effects.

## Features

- Responsive single-page portfolio
- Animated hero and page transitions
- Skills, projects, education, and activity sections
- Liquid-glass navigation with a frosted-glass fallback
- Direct CV viewing and download
- Email and social profile links
- EmailJS-powered contact form
- GitHub Pages deployment through GitHub Actions

## Built With

- React 19
- TypeScript
- Vite 8
- Tailwind CSS 4
- Framer Motion
- Lucide React
- EmailJS

## Getting Started

### Prerequisites

- Node.js 20 or later
- npm

### Installation

```bash
git clone https://github.com/dm-asif/dm-asif.github.io.git
cd dm-asif.github.io
npm ci
npm run dev
```

The development server will usually be available at `http://localhost:5173`.

### Production Build

```bash
npm run build
npm run preview
```

The production files are generated in `dist/`.

## Contact Form

The contact form uses EmailJS. Create a service and template in EmailJS, then copy `.env.example` to `.env.local` and set:

```env
VITE_EMAILJS_SERVICE_ID=your_service_id
VITE_EMAILJS_TEMPLATE_ID=your_template_id
VITE_EMAILJS_PUBLIC_KEY=your_public_key
```

Configure the EmailJS template to accept:

- `from_name`
- `from_email`
- `subject`
- `message`

Set the recipient address to `dmasif.me@gmail.com`.

> Use an EmailJS public key only. Never place a private API key or secret in a `VITE_` environment variable.

## CV

The CV is served from:

```text
public/assets/MD_Asif_Hossain_CV.pdf
```

## Project Assets

Project logos are stored in `public/assets/projects/`.

- HerCare: [dm-asif/HerCare](https://github.com/dm-asif/HerCare)
- Student OS: [dm-asif/Student-OS](https://github.com/dm-asif/Student-OS)

The liquid-glass implementation includes its MIT license at `public/LIQUID_GLASS_LICENSE.txt`.

## Deployment

Deployment is handled by `.github/workflows/deploy.yml`.

Every push to `main`:

1. Installs dependencies with `npm ci`
2. Builds the Vite application
3. Uploads `dist/` as a Pages artifact
4. Deploys the artifact to GitHub Pages

The workflow can also be started manually from the repository's **Actions** tab.

## Project Structure

```text
public/
  assets/          CV and project images
src/
  App.tsx          Portfolio content and page sections
  main.tsx         React entry point
  styles.css       Application styles
.github/
  workflows/       GitHub Pages deployment workflow
```

## Repository

- [GitHub Repository](https://github.com/dm-asif/dm-asif.github.io)
- [Live Portfolio](https://dm-asif.github.io/)
