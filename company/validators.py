from django.core.exceptions import ValidationError
import re
from django.utils.deconstruct import deconstructible


def validate_positive(value):
    """
    Validator to ensure that a given value is positive.
    Raises ValidationError if the value is not positive.
    """
    if value <= 0:
        raise ValidationError(
            f"Value {value} is not positive. It must be greater than zero."
        )
@deconstructible
class ValidatePhoneNumber:
    def __call__(self, value):
        if not re.match(r'^\d{10}$', value):
            raise ValidationError("Phone number must be exactly 10 digits.")

# Example format: 22AAAAA0000A1Z5 (15 characters: 2 digits + 10 alphanumeric + 1 + Z + 1 digit/alphabet)
def validate_gst_format(value):
    gst_regex = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$'
    if not re.match(gst_regex, value):
        raise ValidationError("Invalid GST number format.")


def validate_email_custom(value):
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
        raise ValidationError("Enter a valid email address.")


def validate_pan(value):
    pan_regex = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    if value and not re.match(pan_regex, value):
        raise ValidationError("Invalid PAN format.")

def validate_address(value):
    if len(value.strip()) < 10:
        raise ValidationError("Address is too short.")
    if value.isdigit():
        raise ValidationError("Address must contain characters, not just numbers.")

@deconstructible
class ValidateName:
    def __init__(self, field_name="Name"):
        self.field_name = field_name

    def __call__(self, value):
        if not re.match(r'^[A-Za-z\s]+$', value):
            raise ValidationError(f"{self.field_name} must contain only alphabets and spaces.")


def validate_pincode(value):
    if not re.match(r"^[A-Za-z0-9\s\-]{3,10}$", value):
        raise ValidationError("Invalid postal/zip code format.")

@deconstructible
class ValidatePositiveAmount:
    def __init__(self, field_name="Amount"):
        self.field_name = field_name

    def __call__(self, value):
        if value < 0:
            raise ValidationError(f"{self.field_name} cannot be negative.")

@deconstructible
class ValidateIfPresentNotEmpty:
    def __init__(self, field_name="Field"):
        self.field_name = field_name

    def __call__(self, value):
        if value is not None and value.strip() == '':
            raise ValidationError(f"{self.field_name} cannot be empty if provided.")
@deconstructible
class ValidateDiscount:
    def __init__(self, field_name="Discount"):
        self.field_name = field_name

    def __call__(self, value):
        if value < 0 or value > 100:
            raise ValidationError(f"{self.field_name} must be between 0 and 100.")
@deconstructible
class ValidateInvoiceNumber:
    def __call__(self, value):
        if not re.fullmatch(r'^[A-Z0-9\-/]+$', value.strip()):
            raise ValidationError("Invoice number can only contain uppercase letters, digits, hyphens, and slashes.")

def validate_account_number(value):
    if not re.fullmatch(r'^\d{9,18}$', value):
        raise ValidationError("Account number must be between 9 and 18 digits.")

def validate_ifsc_code(value):
    if not re.fullmatch(r'^[A-Z]{4}0[A-Z0-9]{6}$', value):
        raise ValidationError("Invalid IFSC code format.")
