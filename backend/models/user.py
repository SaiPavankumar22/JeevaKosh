from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    accepted_terms: bool = Field(..., description="User must accept Terms & Conditions")

    @field_validator("accepted_terms")
    @classmethod
    def terms_must_be_accepted(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must accept the Terms & Conditions to register.")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
