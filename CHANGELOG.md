# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 1.6.3 - 2022-05-29

### Fixed

  * Daily sub state check failed after first Rezident, and no mails were sent.


## 1.6.2 - 2022-04-02

### Fixed

  * Rezidents were not automatically unbanned when taking a new subscription;
  * Ban-related actions were not logged.


## 1.6.1 - 2022-03-08

### Changed

  * Device transfer is no longer necessary when using DOAS (now considered
    always as an external connection).

### Fixed

  * Rezidents list page: sort on account column did not work.


## 1.6.0 - 2022-02-17

### Added

  * Ban mechanism:
      * :class:`.models.Ban`, :meth:`.models.Rezident.current_ban` and
        :attr:`.models.Rezident.is_banned`;
      * New form for ban creation/modification in a modal in rezidents list;
      * :func:`.models.Device.allocate_ip_for` gives an address in the range
        ``10.0.8-255.0-255`` if the user is banned, storing the ban ID;
      * Banned page redirected to when IP in this range;
      * Navigation header red when banned;
      * Form validators for Rezident / Ban by ID;
      * Ban creation / deletion when subscription expires / is renewed.

### Changed

  * Default language for password reset is now French

### Fixed

  * ``PaymentStatus`` missing in ``.enums.__all__``;
  * :attr:`Rezident.first_seen` was not in UTC timezone.


## 1.5.0 - 2022-02-11

### Added

