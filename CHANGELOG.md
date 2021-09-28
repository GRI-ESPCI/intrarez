# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 0.3.0 - 2021-09-29

# Added

  * Device detection, registration and transfer (new ``Device`` model).
  * Device check on each request, redirecting to the appropriate page.
  * Extended ``User`` model with first / last names and promotion.
  * Automatic username construction form first and last names.
  * Automatic promotion list built from current year.
  * Utility function ``tools.utils.redirect_to_next``.
  * MAC address and Length form validators.

# Changed

  * External links now open in a new tab.

# Fixed

  * Form input custom classes were ignored in some cases.


## 0.2.0 - 2021-09-26

# Added

  * Contact us page with contact form and Discord integration.
  * Legal notice page.
  * New footer on all pages.
  * Room number form validator.
  * 405 error page.

# Changed

  * Renamed `app._tools` module to `app.tools` (issues with Flask-Babel)
  * Minor style improvements.


## 0.1.1 - 2021-09-25

# Changed

  * Integrated Bootstrap directly in project files.
  * Upgraded flashed messages display using Bootstrap toasts.
  * Other various style improvements.

# Fixed

  * Crash when redirecting to login page.
  * Errors in Nginx / Supervisor configuration models.


## 0.1.0 - 2021-09-17

First working application, with basic Flask structure.
No IntraRez-specific features.
