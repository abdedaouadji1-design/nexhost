"""
NexHost V6 - Ready Bots Service
===============================
Service for managing ready-made bots and AI bot generation
"""
import os
import re
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import ReadyBot, UserBot, User, BotStatus
from ai_router import ai_router, AIModel

logger = logging.getLogger(__name__)


class ReadyBotService:
    """Service for ready-made bots management"""
    
    def __init__(self, bots_dir: str = "/app/bots"):
        self.bots_dir = bots_dir
        os.makedirs(bots_dir, exist_ok=True)
    
    async def create_bot_template(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        bot_type: str,
        code: str,
        requirements: str,
        created_by: int,
        image_url: Optional[str] = None,
        icon: str = "🤖",
        config_fields: Optional[List[Dict]] = None,
        is_premium: bool = False
    ) -> ReadyBot:
        """Create new bot template (Admin only)"""
        
        # Auto-detect config fields if not provided
        if config_fields is None:
            config_fields = self._detect_config_fields(code)
        
        bot = ReadyBot(
            name=name,
            description=description,
            bot_type=bot_type,
            code=code,
            requirements=requirements,
            created_by=created_by,
            image_url=image_url,
            icon=icon,
            config_fields=config_fields,
            is_premium=is_premium,
            is_active=True
        )
        
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        
        logger.info(f"Created bot template: {name} (ID: {bot.id})")
        return bot
    
    def _detect_config_fields(self, code: str) -> List[Dict]:
        """Auto-detect required config fields from code"""
        fields = []
        
        # Look for common patterns
        patterns = [
            (r'bot_token\s*=\s*["\']', "token", "Bot Token", "text"),
            (r'TOKEN\s*=\s*["\']', "token", "Bot Token", "text"),
            (r'API_KEY\s*=\s*["\']', "api_key", "API Key", "text"),
            (r'CHAT_ID\s*=\s*["\']', "chat_id", "Chat ID", "text"),
            (r'ADMIN_ID\s*=\s*["\']', "admin_id", "Admin ID", "text"),
        ]
        
        for pattern, name, label, field_type in patterns:
            if re.search(pattern, code):
                fields.append({
                    "name": name,
                    "label": label,
                    "type": field_type,
                    "required": True
                })
        
        return fields
    
    async def get_all_templates(
        self,
        db: AsyncSession,
        include_inactive: bool = False
    ) -> List[ReadyBot]:
        """Get all bot templates"""
        query = select(ReadyBot)
        if not include_inactive:
            query = query.where(ReadyBot.is_active == True)
        
        result = await db.execute(query.order_by(ReadyBot.created_at.desc()))
        return result.scalars().all()
    
    async def get_template(self, db: AsyncSession, bot_id: int) -> Optional[ReadyBot]:
        """Get bot template by ID"""
        result = await db.execute(select(ReadyBot).where(ReadyBot.id == bot_id))
        return result.scalar_one_or_none()
    
    async def update_template(
        self,
        db: AsyncSession,
        bot_id: int,
        **kwargs
    ) -> Optional[ReadyBot]:
        """Update bot template"""
        bot = await self.get_template(db, bot_id)
        if not bot:
            return None
        
        for key, value in kwargs.items():
            if hasattr(bot, key):
                setattr(bot, key, value)
        
        bot.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(bot)
        
        return bot
    
    async def delete_template(self, db: AsyncSession, bot_id: int) -> bool:
        """Delete bot template"""
        bot = await self.get_template(db, bot_id)
        if not bot:
            return False
        
        await db.delete(bot)
        await db.commit()
        
        return True