#### Payments

  * New tables :class:`.models.Subscription`, :class:`.models.Payment` and
    :class:`.models.Offer` to handle payments (see bottom left part of
    https://dbdiagram.io/d/60f9d116b7279e412336e4c1);
  * New convenient properties :attr:`~.models.Rezident.current_subscription`,
    :attr:`~.models.Rezident.old_subscriptions`,
    :attr:`~.models.Rezident.add_first_subscription` and
    :attr:`~.models.Rezident.first_seen` and method
    :meth:`~.models.Rezident.compute_sub_state`;
  * New blueprint ``payments`` with email support:
      * New page ``payments/main`` with informations about subscription and
        subscriptions history (added to navbar);
      * New page ``payments/pay`` where Rezidents can chose an offer and a
        payment method, leading to page ``payments/pay/<method>/<offer>``
        to "proceed to" payment. Available methods:
          * /lydia (Lydia / CB, form to chose and indicate mobile phone);
          * /transfer (bank transfer);
          * /cash (or other hand-to-hant transaction);
          * /magic (special for GRI to add arbitrary payments).
      * New route ``payments.add_payment/<offer>`` to GRI to add payments;
      * Lydia integration:
          * New routes ``payment.lydia_callback_[confirm/cancel]`` called by
            Lydia server once payment made / cancelled;
          * New routes ``payment.lydia_[success/fail]`` the user is redirected
            to after payment made / cancelled;
          * New routes ``payment.lydia_validate/<payment_id>`` used only if
            the callback did not work, to register payment in the Intrarez;
          * New module ``tools.lydia`` with Lydia API / utility functions;
          * New environment variables ``LYDIA_BASE_URL``,
            ``LYDIA_VENDOR_TOKEN`` and ``LYDIA_PRIVATE_TOKEN``;
      * New mails templates ``payments/new_subscription``,
        ``payments/subscription_expired``, ``payments/renew_reminder`` and
        ``payments/internet_cut``, ``payments.on_setup``;
  * First offer automatically subscribed if necessary during context creation;
  * Added payments info card to index;
  * Added Rezidents subscription state to GRI rezidents list;
  * Added data Enums handling in ``app/enums.py``,
    :class:`.enums.SubState` for subscription states and
    :class:`.enums.PaymentStatus` for payments status;
  * New script ``update_sub_state`` to be called every day to update
    Rezidents subscription state and send calendar-based mails;
  * New script ``update_offers`` holding basic offers data allowing to
    modify offers from source control;
  * New script ``setup_payments`` to add all first subscriptions and send
    information mails.

#### Mails, misc.

  * User locale is now stored:
      * New column :attr:`.models.Rezident.locale` checked before each request
        and updated if necessary;
      * This locale is used to build mails to the Rezident;
      * It is shown in GRI rezidents list;
  * Real-world email support:
      * HTML rich body (extends ``templates/mails_base.html``;
      * HTML body adapted to emails using :mod:`premailer`, through new
        functions :func:`email.init_premailer` (called before first request
        to set up options) and :func:`email.process_html`;
      * Plain-text body can now be constructed from HTML body using
        :mod:`html2text`, through new functions :func:`email.init_textifier`
        (called before first request to set up options) and
        :func:`email.html_to_plaintext`;
      * New mails-specific logger logging to ``logs/mails.log``;
      * Added ``List-Unsubscribe`` header to help message distribution;
      * Errors when sending mails are now reported as errors to the main
        logger (Discord alert);
      * New emails when creating an account (``auth/account_registered``)
        and when a rezident's room is transferred (``rooms/room_transferred``);
  * New promised rules ``profile.modify_account``, ``profile.update_password``,
    ``rooms.modify`` and ``devices.modify`` (and revealed buttons in profile
    page, cards...) and delete device button (but not implemented) ;
  * New GRI page ``run_script`` to execute scripts from the web interface;
  * New form validator for French phone numbers;
  * New maintenance mode (``MAINTENANCE`` environment variable and 503 page);
  * New attribute :attr:`flask.g.logged_in_user` as a shorthand for
    :attr:`flask_login.current_user` (ignores doas);
  * Type annotations!

### Changed

  * Moved route ``main.profile`` to new blueprint ``profile``, as
    ``profile.main``;
  * Current device shown in Profile for an external request is now a special
    pseudo-device with external IP;
  * :meth:`~.models.Rezident.other_devices` now includes current device if the
    request is not made internally, from this device;
  * Dropped :func:`.tools.utils.get_locale` in favor of
    :func:`flask_babel.get_locale`;
  * Moved ``auth.forms.promotions_list`` to :func:`tools.utils.promotions`,
    and it now has a cache mechanism to compute it once a day maximum, and
    returns a dict rather than a list of tuples;
  * Modified application logging (:mod:`.tools.loggers`):
      * Use timed-rotating instead of rotating, to keep all logs;
      * No more mail logging (redundant with mails transfer to Discord);
      * New sub-logger ``app.actions_logger`` (and
        :func:`.tools.utils.log_action`) to report to Discord (through
        webhook ``LOGGING_WEBHOOK``):
          * Account creation / modification;
          * Password change / reset;
          * Device registration / modification / transfer;
          * Rental creation / modification / termination;
          * Room transfer and forced rental termination (warning);
          * First subscription automatic add;
          * Subscription (and payment) add by GRI;
          * Daily sub state changes;
          * First offer / rooms creation, and offers update.
  * Displaying green progress bar on device/rental registration
    (and redirecting to connect check) is now done only if query argument
    ``hello`` is set (opt-in), not if ``force`` is NOT set as before;
  * Captive portal redirection is now managed by :func:`context.capture`;
  * 401 / 403 / 404 errors are no more reported to Discord, and IP is now
    reported;
  * Changed the way Darkstat and Bandwidthd monitoring systems are integrated
    to work under HTTPS; updated configuration models consequently (new
    environment variable ``GRI_BASIC_PASSWORD``);
  * "NEW" /star badges, ``bootstrap_icon`` and flashed messages toast
    are now set using Jinja macros written in ``app/templates/macros.html``;
  * "External link" icon is now shown for ``rel=external`` links rather
    than ``target=_blank`` ones;
  * Loading speed optimizations: small GRI logo image, deferred loading of
    ``moment.js`` (copied in ``static/js``), automatic gzip compression and
    of static files;
  * Discord webhooks are now sent in a separate thread;
  * Flask app is now a member of custom :class:`.IntraRezApp`;
  * Copyright is now defined in ``app/__init__.py``, centered below
    application name and updated to 2022.

### Removed

  * :meth:`.models.Rental.terminate` (2 lines of code called only once);
  * :func:`.utils.tools.get_bootstrap_icon` (replaced by macro);
  * :attr:`.models.Rezident.has_a_room` / :attr:`models.Rental.is_current`
    hybrid properties mechanism (properties on class, not used) and
    :attr:`models.Rental.is_currently_rented` (not used);
  * In Jinja context, ``bootstrap_is_hidden_field`` function (not used),
    ``alert_labels`` and ``alert_symbols`` dicts (integrated in macro).

### Fixed

  * Corrected flashed messages position on page and navbar menu display
    on small screens;
  * Trying to log with wrong credentials caused a 500 Internal Error;
  * Error report crashed if the error occurred too early (before setting up
    custom request context);
  * :mod:`context` decorators did not handle arguments in routes functions;
  * Password reset email was not send, and password reset page crashed;
  * :attr:`flask.g` context attributes were not modified when logging out,
    which could cause crashs;
  * Arbitrary ``doas`` query arguments could induce crashs;
  * A lot of small typos (especially in English translation) / style misses.


## 1.4.1 - 2021-12-21

### Fixed

  * Error report crashed if the error occurred too early (before setting up
    custom request context);
  * "Visit the Internet" button did not work.


## 1.4.0 - 2021-12-20

### Added

  * New module ``context.py`` with :func:`~.context.create_request_context`
    to define custom request context through :attr:`flask.g` attributes
    and route decorators :func:`~.context.all_good_only`,
    :func:`~.context.internal_only`, :func:`~.context.logged_in_only` and
    :func:`~.context.gris_only`,
  * New configuration options ``PREFERRED_URL_SCHEME``, ``SERVER_NAME`` and
    ``APPLICATION_ROOT`` to generate absolute URLs;
  * New configuration options ``FORCE_IP`` and ``FORCE_MAC``;
  * New 401 error page handler for internal-only pages;
  * New different home page for external requests;
  * Implementation of Google reCAPTCHA v2: module :mod:`.tools.captcha`,
    configuration options ``GOOGLE_RECAPTCHA_SITEKEY`` and
    ``GOOGLE_RECAPTCHA_SECRET``, and implementation in contact form if from
    outside;
  * Added pgAdmin link to GRI menu;
  * New util function :func:`.utils.safe_redirect`;
  * New script ``mail_hook.py`` to report incoming mail to Discord with
    new configuration option ``MAIL_WEBHOOK``;
  * New template ``templates/mails/base.html`` for emails HTML content;
  * Added dev branch display and setup in ``.env``;
  * New package requirements: ``python-dateutil``, ``premailer``.

### Changed

  * IntraRez is now adapted to a usage from the Internet (updated legal);
  * ``doas`` mechanism made global and not page-specific;
  * Account registration is now available from internal network only;
  * Moved ``auth_needed`` and ``connect_check`` routes to ``main`` blueprint;
  * Removed :func:`.app.devices.check_device`, :func:`.app.devices.get_mac`
    and :func:`.app.gris.gris_only` in favor of :mod:`context`;
  * GRI pages do not require device check anymore;
  * Moved admin addresses configuration from ``config.py`` to ``.env``.
  * Moved :func:`get_locale` from ``__init__.py`` to ``tools/utils.py``,
    and added it to Jinja env;
  * Informative cards shown on homepage, profile... are now built over a
    base template (``templates/cards/base.html``);
  * Moved JS tooltips triggering in a specific file.

### Fixed

  * Rezidents list ID sorting fix was not working.


## 1.3.0 - 2021-12-06

### Added

  * New table :class:`.models.Allocation` for IP allocations (per-room and
    per-room) to store reliably IPs
  * Show current device IP on device card;
  * Terminate rental action, allowing to declare a new rental;
  * "Doas" mechanism to allow GRI to manage rezidents rentals and devices;
  * Check if room is occupied when declaring a new rental, if yes print a
    warning popup;
  * New changelog page.

### Changed

  * Forms fields with an empty name are now not shown at all;
  * :func:`~.tools.utils.redirect_to_next` now accept URL parameters
    through keywords arguments.

### Fixed

  * Device MAC address duplication check was case-sensitive;
  * Display bug in profile card / GRI list when no rental;
  * Rezidents list ID sorting was alphabetical and not numerical.


## 1.2.0 - 2021-11-23

### Added

  * GRI menu: network monitoring through Darkstat and Bandwidthd;
  * Re-introduced ``Rezident.last_seen`` as a proxy to
    ``Rezident.current_device.last_seen``.

### Changed

  * GRI menu: rezidents list can now be sorted;
  * GRI menu dropdown has now its own template;
  * Device last connexion time is now shown even for the current device.

### Fixed

  * Device check routine sometimes crashed for new users;
  * ``Room.is_current`` could not be used as an expression.


## 1.1.1 - 2021-11-20

### Fixed

  * Captive portal could generate infinite redirection loops;
  * MAC address checks were case-sensitive;
  * Rezident last device and ``last_seen`` time were not correctly
    updated: made it per-device and made device ``last_seen`` nullable.


## 1.1.0 - 2021-11-14

### Added

  * Captive portal: serving homepage for requests to domains not
    in new environment variable ``NETLOCS``.

### Changed

  * Scripts now need to provide a ``main()`` function called by
    ``flask script``.

### Fixed

  * Generated usernames could contain non-alphanumeric characters;
  * Scripts were only run once (no re-import);
  * PastDate and FutureDate validators did not handle empty fields;
  * Typos in Makefile.


## 1.0.0 - 2021-11-13

### Added

  * New logs for DHCP hosts watcher and rickrollage.

### Fixed

  * Typos in Makefile / README.


## 0.8.0 - 2021-10-20

### Added

  * Watcher script for reloading DHCP server (new environment variable
    ``DHCP_HOSTS_FILE``, watcher job configuration in Supervisor
    configuration model).
  * Added an information message before DHCP rules.

### Changed

  * Traceback is now shown on error page depending on user status (GRI or
    not), regardless the app debug value.


## 0.7.0 - 2021-10-19

### Added

  * Scripts system and `flask script`.
  * `gen_dhcp.py` script for generating DHCP hosts rules, called at
    device register / transfer.

### Changed

  * Rezidents devices are sorted by ID.

### Fixed

  * Profile page crashed when several devices.


## 0.6.1 - 2021-10-18

### Changed

  * Globally renamed `user` table (and associated relationships) into
    `rezident` (reserved keyword in PostgreSQL).

### Fixed

  * Typos in Makefile / README and in Bower configuration file.


## 0.6.0 - 2021-10-17

### Added

  * Makefile rules for automatic installation (beta).
  * IntraRez is now a npm local package (easier dependencies installations).
  * Added custom logging messages on each request.
  * GRIs-only menu with users list.
  * New custom error page for 403 (GRI-only pages).
  * User last device last seen timestamp is now updated at each request.

### Changed

  * Application version is now retrieved from npm package information.
  * Different favicon depending on user permissions.
  * Moment.js is now a local dependency (instead of a web-loaded file).

### Fixed

  * Wrong label for "contact us" page email field.


## 0.5.0 - 2021-10-04

### Added

  * New Index page.
  * New Profile page listing account information, rooms and devices.
  * New convenience properties ``User.full_name``, ``User.current_device``,
    ``User.other_devices``, ``User.current_rental`` and ``User.old_rentals``.
  * Added ESPCI colors to Bootstrap-customized main colors.

### Changed

  * Login is now automatic on registration.
  * Automatically override names case when creating account.
  * Show registration progress bar on device transfer page, and not if
    ``force`` argument is set.
  * Replaces some basic fields with HTML5 fields.

### Fixed

  * Some endpoints were erroneous during registration process.
  * ``User.current_room`` returned a ``Rental`` and not a ``Room``.


## 0.4.0 - 2021-10-03

### Added

  * Room registration (new ``Room`` and ``Rental`` models).
  * Room check integrated in registration process.
  * Rezidence rooms created automatically if table empty.
  * Connection check page, integrated in registration process (new Bower
    dependency: webping-js).
  * Global progress bar in registration process.
  * Past / Future Date form validators.
  * New utility function ``get_bootstrap_icon`` to facilite icons integration.

### Changed

  * New favicon
  * New 404 / other errors pages.

### Fixed

  * Discord report of app errors.


## 0.3.1 - 2021-09-30

### Changed

  * Minor style changes, Bootstrap customization tests

### Fixed

  * Critical bug in routing handling
  * Louis Grandvaux name


## 0.3.0 - 2021-09-29

### Added

  * Device detection, registration and transfer (new ``Device`` model).
  * Device check on each request, redirecting to the appropriate page.
  * Extended ``User`` model with first / last names and promotion.
  * Automatic username construction form first and last names.
  * Automatic promotion list built from current year.
  * Utility function ``tools.utils.redirect_to_next``.
  * MAC address and Length form validators.

### Changed

  * External links now open in a new tab.
  * Bootstrap is now provided as an external dependency, not included.
  * CSS is now generated from SCSS files, allowing Bootstrap customization.

### Fixed

  * Form input custom classes were ignored in some cases.


## 0.2.0 - 2021-09-26

### Added

  * Contact us page with contact form and Discord integration.
  * Legal notice page.
  * New footer on all pages.
  * Room number form validator.
  * 405 error page.

### Changed

  * Renamed `app._tools` module to `app.tools` (issues with Flask-Babel)
  * Minor style improvements.


## 0.1.1 - 2021-09-25

### Changed

  * Integrated Bootstrap directly in project files.
  * Upgraded flashed messages display using Bootstrap toasts.
  * Other various style improvements.

### Fixed

  * Crash when redirecting to login page.
  * Errors in Nginx / Supervisor configuration models.


## 0.1.0 - 2021-09-17

First working application, with basic Flask structure.
No IntraRez-specific features.
