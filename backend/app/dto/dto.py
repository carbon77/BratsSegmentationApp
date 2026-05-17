from pydantic import BaseModel, field_validator


class AuthRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if '@' not in normalized:
            raise ValueError('Valid email is required')
        return normalized


class RegisterRequest(AuthRequest):
    name: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError('Name is required')
        return normalized


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: dict


class PatchScanRequest(BaseModel):
    title: str