from __future__ import annotations

from blueprints.auth import auth_bp

import datetime
from asyncio import sleep

import aiohttp
from quart import flash, request, url_for, redirect, current_app, render_template
from quart_auth import login_user, logout_user, current_user, login_required
from quart.typing import ResponseReturnValue

from utils.mail import send_email
from utils.forms import Login, Reset, Delete, Register, ResetPassword
from utils.models import User
from utils.tokens import generate_token, validate_token
from utils.factory import bcrypt, docker, schema
from library.helpers import capture_event


@auth_bp.route("/register", methods=["GET", "POST"])
async def _register() -> ResponseReturnValue:
    """
    Handles user registration process, including form validation,
    email confirmation, and user account creation.

    Returns:
        ResponseReturnValue: Redirect to the appropriate page after registration or rendering the registration template.
    """
    form = await Register().create_form()

    if await current_user.is_authenticated:
        return redirect(url_for("wallet._dashboard"))

    if await form.validate_on_submit():
        user = User(username=form.username.data)
        try:
            await user.load()
            await flash("This email is already registered.", "warning")
            return redirect(url_for("auth._login"))

        except ValueError:
            pass

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://block-temporary-email.com/check/email/{form.email.data}",
                headers={
                    "x-api-key": current_app.config.get("TEMP_MAIL_BLOCK_API_KEY")
                },
            ) as res:
                if res.status != 200:
                    pass

                if (await res.json())["temporary"]:
                    await flash(
                        "Registrations with temporary disposable emails are not allowed.",
                        "error",
                    )

                    form.email.data = None
                    form.password.data = None
                    form.confirm_password.data = None
                    return await render_template(
                        "auth/register.html", form=form, scroll=True
                    )

        if not schema.validate(form.password.data):
            await flash(
                "Password must be at least 8 characters, and must contain "
                "at least one uppercase, one lowercase, one digit, and a symbol.",
                "warning",
            )

            form.password.data = None
            form.confirm_password.data = None
            return await render_template(
                "auth/register.html", form=form, scroll=True
            )

        if not form.password.data == form.confirm_password.data:
            await flash("Passwords do not match.", "warning")

            form.password.data = None
            form.confirm_password.data = None
            return await render_template(
                "auth/register.html", form=form, scroll=True
            )

        user = User(username=form.username.data)
        user.email = form.email.data
        user.password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf8"
        )
        await user.save()

        token = generate_token(user.email)
        confirm_url = url_for("auth._confirm", token=token, _external=True)
        template = await render_template(
            "auth/email/activate.html", confirm_url=confirm_url
        )
        await send_email(user.email, "Account Activation", template)

        await capture_event(user.username, "register")
        login_user(user)

        await flash(
            "A confirmation email has been sent. Please check Junk/Spam folders.",
            "success",
        )
        return redirect(url_for("auth._unconfirmed"))

    return await render_template("auth/register.html", form=form)


@auth_bp.route("/confirm/<token>", methods=["GET"])
async def _confirm(token: str) -> ResponseReturnValue:
    """
    Confirms the user's account using the provided token.

    Args:
        token (str): The confirmation token.

    Returns:
        ResponseReturnValue: Redirect to the appropriate page after confirmation.
    """
    email = validate_token(token)

    try:
        user = await User.get_by_email(email)

        if not email:
            raise ValueError

    except ValueError:
        await flash(
            "The confirmation link is either invalid or has expired.", "error"
        )
        return redirect(url_for("auth._login"))

    if user.confirmed:
        await flash("Account already confirmed.", "info")

    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        await user.save()

        await capture_event(user.username, "confirmed")
        await flash("You have successfully confirmed your account.", "success")

    return redirect(url_for("wallet._setup"))


@auth_bp.route("/unconfirmed", methods=["GET"])
@login_required
async def _unconfirmed() -> ResponseReturnValue:
    """
    Displays the unconfirmed account page if the user hasn't confirmed their email.

    Returns:
        ResponseReturnValue: Renders the unconfirmed page if the user is not confirmed.
    """
    if current_user.confirmed:
        return redirect(url_for("wallet._setup"))

    return await render_template("auth/unconfirmed.html")


@auth_bp.route("/resend", methods=["GET"])
@login_required
async def _resend() -> ResponseReturnValue:
    """
    Resends the account confirmation email to the current user.

    Returns:
        ResponseReturnValue: Redirects to the unconfirmed page after resending the email.
    """
    token = generate_token(current_user.email)
    confirm_url = url_for("auth._confirm", token=token, _external=True)
    html = await render_template("auth/email/activate.html", confirm_url=confirm_url)
    subject = "Account Activation"
    await send_email(current_user.email, subject, html)
    await flash("A new confirmation email has been sent.", "success")

    await capture_event(current_user.username, "resend_confirm_email")
    return redirect(url_for("auth._unconfirmed"))


