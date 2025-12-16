import ast
import logging
import re

from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.db.models import Q

from apps.authentication.models import AuthProvider
from apps.authentication.services.regex import PHONE_NUMBER2
from apps.country.models import Country
from apps.referral.models import FlatReferral
from apps.referral.services import ReferralService
from base_utils.clean import DataSanitizer
from base_utils.validators import Validators

log = logging.getLogger(__name__)
User = get_user_model()

print(flush=True)


class UserService:
    def create_user_with_username(
        self,
        username: str,
        phone_country: str = None,
        role_static_name: str = None,
        password: str = None,
        is_passwordless: bool = False,
        **kwargs,
    ) -> User:
        log.info(
            f"Creating user with username: {username}, phone_country: {phone_country}, role: {role_static_name}, passwordless: {is_passwordless}"
        )

        if Validators.is_email(username):
            log.debug(f"Username identified as email: {username}")
            return self._create_user_with_email(email=username, password=password, is_passwordless=is_passwordless, **kwargs)

        log.debug(f"Username identified as phone number: {username}")
        return self._create_user_with_phone_number(
            phone_number=username,
            phone_country=phone_country,
            role_static_name=role_static_name,
            password=password,
            is_passwordless=is_passwordless,
            **kwargs,
        )

    def _create_user_with_email(self, email: str, password: str = None, is_passwordless: bool = False, **kwargs) -> User:
        try:
            log.info(f"Creating user with email: {email}, passwordless: {is_passwordless}")
            instance = User.objects.create(email=email, **kwargs)

            if is_passwordless or not password:
                log.debug(f"Setting unusable password for email user: {email}")
                instance.set_unusable_password()
            else:
                log.debug(f"Setting password for email user: {email}")
                instance.set_password(password)

            instance.save()
            log.info(f"User created successfully with email: {email}, user_id: {instance.id}")
            return instance
        except Exception as e:
            log.error(f"Failed to create user with email {email}: {str(e)}", exc_info=True)
            raise

    def _create_user_with_phone_number(
        self,
        phone_number: str,
        password: str = None,
        phone_country: str = None,
        role_static_name: str = None,
        is_passwordless: bool = False,
        **kwargs,
    ) -> User:
        try:
            log.info(
                f"Creating user with phone number: {phone_number}, country: {phone_country}, passwordless: {is_passwordless}"
            )
            cleaned_phone_number = DataSanitizer.clean_phone_number(phone_number, phone_country)
            log.debug(f"Phone number cleaned: {phone_number} -> {cleaned_phone_number}")

            instance = User(phone_number=cleaned_phone_number, **kwargs)

            # Set role if specified
            result = UserService.set_un_committed_user_role(instance, role_static_name)
            if result and isinstance(result, User):
                instance = result
            else:
                log.warning(f"Role not set for user with phone {cleaned_phone_number}, continuing without role")

            # Handle password based on passwordless flag
            if is_passwordless or not password:
                log.debug(f"Setting unusable password for phone user: {cleaned_phone_number}")
                instance.set_unusable_password()
            else:
                log.debug(f"Setting password for phone user: {cleaned_phone_number}")
                instance.set_password(password)

            instance.save()

            log.info(f"User created successfully with phone number: {cleaned_phone_number}, user_id: {instance.id}")
            return instance
        except Exception as e:
            log.error(f"Failed to create user with phone number {phone_number}: {str(e)}", exc_info=True)
            raise

    def concat_phone_number(self, username: str, country) -> str:
        try:
            log.debug(f"Concatenating phone number: {username} with country: {country}")

            if re.match(PHONE_NUMBER2, username):
                if username.startswith("0"):
                    result = username[1:]
                    log.debug(f"Removed leading zero from phone number: {username} -> {result}")
                    return result

            log.debug(f"Phone number unchanged: {username}")
            return username

        except Exception as e:
            log.error(f"Error concatenating phone number {username}: {str(e)}", exc_info=True)
            return username

    def check_username(self, username: str) -> str | None:
        log.debug(f"Checking username format: {username}")

        # Ctainoert username to string if it's not already a string
        if not isinstance(username, str):
            log.debug(f"Ctainoerting username to string from type: {type(username)}")
            username = str(username)

        try:
            validate_email(username)
            log.debug(f"Username validated as email: {username}")
            return username
        except Exception as e:
            log.debug(f"Username is not a valid email: {username}, error: {str(e)}")
            pass

        if re.match(PHONE_NUMBER2, username):
            log.debug(f"Username validated as phone number: {username}")
            return username
        else:
            log.warning(f"Username format invalid: {username}")
            return None

    def get_user_by_username(self, username: str) -> User | None:
        """
        Get user with this username as phone_number or email

        Return
        ------
            user, does_exist: tuple[User | None, bool]
        """
        log.debug(f"Fetching user by username: {username}")

        queryset = User.objects.filter(Q(phone_number__iexact=username) | Q(email__iexact=username))
        if queryset:
            user = queryset[0]
            log.info(f"User found with username {username}: user_id={user.id}")
        else:
            user = None
            log.info(f"No user found with username: {username}")

        return user

    def check_and_repair_username(self, username: str, country) -> str | None:
        log.debug(f"Checking and repairing username: {username} for country: {country}")
        username = self.check_username(username=username)
        result = self.concat_phone_number(username, country)
        log.debug(f"Username after check and repair: {result}")
        return result

    def get_and_validate_username(self, username: str, country) -> User:
        log.info(f"Getting and validating username: {username} for country: {country}")
        username = self.check_and_repair_username(username, country)
        return self.get_user_by_username(username=username)

    def set_user_phone_country(self, user: User, country: Country = None) -> bool:
        try:
            log.info(f"Setting phone country for user {user.id} to {country}")
            user.phone_country = country
            user.save()
            log.info(f"Phone country set successfully for user {user.id}")
            return True
        except Exception as e:
            log.error(f"Failed to set phone country for user {user.id}: {str(e)}", exc_info=True)
            return False

    def set_user_default_country(self, user: User, country_code: str = None) -> bool:
        try:
            log.info(f"Setting default country for user {user.id} with code: {country_code}")
            country = Country.objects.get(code__iexact=country_code)
            user.country = country
            user.save()
            log.info(f"Default country set successfully for user {user.id}: {country_code}")
            return True
        except Country.DoesNotExist:
            log.error(f"Country not found with code: {country_code}")
            return False
        except Exception as e:
            log.error(f"Failed to set default country for user {user.id}: {str(e)}", exc_info=True)
            return False

    def get_referrer_and_referred_score(self):
        log.debug("Fetching referrer and referred scores from settings")

        try:
            from apps.setting.models import GeneralSetting
            from apps.setting.models import GeneralSettingChoices

            try:
                referrer_score = GeneralSetting.objects.get(key=GeneralSettingChoices.EARN_MONEY_INVITER_SCORE.value).value
                log.debug(f"Referrer score found: {referrer_score}")
            except GeneralSetting.DoesNotExist:
                log.warning("Referrer score setting not found, defaulting to 0")
                referrer_score = 0

            try:
                referred_score = GeneralSetting.objects.get(key=GeneralSettingChoices.EARN_MONEY_INVITED_SCORE.value).value
                log.debug(f"Referred score found: {referred_score}")
            except GeneralSetting.DoesNotExist:
                log.warning("Referred score setting not found, defaulting to 0")
                referred_score = 0

        except Exception as e:
            log.error(f"Exception in get_referrer_and_referred_score: {str(e)}", exc_info=True)
            referrer_score = 0
            referred_score = 0

        log.info(f"Referral scores retrieved - referrer: {referrer_score}, referred: {referred_score}")
        return int(referrer_score), int(referred_score)

    def create_flat_referral(self, referrer: User, referred: User) -> None:
        log.info(f"Creating flat referral - referrer: {referrer.id}, referred: {referred.id}")
        referrer_score, referred_score = self.get_referrer_and_referred_score()

        try:
            flat_referral = FlatReferral.objects.create(referrer=referrer, referred=referred)
            log.debug(f"FlatReferral created with id: {flat_referral.id}")

            flat_referral.is_claimed = True
            flat_referral.value = referrer_score
            flat_referral.save()

            log.info(f"Flat referral created successfully: {flat_referral}, value: {referrer_score}")
            return flat_referral

        except Exception as e:
            log.error(
                f"Error creating flat referral for referrer {referrer.id} and referred {referred.id}: {str(e)}", exc_info=True
            )
            return None

    def do_referral(self, referred: str) -> None:
        log.info(f"Processing referral for referred user: {referred}")

        try:
            referral_repo = ReferralService(referred=referred)
            ref = referral_repo.get_referral_detail_from_cache()

            if ref is None:
                log.warning(f"No referral detail found in cache for: {referred}")
                return None

            log.debug(f"Referral detail retrieved from cache: {ref}")
            ref = ast.literal_eval(ref)
            log.debug(f"Referral detail parsed: {ref}")

            referrer = self.get_user_by_username(ref["referrer"])
            referred_user = self.get_user_by_username(ref["referred"])

            if not referrer:
                log.error(f"Referrer user not found: {ref['referrer']}")
                return None

            if not referred_user:
                log.error(f"Referred user not found: {ref['referred']}")
                return None

            result = self.create_flat_referral(referrer=referrer, referred=referred_user)
            log.info(f"Referral processed successfully for {referred}")
            return result

        except Exception as e:
            log.error(f"Error processing referral for {referred}: {str(e)}", exc_info=True)
            return None

    def set_user_password(self, user: User, new_password: str) -> bool:
        try:
            log.info(f"Setting password for user: {user.id}")
            user.set_password(new_password)
            user.save()
            log.info(f"Password set successfully for user: {user.id}")
            return True
        except Exception as e:
            log.error(f"Failed to set password for user {user.id}: {str(e)}", exc_info=True)
            return False

    def set_user_currency(self, user: User, currency_code: str) -> bool:
        try:
            log.info(f"Setting currency for user {user.id} to: {currency_code}")
            user.currency = currency_code
            user.save()
            log.info(f"Currency set successfully for user {user.id}: {currency_code}")
            return True
        except Exception as e:
            log.error(f"Failed to set currency for user {user.id}: {str(e)}", exc_info=True)
            return False

    def set_user_role(self, user: User, role_static_name: str) -> bool:
        """
        Set or change the user's role
        """
        try:
            log.info(f"Setting role for user {user.id} to: {role_static_name}")
            from apps.authentication.models import UserType

            role = UserType.objects.filter(static_name=role_static_name, is_active=True).first()
            if role:
                user.role = role
                user.save(update_fields=["role"])
                log.info(f"Role set successfully for user {user.id}: {role_static_name} (role_id: {role.id})")
                return True

            log.warning(f"Role not found or inactive: {role_static_name} for user {user.id}")
            return False
        except Exception as e:
            log.error(f"Failed to set role for user {user.id}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def set_un_committed_user_role(user: User, role_static_name: str) -> User | bool:
        """
        Set or change the user's role before saving
        Returns the user object if successful, False otherwise
        """
        # If no role is specified, just return the user object
        if not role_static_name:
            log.debug("No role specified, skipping role assignment")
            return user

        try:
            log.info(f"Setting uncommitted role: {role_static_name}")
            from apps.authentication.models import UserType

            role = UserType.objects.filter(static_name=role_static_name, is_active=True).first()
            if role:
                user.role = role
                log.debug(f"Uncommitted role set: {role_static_name} (role_id: {role.id})")
                return user

            log.warning(f"Role not found or inactive for uncommitted user: {role_static_name}")
            # Return the user anyway, just without the role
            return user
        except Exception as e:
            log.error(f"Failed to set uncommitted role {role_static_name}: {str(e)}", exc_info=True)
            # Return the user anyway, just without the role
            return user
