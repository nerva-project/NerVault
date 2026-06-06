from wtforms import StringField, BooleanField
from quart_wtf import QuartForm
from wtforms.validators import Email, Optional, DataRequired, ValidationError

from library.validation import (
    validate_seed as check_seed,
    is_valid_username,
)


class Register(QuartForm):
    """Form for registering a new user."""

    username: StringField
    email: StringField
    password: StringField
    confirm_password: StringField
    faq_reviewed: BooleanField
    terms_reviewed: BooleanField
    privacy_reviewed: BooleanField

    username = StringField(
        "Username:",
        validators=[DataRequired()],
        render_kw={"placeholder": "Username", "class": "form-control"},
    )
    email = StringField(
        "Email Address:",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Email", "class": "form-control", "type": "email"},
    )
    password = StringField(
        "Password:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Password",
            "class": "form-control",
            "type": "password",
        },
    )
    confirm_password = StringField(
        "Confirm Password:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Confirm Password",
            "class": "form-control",
            "type": "password",
        },
    )
    faq_reviewed = BooleanField(
        "FAQ Reviewed:",
        validators=[DataRequired()],
        render_kw={"class": "form-control-span"},
    )
    terms_reviewed = BooleanField(
        "Terms of Service Reviewed:",
        validators=[DataRequired()],
        render_kw={"class": "form-control-span"},
    )
    privacy_reviewed = BooleanField(
        "Privacy Policy Reviewed:",
        validators=[DataRequired()],
        render_kw={"class": "form-control-span"},
    )
    # recaptcha = RecaptchaField()

    def validate_username(self, _: object) -> None:
        """Normalise to lowercase and enforce the allowed username charset."""

        if self.username.data:
            self.username.data = self.username.data.strip().lower()

        if not is_valid_username(self.username.data or ""):
            raise ValidationError(
                "Username must be 3-32 characters long and contain only "
                "lowercase letters, digits, or underscores."
            )


class Login(QuartForm):
    """Form for logging in a user."""

    username: StringField
    password: StringField

    username = StringField(
        "Username:",
        validators=[DataRequired()],
        render_kw={"placeholder": "Username", "class": "form-control"},
    )
    password = StringField(
        "Password:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Password",
            "class": "form-control",
            "type": "password",
        },
    )
    # recaptcha = RecaptchaField()


class Reset(QuartForm):
    """Form for resetting the user's password."""

    email: StringField

    email = StringField(
        "Email Address:",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Email", "class": "form-control", "type": "email"},
    )
    # recaptcha = RecaptchaField()


class ResetPassword(QuartForm):
    """Form for setting a new password after reset."""

    password: StringField
    confirm_password: StringField

    password = StringField(
        "Password:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "New Password",
            "class": "form-control",
            "type": "password",
        },
    )
    confirm_password = StringField(
        "Confirm Password:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Confirm Password",
            "class": "form-control",
            "type": "password",
        },
    )


class Secrets(QuartForm):
    """Form for entering a password to access secrets."""

    password: StringField

    password = StringField(
        "Enter your password:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Password",
            "class": "form-control",
            "type": "password",
        },
    )


class Restore(QuartForm):
    """Form for restoring a wallet using a seed phrase."""

    seed: StringField
    confirm: BooleanField

    seed = StringField(
        "Seed Phrase",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "25 word mnemonic seed phrase",
            "class": "form-control",
        },
    )
    confirm = BooleanField(
        "I agree:",
        validators=[DataRequired()],
        render_kw={"class": "form-control-span"},
    )

    def validate_seed(self, _: object) -> None:
        """Validate that the seed phrase is a standard 25-word Nerva mnemonic."""

        if not self.seed.data:
            raise ValidationError("Seed phrase is required")

        try:
            self.seed.data = check_seed(self.seed.data.lower())

        except ValueError:
            raise ValidationError(
                "Invalid seed phrase provided; must be a standard 25-word "
                "Nerva mnemonic seed phrase."
            ) from None


class Send(QuartForm):
    """Form for sending funds from a wallet."""

    address: StringField
    amount: StringField
    payment_id: StringField

    address = StringField(
        "Destination Address:",
        validators=[DataRequired()],
        render_kw={"placeholder": "Nerva address", "class": "form-control"},
    )
    amount = StringField(
        "Amount:",
        validators=[DataRequired()],
        render_kw={
            "placeholder": 'Amount to send or "all"',
            "class": "form-control",
        },
    )
    payment_id = StringField(
        "Payment ID (Optional):",
        validators=[Optional()],
        render_kw={
            "placeholder": "16 or 32 character payment ID",
            "class": "form-control",
        },
    )


class Delete(QuartForm):
    """Form for confirming wallet deletion."""

    confirm: BooleanField

    confirm = BooleanField(
        "Confirm Wallet Deletion:",
        validators=[DataRequired()],
        render_kw={"class": "form-control-span"},
    )
