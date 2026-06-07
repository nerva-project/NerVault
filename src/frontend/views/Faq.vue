<script setup lang="ts">
import { RouterLink } from "vue-router"
</script>

<template>
  <section class="page container page--narrow prose">
    <h1>Frequently Asked Questions</h1>

    <h2>What is this website?</h2>
    <p>
      NerVault lets you send and receive Nerva (XNV) — a decentralized, peer-to-peer, open-source
      digital currency — directly from your browser.
    </p>

    <h2>How does it work?</h2>
    <p>
      When you register, you choose to either generate a new Nerva wallet or restore an existing one
      from a seed. When you log in, your wallet is mapped to your account so that you can only ever
      interact with your own wallet in the browser. You can then send XNV and view your transactions.
    </p>

    <h2>Is it safe?</h2>
    <p>
      Every measure has been taken to secure this application. That said, web wallets in general are
      not recommended: there are many attack vectors and possible ways to bypass security. Even
      though you control the seed, this is technically a <b>custodial</b> wallet, because we hold the
      wallet files and the secrets used to access them. If someone were to compromise the server,
      they could potentially gain access to them too. If you are willing to accept these risks, web
      wallets make it very easy and convenient to get started — but you have to trust the service.
    </p>

    <h2>What should I use instead?</h2>
    <p>
      Check the
      <a href="https://nerva.one/downloads" target="_blank" rel="noopener">Nerva Downloads</a> page
      for the most recent software wallets (CLI/GUI). Anything you can install on your own computer
      is the safest bet. This website uses <code>nerva-wallet-cli</code> under the hood; you should
      use that.
    </p>

    <p style="margin-top: 2rem">
      <RouterLink to="/register">Create an account →</RouterLink>
    </p>
  </section>
</template>
