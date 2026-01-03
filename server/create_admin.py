from db_connection import DbPool
from queries.user import UserQueryManager
from constants import UserRole
import sys

def create_admin(email, password, first_name, last_name):
    """Create an admin user via CLI"""
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.register_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.ADMIN.value
            )
        print(f"✓ Admin user created successfully with ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"✗ Error creating admin: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python create_admin.py <email> <password> <first_name> <last_name>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    first_name = sys.argv[3]
    last_name = sys.argv[4]
    
    create_admin(email, password, first_name, last_name)