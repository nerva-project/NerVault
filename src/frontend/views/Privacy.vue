<script setup lang="ts">
import PageHeader from "../components/ui/PageHeader.vue"
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[680px] mx-auto">
    <PageHeader title="Privacy Policy" lead="What NerVault collects, and how it's used." />

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">1. Information we collect</h2>
      <ul class="mt-4 list-none flex flex-col gap-[0.85rem]">
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">Your email address and a hashed password (your password is never stored in plaintext).</li>
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">Standard web server logs, such as your IP address, browser user agent, and the pages you request.</li>
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">
          A record of in-app actions you take (for example, creating, connecting, or deleting a
          wallet), stored together with your username.
        </li>
      </ul>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">2. Your wallet data</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        Because NerVault is a custodial wallet, it stores your wallet files and the secret used to
        access them on its servers, so the wallet can be operated on your behalf.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">3. How we use it</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        We use this information only to operate the service: to authenticate you, run your wallet,
        send account emails (confirmation and password reset), troubleshoot issues, and protect
        against abuse.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">4. Third-party services</h2>
      <ul class="mt-4 list-none flex flex-col gap-[0.85rem]">
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">
          At sign-up, your email address is checked against a disposable-email detection service
          (block-temporary-email.com) to block throwaway addresses.
        </li>
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">Confirmation and password-reset emails are delivered through an email (SMTP) provider.</li>
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">
          Market price shown on the site is fetched from CoinGecko; none of your information is sent
          to them.
        </li>
      </ul>
      <p class="mb-3 last:mb-0 text-text-dim">We do not sell your data or share it for advertising.</p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">5. Data retention</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        Logs and event records are retained for troubleshooting and security. Deleting your wallet
        removes your wallet data from our servers.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">6. Security</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        Reasonable measures are taken to protect your data, but no online service is completely
        secure — and as a custodial wallet, the operator can technically access your wallet secrets.
        Please do not store more than you can afford to lose.
      </p>
    </section>
  </section>
</template>
