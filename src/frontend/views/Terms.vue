<script setup lang="ts">
import PageHeader from "../components/ui/PageHeader.vue"
</script>

<template>
  <section class="flex-[1_0_auto] pt-10 pb-16 w-full max-w-[680px] mx-auto">
    <PageHeader title="Terms of Service" lead="The agreement you accept by using NerVault." />

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">1. Acceptance of these terms</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        By creating an account or using NerVault, you agree to be bound by these terms. If you do not
        agree, please do not use the service.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">2. The service</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        NerVault is a custodial web wallet for Nerva (XNV). It lets you create or restore a wallet and
        send and receive XNV from your browser. Because it is custodial, NerVault stores your wallet
        files and the secret used to access them on its servers so the wallet can be operated on your
        behalf.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">3. Your responsibilities</h2>
      <ul class="mt-4 list-none flex flex-col gap-[0.85rem]">
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">Keep your account credentials secure; you are responsible for all activity under your account.</li>
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">
          Always back up your mnemonic seed yourself — you can retrieve it any time from
          <strong>Wallet → View secrets</strong>. NerVault is not a backup service for your funds.
        </li>
        <li class="relative pl-[1.6rem] text-text-dim before:content-[''] before:absolute before:left-[0.2rem] before:top-[0.55em] before:size-[7px] before:rounded-full before:bg-accent">Do not deposit more than you are willing to lose.</li>
      </ul>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">4. Risks and no warranty</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        Web wallets carry inherent risks and are not recommended for significant balances. NerVault is
        provided on an &ldquo;as is&rdquo; and &ldquo;as available&rdquo; basis, without warranties of
        any kind, express or implied. You use the service only if you accept these risks.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">5. Limitation of liability</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        To the maximum extent permitted by law, NerVault and its operators shall not be liable for any
        loss of cryptocurrency or for any direct, indirect, or consequential damages arising from your
        use of, or inability to use, the service, for any reason.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">6. Acceptable use</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        You agree not to use NerVault for any unlawful purpose, and not to attempt to disrupt, attack,
        or gain unauthorized access to the service, its infrastructure, or other users' wallets.
      </p>
    </section>

    <section class="mt-7 first-of-type:mt-0">
      <h2 class="text-[1.15rem] mb-[0.6rem]">7. Changes to these terms</h2>
      <p class="mb-3 last:mb-0 text-text-dim">
        These terms may be updated from time to time. Continued use of the service after a change
        means you accept the current version.
      </p>
    </section>
  </section>
</template>
