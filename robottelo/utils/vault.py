"""Hashicorp Vault Utils where vault CLI is wrapped to perform vault operations"""

import json
import os
import shlex
import subprocess
import sys

from dotenv import get_key, set_key, unset_key

from robottelo.exceptions import InvalidVaultURLForOIDC
from robottelo.logging import logger, robottelo_root_dir


class Vault:
    HELP_TEXT = (
        "Vault CLI is not installed in your system, "
        "refer link https://learn.hashicorp.com/tutorials/vault/getting-started-install to "
        "install vault CLI as per your system spec!"
    )

    # Configuration constants
    DEFAULT_COMMAND_TIMEOUT = 30  # seconds
    DEFAULT_OIDC_TIMEOUT = 120  # seconds (browser interaction takes longer)
    DEFAULT_TOKEN_RENEWAL = '10h'

    def __init__(self, env_file='.env'):
        self.env_path = robottelo_root_dir.joinpath(env_file)
        self.vault_enabled = None
        self.vault_url = None

    def setup(self):
        """Initialize vault configuration from .env file"""
        # Ensure .env file exists
        if not self.env_path.exists():
            logger.error(f"Environment file not found: {self.env_path}")
            logger.info("Please copy .env.example to .env and configure vault settings")
            sys.exit(1)

        try:
            # Load configuration safely using dotenv
            self.vault_enabled = get_key(str(self.env_path), 'VAULT_ENABLED_FOR_DYNACONF')
            self.vault_url = get_key(str(self.env_path), 'VAULT_URL_FOR_DYNACONF')
        except Exception as e:
            logger.error(f"Failed to read vault configuration from .env file: {e}")
            logger.info("Please ensure VAULT_URL_FOR_DYNACONF is set in your .env file")
            sys.exit(1)

        if not self.vault_url:
            logger.error("VAULT_URL_FOR_DYNACONF not found in .env file")
            logger.info("Please set VAULT_URL_FOR_DYNACONF in your .env file")
            sys.exit(1)

        # Validate vault CLI is available (skip in CI/test environments with AppRole auth)
        if not self._has_approle_auth():
            self._validate_vault_cli()

        self._export_vault_addr()

    def _validate_vault_cli(self):
        """Validate that vault CLI is installed and accessible"""
        try:
            result = subprocess.run(
                ['vault', '--version'], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                logger.error(self.HELP_TEXT)
                sys.exit(1)
            logger.debug(f"Vault CLI version: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error(self.HELP_TEXT)
            sys.exit(1)

    def teardown(self):
        """Clean up environment variables"""
        if os.environ.get('VAULT_ADDR') is not None:
            del os.environ['VAULT_ADDR']

    def _export_vault_addr(self):
        """Set VAULT_ADDR environment variable and validate configuration"""
        # Set Vault CLI Env Var (only if not already set to avoid override)
        if 'VAULT_ADDR' not in os.environ:
            os.environ['VAULT_ADDR'] = self.vault_url

        # Validate vault configuration for OIDC
        if self._is_vault_enabled() and 'localhost:8200' in self.vault_url:
            raise InvalidVaultURLForOIDC(
                f"{self.vault_url} doesn't support OIDC login, "
                "please change url to corp vault in env file!"
            )

    def _is_vault_enabled(self) -> bool:
        """Check if vault is enabled"""
        return self.vault_enabled and self.vault_enabled.lower() == 'true'

    def _has_approle_auth(self) -> bool:
        """Check if AppRole authentication is configured"""
        secret_id = os.environ.get('VAULT_SECRET_ID_FOR_DYNACONF')
        return secret_id is not None and secret_id.strip() != ''

    def exec_vault_command(self, command: str, timeout: int = None, **kwargs):
        """A wrapper to execute the vault CLI commands

        :param command str: The vault CLI command
        :param timeout int: Optional timeout in seconds (defaults to DEFAULT_COMMAND_TIMEOUT)
        :param kwargs dict: Arguments to the subprocess run command to customize the run behavior
        :return: subprocess.CompletedProcess object
        """
        if timeout is None:
            timeout = self.DEFAULT_COMMAND_TIMEOUT

        try:
            logger.debug(f"Executing vault command: {command}")
            # Split command string into list for safe execution without shell
            cmd_list = shlex.split(command)
            vcommand = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,  # Ensure string output
                timeout=timeout,
                **kwargs,
            )

            if vcommand.returncode != 0:
                self._handle_vault_error(vcommand)

            return vcommand

        except subprocess.TimeoutExpired:
            logger.error(f"Vault command timed out after {timeout} seconds")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to execute vault command '{command}': {e}")
            sys.exit(1)

    def _handle_vault_error(self, vcommand):
        """Handle vault command errors with proper logging"""
        verror = vcommand.stderr.strip() if vcommand.stderr else "Unknown error"
        voutput = vcommand.stdout.strip() if vcommand.stdout else ""

        if vcommand.returncode == 127:
            logger.error(f"Error! {self.HELP_TEXT}")
            sys.exit(1)
        elif 'no such host' in verror.lower():
            logger.error("The Vault host is not reachable, check network availability.")
            logger.info(f"Verify that {self.vault_url} is accessible from your network")
            sys.exit(1)
        elif 'Error revoking token' in verror:
            logger.info("Token is already revoked!")
        elif 'Error looking up token' in verror:
            logger.info("Vault is not logged in!")
            logger.info("Run 'make vault-login' to authenticate")
        elif 'permission denied' in verror.lower():
            logger.error("Permission denied - check your vault credentials")
            logger.info(
                "Try running 'make vault-logout' then 'make vault-login' to re-authenticate"
            )
            sys.exit(1)
        else:
            logger.error(f"Vault command failed: {verror}")
            if voutput:
                logger.debug(f"Stdout: {voutput}")
            # Don't exit for other errors, let caller handle them

    def login(self, **kwargs):
        """Login to vault using OIDC and store token in .env file"""
        # Simplified conditional logic
        if not self._is_vault_enabled():
            logger.info("Vault is not enabled in configuration")
            logger.info("Set VAULT_ENABLED_FOR_DYNACONF=true in .env to enable vault")
            return

        if self._has_approle_auth():
            logger.info("AppRole authentication is configured, skipping OIDC login")
            return

        # Check if already logged in
        if self.status(silent=True, **kwargs).returncode == 0:
            logger.info("Already logged in to vault")
            return

        logger.info(
            "Warning! The browser is about to open for vault OIDC login, "
            "close the tab once the sign-in is done!"
        )

        # Perform OIDC login with extended timeout for browser interaction
        login_result = self.exec_vault_command(
            command="vault login -method=oidc", timeout=self.DEFAULT_OIDC_TIMEOUT, **kwargs
        )
        if login_result.returncode != 0:
            logger.error("OIDC login failed")
            logger.info("Make sure you completed the browser authentication")
            return

        # Renew token for extended duration
        renew_result = self.exec_vault_command(
            command=f"vault token renew -i {self.DEFAULT_TOKEN_RENEWAL}", **kwargs
        )
        if renew_result.returncode != 0:
            logger.error("Failed to renew token")
            logger.info(
                "Token was created but renewal failed - it will expire sooner than expected"
            )
            return

        logger.info(f"Success! Vault OIDC Logged-In and extended for {self.DEFAULT_TOKEN_RENEWAL}!")

        # Fetch and parse token with proper error handling
        try:
            token_result = self.exec_vault_command("vault token lookup --format json")
            if token_result.returncode != 0:
                logger.error("Failed to lookup token")
                return

            token_data = json.loads(token_result.stdout)
            token = token_data['data']['id']

            if not token or not isinstance(token, str) or not token.strip():
                logger.error("Invalid token format received")
                return

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse token from vault response: {e}")
            return

        # Store token in .env file using dotenv (thread-safe)
        try:
            set_key(str(self.env_path), 'VAULT_TOKEN_FOR_DYNACONF', token)
            logger.info("Success! New OIDC token added to .env file to access secrets from vault!")
        except Exception as e:
            logger.error(f"Failed to write token to .env file: {e}")
            return

    def logout(self):
        """Logout from vault and remove token from .env file"""
        # Revoke the vault token
        vstatus = self.exec_vault_command('vault token revoke -self')

        # Remove token from .env file using dotenv (thread-safe)
        try:
            # Use unset_key to remove the token, which automatically comments it out
            success = unset_key(str(self.env_path), 'VAULT_TOKEN_FOR_DYNACONF')

            if success and vstatus.returncode == 0:
                logger.info("Success! OIDC token revoked and removed from .env file!")
            elif success:
                logger.info(
                    "Token removed from .env file (vault revocation may have already occurred)"
                )
            else:
                logger.warning("Could not remove token from .env file")
        except Exception as e:
            logger.error(f"Failed to update .env file during logout: {e}")
            logger.info("You may need to manually comment out VAULT_TOKEN_FOR_DYNACONF in .env")

    def status(self, silent=False, **kwargs):
        """Check vault login status

        :param silent: If True, don't log output (useful for internal checks)
        :param kwargs: Additional arguments passed to exec_vault_command
        :return: subprocess.CompletedProcess object
        """
        vstatus = self.exec_vault_command('vault token lookup', **kwargs)
        if vstatus.returncode == 0 and not silent:
            # stdout is already a string due to text=True in exec_vault_command
            logger.info(vstatus.stdout)
        return vstatus

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()