class UserBotService:
    """Service for user bot instances"""
    
    def __init__(self, bots_dir: str = "/app/bots"):
        self.bots_dir = bots_dir
        os.makedirs(bots_dir, exist_ok=True)
    
    async def create_bot_instance(
        self,
        db: AsyncSession,
        user: User,
        template_id: int,
        name: str,
        config: Dict[str, str],
        debug_mode: bool = False
    ) -> UserBot:
        """Create bot instance for user"""
        
        # Check user's bot quota
        current_bots = await self._get_user_bot_count(db, user.id)
        if current_bots >= user.max_ready_bots:
            raise ValueError(f"Bot limit reached. Maximum: {user.max_ready_bots}")
        
        # Get template
        template_result = await db.execute(
            select(ReadyBot).where(ReadyBot.id == template_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise ValueError("Bot template not found")
        
        # Generate modified code with AI
        modified_code = await self._generate_bot_code(
            template.code,
            config,
            debug_mode
        )
        
        # Create bot directory
        bot_dir = os.path.join(self.bots_dir, str(user.id), str(template_id))
        os.makedirs(bot_dir, exist_ok=True)
        
        # Save bot files
        bot_file = os.path.join(bot_dir, "bot.py")
        with open(bot_file, "w", encoding="utf-8") as f:
            f.write(modified_code)
        
        # Save requirements
        if template.requirements:
            req_file = os.path.join(bot_dir, "requirements.txt")
            with open(req_file, "w", encoding="utf-8") as f:
                f.write(template.requirements)
        
        # Create log file
        log_file = os.path.join(bot_dir, "bot.log")
        Path(log_file).touch()
        
        # Create bot instance
        bot = UserBot(
            user_id=user.id,
            bot_template_id=template_id,
            name=name,
            config=config,
            modified_code=modified_code,
            bot_path=bot_dir,
            log_path=log_file,
            debug_mode=debug_mode,
            status=BotStatus.STOPPED
        )
        
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        
        logger.info(f"Created bot instance: {name} for user {user.username}")
        return bot
    
    async def _generate_bot_code(
        self,
        template_code: str,
        config: Dict[str, str],
        debug_mode: bool
    ) -> str:
        """Generate bot code with AI"""
        
        # Build config string
        config_lines = []
        for key, value in config.items():
            config_lines.append(f'{key.upper()} = "{value}"')
        
        config_str = "\n".join(config_lines)
        debug_label = "Add debug logging" if debug_mode else "Keep it production-ready"
        
        prompt = f"""Insert these configurations into the bot code:

CONFIGURATION:
{config_str}

ORIGINAL CODE:
{template_code}

Requirements:
1. Insert the configuration at the TOP of the file after imports
2. Replace any placeholder tokens with the actual values
3. Add error handling
4. {debug_label}
5. Return ONLY the complete modified code

MODIFIED CODE:"""
        
        try:
            response = await ai_router.generate(
                prompt=prompt,
                model=AIModel.V3,
                system_prompt="You are a Python bot developer. Insert configuration securely.",
                temperature=0.1,
                max_tokens=3000
            )
            
            if response.success:
                return response.content
            else:
                # Fallback: manual insertion
                return self._manual_code_insertion(template_code, config)
                
        except Exception as e:
            logger.error(f"AI code generation failed: {e}")
            return self._manual_code_insertion(template_code, config)
    
    def _manual_code_insertion(self, code: str, config: Dict[str, str]) -> str:
        """Manually insert config into code (fallback)"""
        config_lines = []
        for key, value in config.items():
            config_lines.append(f'{key.upper()} = "{value}"')
        
        config_str = "\n".join(config_lines)
        
        # Find where to insert (after imports)
        lines = code.split("\n")
        insert_index = 0
        
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_index = i + 1
        
        lines.insert(insert_index, f"\n# Configuration\n{config_str}\n")
        
        return "\n".join(lines)
    
    async def _get_user_bot_count(self, db: AsyncSession, user_id: int) -> int:
        """Get number of bots for user"""
        result = await db.execute(
            select(func.count(UserBot.id)).where(UserBot.user_id == user_id)
        )
        return result.scalar()
    
    async def get_user_bots(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[UserBot]:
        """Get all bots for user"""
        result = await db.execute(
            select(UserBot)
            .where(UserBot.user_id == user_id)
            .order_by(UserBot.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_bot(self, db: AsyncSession, bot_id: int, user_id: int) -> Optional[UserBot]:
        """Get bot instance"""
        result = await db.execute(
            select(UserBot)
            .where(UserBot.id == bot_id)
            .where(UserBot.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_bot(
        self,
        db: AsyncSession,
        bot_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[UserBot]:
        """Update bot instance"""
        bot = await self.get_bot(db, bot_id, user_id)
        if not bot:
            return None
        
        for key, value in kwargs.items():
            if hasattr(bot, key):
                setattr(bot, key, value)
        
        bot.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(bot)
        
        return bot
    
    async def delete_bot(self, db: AsyncSession, bot_id: int, user_id: int) -> bool:
        """Delete bot instance"""
        bot = await self.get_bot(db, bot_id, user_id)
        if not bot:
            return False
        
        # Stop bot if running
        if bot.status == BotStatus.RUNNING:
            await self.stop_bot(bot)
        
        # Delete files
        if bot.bot_path and os.path.exists(bot.bot_path):
            import shutil
            shutil.rmtree(bot.bot_path)
        
        await db.delete(bot)
        await db.commit()
        
        return True
    
    async def start_bot(self, bot: UserBot) -> bool:
        """Start bot process"""
        if bot.status == BotStatus.RUNNING:
            return True
        
        try:
            bot_file = os.path.join(bot.bot_path, "bot.py")
            if not os.path.exists(bot_file):
                logger.error(f"Bot file not found: {bot_file}")
                return False
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                "python3", bot_file,
                stdout=open(bot.log_path, "a"),
                stderr=asyncio.subprocess.STDOUT,
                cwd=bot.bot_path
            )
            
            bot.pid = process.pid
            bot.status = BotStatus.RUNNING
            bot.started_at = datetime.utcnow()
            
            logger.info(f"Started bot {bot.name} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            bot.status = BotStatus.ERROR
            return False
    
    async def stop_bot(self, bot: UserBot) -> bool:
        """Stop bot process"""
        if bot.status != BotStatus.RUNNING or not bot.pid:
            return True
        
        try:
            import signal
            os.kill(bot.pid, signal.SIGTERM)
            
            bot.status = BotStatus.STOPPED
            bot.pid = None
            
            logger.info(f"Stopped bot {bot.name}")
            return True
            
        except ProcessLookupError:
            # Process already dead
            bot.status = BotStatus.STOPPED
            bot.pid = None
            return True
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            return False
    
    async def get_bot_logs(self, bot: UserBot, lines: int = 100) -> List[str]:
        """Get bot logs"""
        if not bot.log_path or not os.path.exists(bot.log_path):
            return []
        
        try:
            with open(bot.log_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
            return []
    
    async def clear_logs(self, bot: UserBot) -> bool:
        """Clear bot logs"""
        if not bot.log_path or not os.path.exists(bot.log_path):
            return False
        
        try:
            # Backup old logs
            backup_path = bot.log_path + ".old"
            os.rename(bot.log_path, backup_path)
            
            # Create new log file
            Path(bot.log_path).touch()
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear logs: {e}")
            return False


class AIBotGenerator:
    """AI-powered bot generator"""
    
    @staticmethod
    async def generate_bot(
        description: str,
        bot_type: str = "telegram",
        features: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Generate complete bot using AI"""
        
        features_list = features or []
        features_str = "\n".join(["- " + feat for feat in features_list])
        
        prompt = f"""Create a complete, production-ready {bot_type} bot in Python.

DESCRIPTION:
{description}

REQUIRED FEATURES:
{features_str}

Requirements:
1. Use the official python-telegram-bot library (v20+)
2. Include proper async/await
3. Add comprehensive error handling
4. Include logging
5. Add comments in Arabic where helpful
6. Make it easy to configure (TOKEN, CHAT_ID, etc.)
7. Include a requirements.txt section
8. Structure the code professionally

Return your response in this exact format:

===CODE===
[The complete Python code]

===REQUIREMENTS===
[requirements.txt content]

===DESCRIPTION===
[Short description of what the bot does]

===CONFIG_FIELDS===
[JSON array of required config fields like: {{"name": "token", "label": "Bot Token", "type": "text"}}]"""
        
        response = await ai_router.generate(
            prompt=prompt,
            model=AIModel.R1,  # Use reasoning model for code generation
            system_prompt="You are an expert Python bot developer. Create complete, working, production-ready bots.",
            temperature=0.3,
            max_tokens=4000
        )
        
        if not response.success:
            raise Exception(f"Failed to generate bot: {response.error}")
        
        # Parse response
        content = response.content
        
        result = {
            "code": "",
            "requirements": "",
            "description": "",
            "config_fields": []
        }
        
        # Extract sections
        sections = {
            "code": r"===CODE===(.+?)(?===|$)",
            "requirements": r"===REQUIREMENTS===(.+?)(?===|$)",
            "description": r"===DESCRIPTION===(.+?)(?===|$)",
            "config_fields": r"===CONFIG_FIELDS===(.+?)(?===|$)"
        }
        
        import re
        for key, pattern in sections.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                value = match.group(1).strip()
                if key == "config_fields":
                    try:
                        import json
                        result[key] = json.loads(value)
                    except:
                        result[key] = []
                else:
                    result[key] = value
        
        return result
    
    @staticmethod
    async def debug_code(code: str, error_message: Optional[str] = None) -> str:
        """Debug code using AI"""
        
        prompt = f"""Debug and fix this Python code:

```python
{code}
```

{("ERROR MESSAGE:\n" + error_message + "\n") if error_message else ""}

Please:
1. Identify the issues
2. Provide the fixed code
3. Explain what was wrong (in Arabic)

Return ONLY the fixed code."""
        
        response = await ai_router.generate(
            prompt=prompt,
            model=AIModel.V3,
            system_prompt="You are a Python debugging expert. Fix code issues efficiently.",
            temperature=0.2,
            max_tokens=3000
        )
        
        if response.success:
            return response.content
        else:
            raise Exception(f"Debug failed: {response.error}")


# Service instances
ready_bot_service = ReadyBotService()
user_bot_service = UserBotService()
ai_bot_generator = AIBotGenerator()
