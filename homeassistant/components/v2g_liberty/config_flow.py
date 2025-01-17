"""Config flow for V2G Liberty integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv


from .const import *

_LOGGER = logging.getLogger(__name__)

STEP_SETUP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=DEFAULT_PORT): int,
    }
)

STEP_BATTERYLOW_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("battlow", default=DEFAULT_BATTERYLOW): int,
    }
)
STEP_BATTERYHIGH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("batthigh", default=DEFAULT_BATTERYHIGH): int,
    }
)
STEP_BATTERYCAP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("battcap"): int,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, port: int) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

    if not await hub.authenticate(data["port"]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Wallbox Charger"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for V2G Liberty."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return self.async_show_menu(step_id="user", menu_options=["setup"])

    async def async_step_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_charger"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self.async_step_battlow()

        return self.async_show_form(
            step_id="setup",
            data_schema=STEP_SETUP_DATA_SCHEMA,
            errors=errors,
            last_step=False,
        )

    async def async_step_battlow(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the minimum battery % step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                vol.Range(min=10, max=30)(user_input["battlow"])
                return await self.async_step_batthigh()
            except vol.Invalid:
                errors = {"base": "outofrange"}

        return self.async_show_form(
            step_id="battlow",
            data_schema=STEP_BATTERYLOW_DATA_SCHEMA,
            errors=errors,
            last_step=False,
        )

    async def async_step_batthigh(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the maximum battery % step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                vol.Range(min=60, max=100)(user_input["batthigh"])
                return await self.async_step_battcap()
            except vol.Invalid:
                errors = {"base": "outofrange"}

        return self.async_show_form(
            step_id="batthigh",
            data_schema=STEP_BATTERYHIGH_DATA_SCHEMA,
            errors=errors,
            last_step=False,
        )

    async def async_step_battcap(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the battery capacity step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                vol.Range(min=10, max=150)(user_input["battcap"])
                return await self.async_step_battcap()
            except vol.Invalid:
                errors = {"base": "outofrange"}

        return self.async_show_form(
            step_id="battcap",
            data_schema=STEP_BATTERYCAP_DATA_SCHEMA,
            errors=errors,
            last_step=False,
            description_placeholders={"ev_database_url": "https://ev-database.org"},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid charger."""
