// Don't put any keys in code. See https://docs.stripe.com/keys-best-practices.
// Find your keys at https://dashboard.stripe.com/apikeys.
Stripe.apiKey = "{{TEST_SECRET_KEY}}";

AccountCreateParams params =
  AccountCreateParams.builder()
    .setCountry("US")
    .setController(
      AccountCreateParams.Controller.builder()
        .setStripeDashboard(
          AccountCreateParams.Controller.StripeDashboard.builder()
            .setType(AccountCreateParams.Controller.StripeDashboard.Type.NONE)
            .build()
        )
        .setFees(
          AccountCreateParams.Controller.Fees.builder()
            .setPayer(AccountCreateParams.Controller.Fees.Payer.APPLICATION)
            .build()
        )
        .setLosses(
          AccountCreateParams.Controller.Losses.builder()
            .setPayments(AccountCreateParams.Controller.Losses.Payments.APPLICATION)
            .build()
        )
        .setRequirementCollection(
          AccountCreateParams.Controller.RequirementCollection.APPLICATION
        )
        .build()
    )
    .setCapabilities(
      AccountCreateParams.Capabilities.builder()
        .setTransfers(
          AccountCreateParams.Capabilities.Transfers.builder().setRequested(true).build()
        )
        .setCardIssuing(
          AccountCreateParams.Capabilities.CardIssuing.builder()
            .setRequested(true)
            .build()
        )
        .setTreasury(
          AccountCreateParams.Capabilities.Treasury.builder().setRequested(true).build()
        )
        .setUsBankAccountAchPayments(
          AccountCreateParams.Capabilities.UsBankAccountAchPayments.builder()
            .setRequested(true)
            .build()
        )
        .build()
    )
    .build();

Account account = Account.create(params);

