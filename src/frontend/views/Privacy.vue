<script setup lang="ts"></script>

<template>
  <section class="page container page--content legal">
    <header class="pagehead">
      <h1>Privacy Policy</h1>
      <p class="pagehead__lead">Last updated 8 June 2026</p>
    </header>

    <section>
      <h2>1. Information we collect</h2>
      <ul class="checklist">
        <li>Your email address and a hashed password (your password is never stored in plaintext).</li>
        <li>Standard web server logs, such as your IP address, browser user agent, and the pages you request.</li>
        <li>
          A record of in-app actions you take (for example, creating, connecting, or deleting a
          wallet), stored together with your username.
        </li>
      </ul>
    </section>

    <section>
      <h2>2. Your wallet data</h2>
      <p>
        Because NerVault is a custodial wallet, it stores your wallet files and the secret used to
        access them on its servers, so the wallet can be operated on your behalf.
      </p>
    </section>

    <section>
      <h2>3. How we use it</h2>
      <p>
        We use this information only to operate the service: to authenticate you, run your wallet,
        send account emails (confirmation and password reset), troubleshoot issues, and protect
        against abuse.
      </p>
    </section>

    <section>
      <h2>4. Third-party services</h2>
      <ul class="checklist">
        <li>
          At sign-up, your email address is checked against a disposable-email detection service
          (block-temporary-email.com) to block throwaway addresses.
        </li>
        <li>Confirmation and password-reset emails are delivered through an email (SMTP) provider.</li>
        <li>
          Market price shown on the site is fetched from CoinGecko; none of your information is sent
          to them.
        </li>
      </ul>
      <p>We do not sell your data or share it for advertising.</p>
    </section>

    <section>
      <h2>5. Data retention</h2>
      <p>
        Logs and event records are retained for troubleshooting and security. Deleting your wallet
        removes your wallet data from our servers.
      </p>
    </section>

    <section>
      <h2>6. Security</h2>
      <p>
        Reasonable measures are taken to protect your data, but no online service is completely
        secure — and as a custodial wallet, the operator can technically access your wallet secrets.
        Please do not store more than you can afford to lose.
      </p>
    </section>
  </section>
</template>
