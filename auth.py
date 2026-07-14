import bcrypt
from database import create_user, get_user_by_email

#------------Register-----------------
def register_user(full_name, email, password):

    # Check if email already exists
    if get_user_by_email(email):
        return False, "Email already registered."

    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    create_user(
        full_name,
        email,
        password_hash
    )

    return True, "Registration Successful!"

#--------------Login---------------
def login_user(email, password):

    user = get_user_by_email(email)

    if not user:
        return False, "User not found."

    if bcrypt.checkpw(
        password.encode(),
        user["password_hash"].encode()
    ):
        return True, user

    return False, "Incorrect Password."