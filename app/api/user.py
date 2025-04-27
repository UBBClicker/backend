from fastapi import APIRouter, HTTPException, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from jose import JWTError

from app import schemas, crud
from app.database import get_db
from app.utils.security import create_access_token, validate_token
from app.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.post(
    "/register", 
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user with the provided nickname and password"
)
def register_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Register a new user:
    
    - **nickname**: unique username
    - **password**: user password (min length: 5, max length: 20)
    """
    try:
        return crud.user.register(db, user)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )


@user_router.post(
    "/login",
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
    summary="Login for access token",
    description="Login with user credentials to get an access token for authentication. This endpoint expects data in form-urlencoded format, not JSON."
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    
    **Note:** This endpoint accepts form data (application/x-www-form-urlencoded), not JSON.
    
    Request body parameters:
    - **username**: user's nickname (this is the user's unique identifier)
    - **password**: user's password
    
    Returns:
    - **access_token**: JWT token used for authentication
    - **token_type**: Type of token (bearer)
    
    Example curl request:
    ```
    curl -X POST "http://localhost:8000/user/login" -d "username=yourusername&password=yourpassword" -H "Content-Type: application/x-www-form-urlencoded"
    ```
    """
    user = crud.user.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect nickname or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@user_router.get(
    "/me",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get details of the currently authenticated user"
)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get current user details from the provided access token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = validate_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = crud.user.get(db, id=int(token_data.sub))
    if user is None:
        raise credentials_exception
    
    return user


@user_router.post(
    "/refresh-token",
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using an existing valid token. Use this when your current token is about to expire."
)
def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Refresh the access token
    
    Use an existing valid token to get a new access token with extended expiration time.
    The existing token must be provided in the Authorization header as a Bearer token.
    
    **Authentication Required**: This endpoint requires a valid access token
    
    Request:
    - No request body is needed
    - Token must be provided in the Authorization header: `Authorization: Bearer your_current_token`
    
    Returns:
    - **access_token**: New JWT token with extended validity
    - **token_type**: Type of token (bearer)
    
    Example curl request:
    ```
    curl -X POST "http://localhost:8000/user/refresh-token" \
         -H "Authorization: Bearer your_current_token"
    ```
    
    Status Codes:
    - 200: Success
    - 401: Invalid or expired token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Validate the existing token
    token_data = validate_token(token)
    if token_data is None:
        raise credentials_exception
    
    # Get the user ID from the token
    user_id = int(token_data.sub)
    user = crud.user.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    
    # Create a new token with extended expiration
    new_access_token = create_access_token(user.id)
    return {"access_token": new_access_token, "token_type": "bearer"}


# Dependency to get the current user
def get_current_user_dependency(
    token: str = Security(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = validate_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = crud.user.get(db, id=int(token_data.sub))
    if user is None:
        raise credentials_exception
    
    return user
