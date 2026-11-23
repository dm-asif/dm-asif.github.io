# MD. Asif Hossain Portfolio

A responsive React + Vite portfolio, preserving the supplied profile, education, activities, skills, and project content with a dark maroon liquid glass visual system.

## Run locally

```sh
npm ci
npm run dev
```

Create a production build with `npm run build`.

## Project logos

The Projects page uses optimized copies of the app logos from the [HerCare repository](https://github.com/dm-asif/HerCare) and [Student OS repository](https://github.com/dm-asif/Student-OS).

## Liquid glass navigation

The header uses the [liquid-glass](https://github.com/deepika-builds/liquid-glass) refraction effect in supported Chromium browsers, with a frosted blur fallback elsewhere. Its MIT license is included at `public/LIQUID_GLASS_LICENSE.txt`.

## Contact form setup

The form sends through EmailJS. Create an EmailJS service and template, set the template recipient to `dmasif.me@gmail.com`, and make the template use these fields:

- `from_name`
- `from_email`
- `subject`
- `message`

Copy `.env.example` to `.env.local` and provide the service ID, template ID, and EmailJS **public** key. Add the same values to your hosting provider's build environment. The public key is expected to be visible in the browser; do not put a private key or secret in any `VITE_` variable. Without these settings the form reports that setup is incomplete and points visitors to the direct email address.

## CV file

Place the supplied CV at `public/assets/MD_Asif_Hossain_CV.pdf`. The hero section links to that file for viewing and downloading. The supplied project archive did not contain a CV PDF, so the file must be added before those controls can serve it.
