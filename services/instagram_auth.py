from services import database as database_service
from models.db_models import InstagramUser
from datetime import datetime, timezone
from cryptography.fernet import Fernet
import os
import base64
import hashlib
import httpx
from dotenv import load_dotenv
from services.database import SessionLocal

load_dotenv()

class InstagramAuthService:
    def __init__(self):
        self.encryption_key = os.getenv("INSTAGRAM_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("INSTAGRAM_ENCRYPTION_KEY not found in environment variables")
        self.fernet = Fernet(self.encryption_key.encode())
        
    def encrypt_token(self, access_token: str) -> str:
        """Encrypt the access token"""
        encrypted_token = self.fernet.encrypt(access_token.encode())
        return encrypted_token.decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt the access token"""
        print(f"Encrypted token: {encrypted_token}")
        decrypted_token = self.fernet.decrypt(encrypted_token.encode())
        print(f"🔓 Decrypted token: {decrypted_token.decode()}")
        return decrypted_token.decode()
    
    async def save_instagram_user(self, access_token: str, user_id: str, token_type: str = "long_lived", expires_in: int = None):
        """
        Save Instagram user data securely to database
        """
        try:
            # Ensure user_id is a string
            user_id = str(user_id)
            print(f"💾 Saving Instagram user: {user_id}")
            
            # Get user info from Instagram API
            user_info = await self.get_instagram_user_info(access_token)
            if not user_info:
                raise Exception("Failed to get Instagram user info")
            
            # Encrypt the access token
            encrypted_token = self.encrypt_token(access_token)
            
            # Save to database
            session = database_service.SessionLocal()
            try:
                # Check if user already exists
                existing_user = session.query(InstagramUser).filter_by(instagram_user_id=user_id).first()
                
                if existing_user:
                    # Update existing user
                    existing_user.access_token_encrypted = encrypted_token
                    existing_user.token_type = token_type
                    existing_user.expires_in = expires_in
                    existing_user.username = user_info.get("username", existing_user.username)
                    existing_user.account_type = user_info.get("account_type", existing_user.account_type)
                    existing_user.media_count = user_info.get("media_count", existing_user.media_count)
                    existing_user.updated_at = datetime.now(timezone.utc)
                    existing_user.is_active = True
                    
                    session.commit()
                    session.refresh(existing_user)
                    
                    print(f"✅ Updated existing Instagram user: @{existing_user.username}")
                    return existing_user
                else:
                    # Create new user
                    new_user = InstagramUser(
                        instagram_user_id=user_id,
                        username=user_info.get("username", f"user_{user_id}"),
                        account_type=user_info.get("account_type"),
                        media_count=user_info.get("media_count"),
                        access_token_encrypted=encrypted_token,
                        token_type=token_type,
                        expires_in=expires_in,
                        is_active=True
                    )
                    
                    session.add(new_user)
                    session.commit()
                    session.refresh(new_user)
                    
                    print(f"✅ Created new Instagram user: @{new_user.username}")
                    return new_user
                    
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error saving Instagram user: {str(e)}")
            raise e
    
    async def get_instagram_user_info(self, access_token: str):
        """Get Instagram user info from API"""
        try:
            user_url = "https://graph.instagram.com/me"
            user_params = {
                "fields": "id,username,account_type,media_count",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                user_resp = await client.get(user_url, params=user_params)
                
                if user_resp.status_code == 200:
                    return user_resp.json()
                else:
                    print(f"❌ Failed to get Instagram user info: {user_resp.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting Instagram user info: {str(e)}")
            return None
    
    def get_user_by_instagram_id(self, instagram_user_id: str):
        """Get Instagram user from database by Instagram ID"""
        # Ensure user_id is a string
        instagram_user_id = str(instagram_user_id)
        session = database_service.SessionLocal()
        try:
            user = session.query(InstagramUser).filter_by(
                instagram_user_id=instagram_user_id,
                is_active=True
            ).first()
            return user
        finally:
            session.close()
    
    def get_decrypted_token(self, user: InstagramUser) -> str:
        """Get decrypted access token for a user"""
        if not user.access_token_encrypted:
            print(f"🔍 No encrypted token found for user {user.username}")
            return None
        
        print(f"🔍 Attempting to decrypt token for user {user.username}")
        print(f"🔍 Encrypted token: {user.access_token_encrypted[:50]}...")
        print(f"🔍 Current encryption key: {self.encryption_key[:20] if self.encryption_key else 'None'}...")
        
        try:
            decrypted = self.decrypt_token(user.access_token_encrypted)
            print(f"✅ Successfully decrypted token for {user.username}")
            print(f"🔍 Decrypted token: {decrypted[:20] if decrypted else 'None'}...")
            return decrypted
        except Exception as e:
            print(f"❌ Failed to decrypt token for user {user.username}: {str(e)}")
            print(f"❌ Exception type: {type(e).__name__}")
            print(f"💡 This usually means the encryption key has changed")
            return None
    
    def update_last_used(self, user: InstagramUser):
        """Update the last used timestamp for a user"""
        session = database_service.SessionLocal()
        try:
            user.last_used_at = datetime.now(timezone.utc)
            session.merge(user)
            session.commit()
        finally:
            session.close()
    
    def deactivate_user(self, user_identifier: str):
        """Deactivate (soft delete) an Instagram user by database ID or Instagram ID"""
        session = database_service.SessionLocal()
        try:
            # Try to find by database ID first (if it's a number)
            if user_identifier.isdigit():
                user = session.query(InstagramUser).filter_by(id=int(user_identifier)).first()
            else:
                # Otherwise, find by Instagram user ID
                user = session.query(InstagramUser).filter_by(instagram_user_id=str(user_identifier)).first()
                
            if user:
                user.is_active = False
                user.updated_at = datetime.now(timezone.utc)
                session.commit()
                print(f"✅ Deactivated Instagram user: @{user.username}")
                return True
            return False
        finally:
            session.close()

    def get_user_by_id_with_token(self, user_id: int):
        """Get Instagram user by database ID and return with decrypted token"""
        session = SessionLocal()
        try:
            user = session.query(InstagramUser).filter_by(
                id=user_id,
                is_active=True
            ).first()
            
            if not user:
                return None
            
            print("User found")
            print(user.access_token_encrypted)
            
            # Decrypt the token
            decrypted_token = self.get_decrypted_token(user)
            
            # Update last used timestamp
            self.update_last_used(user)
            
            return {
                "user": {
                    "id": user.id,
                    "instagram_user_id": user.instagram_user_id,
                    "username": user.username,
                    "account_type": user.account_type,
                    "media_count": user.media_count,
                    "token_type": user.token_type,
                    "expires_in": user.expires_in,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_used_at": user.last_used_at.isoformat() if user.last_used_at else None,
                    "is_active": user.is_active
                },
                "access_token": decrypted_token
            }
            
        finally:
            session.close()

    def get_all_users(self, include_inactive: bool = False):
        """Get all Instagram users from the database"""
        session = SessionLocal()
        try:
            query = session.query(InstagramUser)
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            users = query.order_by(InstagramUser.created_at.desc()).all()
            
            user_list = []
            for user in users:
                user_dict = {
                    "id": user.id,
                    "instagram_user_id": user.instagram_user_id,
                    "username": user.username,
                    "account_type": user.account_type,
                    "media_count": user.media_count,
                    "token_type": user.token_type,
                    "expires_in": user.expires_in,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_used_at": user.last_used_at.isoformat() if user.last_used_at else None,
                    "is_active": user.is_active
                }
                user_list.append(user_dict)
            
            return user_list
            
        finally:
            session.close()

# Create global instance
instagram_auth_service = InstagramAuthService() 