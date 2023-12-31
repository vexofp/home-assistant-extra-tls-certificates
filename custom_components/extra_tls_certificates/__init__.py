"""
Custom integration to install extra TLS certificates into Home Assistant.
"""

import logging
from typing import Final, TypedDict, cast

import voluptuous as vol

from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.util.ssl import (get_default_context, get_default_no_verify_context, client_context,
                                    create_no_verify_ssl_context, SSLCipherList)
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_CLIENT, CONF_CA, CONF_CERT, CONF_KEY, CONF_PASSWORD

_LOGGER: logging.Logger = logging.getLogger(__package__)

EXTRA_TLS_CERTIFICATES_SCHEMA: Final = vol.Schema({
    vol.Optional(CONF_CLIENT):
    vol.All(cv.ensure_list, [{
        vol.Required(CONF_CERT): cv.isfile,
        vol.Optional(CONF_KEY): cv.isfile,
        vol.Optional(CONF_PASSWORD): cv.string,
    }]),
    vol.Optional(CONF_CA):
    vol.All(cv.ensure_list, [cv.isfile]),
})

CONFIG_SCHEMA: Final = vol.Schema({DOMAIN: EXTRA_TLS_CERTIFICATES_SCHEMA}, extra=vol.ALLOW_EXTRA)


class ConfClient(TypedDict, total=False):
    """Typed dict for config client data."""

    cert: str
    key: str
    password: str


class ConfData(TypedDict, total=False):
    """Typed dict for config data."""

    client: list[ConfClient]
    ca: list[str]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration."""

    conf: ConfData | None = config.get(DOMAIN)
    if conf is None:
        conf = cast(ConfData, EXTRA_TLS_CERTIFICATES_SCHEMA({}))

    # The context creation functions are cached, so all calls with the same arguments should return the same object,
    # into which we can load our extra certificates.
    # The default contexts result from calling the creation functions with no arguments.
    # httpx_client.get_async_client(), however, calls the creation functions and passes the default argument value
    # explicitly (resulting in a distinct context), so we must load into that also. (Until #105348 is released.)

    # Load extra trusted CA certificate (bundles) into default context
    ca_contexts = [
        get_default_context(),
        client_context(SSLCipherList.PYTHON_DEFAULT),
    ]
    for cafile in conf.get(CONF_CA, []):
        _LOGGER.info('Adding trusted CA: %r', cafile)
        for context in ca_contexts:
            context.load_verify_locations(cafile=cafile)

    # Load client certificates into default contexts
    cert_contexts = ca_contexts + [
        get_default_no_verify_context(),
        create_no_verify_ssl_context(SSLCipherList.PYTHON_DEFAULT),
    ]
    for certdef in conf.get(CONF_CLIENT, []):
        certfile = certdef.get(CONF_CERT)
        keyfile = certdef.get(CONF_KEY)
        password = certdef.get(CONF_PASSWORD)

        _LOGGER.info('Adding client certificate: %s : %s (encrypted=%s)', certfile, keyfile, password is not None)
        for context in cert_contexts:
            context.load_cert_chain(certfile, keyfile, password)

    return True