@auth_bp.route("/login", methods=["GET", "POST"])
async def _login() -> ResponseReturnValue:
    """
    Handles user login, including form validation and authentication.

    Returns:
        ResponseReturnValue: Redirect to the dashboard after successful login or the login page with an error message.
    """
    form = await Login().create_form()

    if await current_user.is_authenticated:
        return redirect(url_for("wallet._setup"))

    if await form.validate_on_submit():
        user = User(username=form.username.data)

        try:
            await user.load()

        except ValueError:
            await flash("Invalid username or password.", "error")
            return redirect(url_for("auth._login"))

        if not bcrypt.check_password_hash(user.password, form.password.data):
            await flash("Invalid username or password.", "error")
            return redirect(url_for("auth._login"))

        await capture_event(user.username, "login")
        login_user(user)
        return redirect(url_for("wallet._dashboard"))

    return await render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["GET"])
@login_required
async def _logout() -> ResponseReturnValue:
    """
    Logs the user out, stops their wallet container, and clears wallet data.

    Returns:
        ResponseReturnValue: Redirects to the main index page after logging out.
    """
    if await current_user.is_authenticated:
        docker.stop_container(current_user.wallet_container)
        await capture_event(current_user.username, "stop_container")
        await current_user.clear_wallet_data()
        await capture_event(current_user.username, "logout")
        logout_user()
        await flash("You have been logged out.", "success")

    return redirect(url_for("meta._index"))


@auth_bp.route("/reset", methods=["GET", "POST"])
async def _reset() -> ResponseReturnValue:
    """
    Handles the password reset process, including sending a reset link to the user.

    Returns:
        ResponseReturnValue: Redirect to the index page after sending the reset link or renders the reset page.
    """
    form = await Reset().create_form()

    if await form.validate_on_submit():
        try:
            user = await User.get_by_email(form.email.data)

        except ValueError:
            await flash("No such email exists in our database.", "error")
            return redirect(url_for("auth._reset"))

        if not user.confirmed:
            await flash("Please confirm your email first.", "warning")
            return redirect(url_for("auth._reset"))

        token = generate_token(user.email)
        reset_url = url_for("auth._reset_token", token=token, _external=True)
        html = await render_template(
            "auth/email/reset_password.html", reset_url=reset_url
        )
        subject = "Password Reset"
        await send_email(user.email, subject, html)

        await flash(
            "An email with a link to reset your password has been sent. "
            "Please check Junk/Spam folders.",
            "success",
        )
        await capture_event(user.username, "pwd_reset_email_sent")
        return redirect(url_for("meta._index"))

    return await render_template("auth/reset.html", form=form)


@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
async def _reset_token(token: str) -> ResponseReturnValue:
    """
    Allows users to reset their password using the provided token.

    Args:
        token (str): The reset token.

    Returns:
        ResponseReturnValue: Redirects to the login page after password reset or renders the change password page.
    """
    email = validate_token(token)

    if not email:
        await flash(
            "The reset password link is either invalid or has expired.", "error"
        )

    form = await ResetPassword().create_form()

    if await form.validate_on_submit():
        if not form.password.data == form.confirm_password.data:
            await flash("The passwords do not match.", "warning")
            return redirect(request.url)

        user = await User.get_by_email(email)
        user.password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf8"
        )
        await user.save()

        await flash("Your password has been changed successfully.", "success")
        await capture_event(user.username, "password_change")
        return redirect(url_for("auth._login"))

    return await render_template("auth/change_password.html", form=form, token=token)


@auth_bp.route("/delete", methods=["GET", "POST"])
@login_required
async def _delete() -> ResponseReturnValue:
    """
    Deletes the user's wallet data after confirmation.

    Returns:
        ResponseReturnValue: Redirects to the wallet setup page after deletion or renders the dashboard with a confirmation request.
    """
    form = await Delete().create_form()

    if await form.validate_on_submit():
        docker.stop_container(current_user.wallet_container)
        await capture_event(current_user.username, "stop_container")

        await sleep(2)

        docker.delete_wallet_data(current_user.username)
        await capture_event(current_user.username, "delete_wallet")

        await current_user.clear_wallet_data(reset_password=True, reset_wallet=True)
        await flash("Successfully deleted wallet data.", "success")

        return redirect(url_for("wallet._setup"))

    else:
        await flash("Please confirm deletion of the wallet.", "warning")
        return redirect(url_for("wallet._dashboard"))
