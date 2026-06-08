<script setup lang="ts">
import { RouterLink } from "vue-router"
</script>

<template>
  <section class="page container page--content">
    <header class="pagehead">
      <h1>Frequently Asked Questions</h1>
      <p class="pagehead__lead">
        Common questions about NerVault and using a custodial XNV wallet.
      </p>
    </header>

    <div class="faq">
      <details class="faq__item" open>
        <summary class="faq__q">
          What is NerVault?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            NerVault is a custodial web wallet for Nerva (XNV), a decentralized, peer-to-peer,
            open-source cryptocurrency. It lets you create or restore a wallet and send and receive
            XNV from your browser, with no software to install.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          How does it work?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            When you register, you choose to either generate a new Nerva wallet or restore an existing
            one from a seed. Your wallet is tied to your account, and each wallet runs in its own
            isolated process on the server that only you can reach once you are logged in. You can then
            view your balance, receive XNV, and send transactions.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          What does &ldquo;custodial&rdquo; mean, and is it safe?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            Custodial means NerVault holds your wallet files and the secret used to unlock them on the
            server, so it can operate the wallet on your behalf. That is convenient, but riskier than
            self-custody: while strong measures are in place, if the server were compromised those
            could be exposed. Once you are logged in, only you can use your wallet through the browser,
            but the operator technically has access to the underlying files and secrets. Web wallets
            are not recommended for significant balances — only keep what you are comfortable with.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          What information does NerVault store about me?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            Your email address and a hashed password, standard web server logs, a record of in-app
            actions you take, and — because it is custodial — your wallet files and the secret used to
            access them. See the
            <RouterLink to="/privacy">Privacy Policy</RouterLink> for the full breakdown.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          How do I move my funds somewhere safer?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            Use <b>Send XNV</b> to transfer to any Nerva address, including a wallet you run yourself.
            You can also reveal your mnemonic seed under <b>Wallet → View secrets</b> and import it
            into a self-custody CLI or GUI wallet.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          What happens to my wallet when I log out or leave it idle?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            To save resources, the live wallet process is shut down after your session expires (about
            an hour). Your wallet itself is preserved — it reconnects automatically the next time you
            open it. You can extend an active session at any time with the <b>Keep alive</b> button.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          How do I delete my wallet and data?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            <b>Wallet → Delete wallet</b> permanently removes your wallet data from the server. Make
            sure you have saved your seed first — this cannot be undone.
          </p>
        </div>
      </details>

      <details class="faq__item">
        <summary class="faq__q">
          What should I use instead?
          <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </summary>
        <div class="faq__a">
          <p>
            For the safest option, run your own wallet. Get the latest CLI or GUI from the
            <a href="https://nerva.one/downloads" target="_blank" rel="noopener">Nerva Downloads</a>
            page — anything you install on your own computer keeps you in full control. NerVault uses
            <code>nerva-wallet-cli</code> under the hood.
          </p>
        </div>
      </details>
    </div>

    <p class="faq__cta">
      <RouterLink to="/register">Create an account →</RouterLink>
    </p>
  </section>
</template>
