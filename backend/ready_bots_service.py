"""
NexHost V6 - Ready Bots Service
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
    def __init__(self, bots_dir: str = "/app/data/bots"):
        self.bots_dir = bots_dir
        os.makedirs(bots_dir, exist_ok=True)

    async def create_bot_template(self, db, name, description, bot_type,
                                   code, requirements, created_by,
                                   image_url=None, icon="🤖",
                                   config_fields=None, is_premium=False):
        if config_fields is None:
            config_fields = self._detect_config_fields(code)
        bot = ReadyBot(
            name=name, description=description, bot_type=bot_type,
            code=code, requirements=requirements, created_by=created_by,
            image_url=image_url, icon=icon, config_fields=config_fields,
            is_premium=is_premium, is_active=True
        )
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        logger.info("Created bot template: " + name)
        return bot

    def _detect_config_fields(self, code):
        fields = []
        patterns = [
            (r'bot_token\s*=\s*["\']', "token", "Bot Token", "text"),
            (r'TOKEN\s*=\s*["\']', "token", "Bot Token", "text"),
            (r'API_KEY\s*=\s*["\']', "api_key", "API Key", "text"),
            (r'CHAT_ID\s*=\s*["\']', "chat_id", "Chat ID", "text"),
            (r'ADMIN_ID\s*=\s*["\']', "admin_id", "Admin ID", "text"),
        ]
        for pattern, name, label, field_type in patterns:
            if re.search(pattern, code):
                fields.append({"name": name, "label": label,
                                "type": field_type, "required": True})
        return fields

    async def get_all_templates(self, db, include_inactive=False):
        query = select(ReadyBot)
        if not include_inactive:
            query = query.where(ReadyBot.is_active == True)
        result = await db.execute(query.order_by(ReadyBot.created_at.desc()))
        return result.scalars().all()

    async def get_template(self, db, bot_id):
        result = await db.execute(select(ReadyBot).where(ReadyBot.id == bot_id))
        return result.scalar_one_or_none()

    async def delete_template(self, db, bot_id):
        bot = await self.get_template(db, bot_id)
        if not bot:
            return False
        await db.delete(bot)
        await db.commit()
        return True


class UserBotService:
    def __init__(self, bots_dir: str = "/app/data/bots"):
        self.bots_dir = bots_dir
        os.makedirs(bots_dir, exist_ok=True)

    async def create_bot_instance(self, db, user, template_id, name,
                                   config, debug_mode=False):
        current_bots = await self._get_user_bot_count(db, user.id)
        if current_bots >= user.max_ready_bots:
            raise ValueError("Bot limit reached. Maximum: " + str(user.max_ready_bots))

        result = await db.execute(select(ReadyBot).where(ReadyBot.id == template_id))
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError("Bot template not found")

        modified_code = await self._generate_bot_code(template.code, config, debug_mode)

        bot_dir = os.path.join(self.bots_dir, str(user.id), str(template_id))
        os.makedirs(bot_dir, exist_ok=True)

        bot_file = os.path.join(bot_dir, "bot.py")
        with open(bot_file, "w", encoding="utf-8") as f:
            f.write(modified_code)

        if template.requirements:
            req_file = os.path.join(bot_dir, "requirements.txt")
            with open(req_file, "w", encoding="utf-8") as f:
                f.write(template.requirements)

        log_file = os.path.join(bot_dir, "bot.log")
        Path(log_file).touch()

        bot = UserBot(
            user_id=user.id, bot_template_id=template_id, name=name,
            config=config, modified_code=modified_code, bot_path=bot_dir,
            log_path=log_file, debug_mode=debug_mode, status=BotStatus.STOPPED
        )
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        return bot

    async def _generate_bot_code(self, template_code, config, debug_mode):
        config_lines = []
        for key, value in config.items():
            config_lines.append(key.upper() + ' = "' + value + '"')
        config_str = "\n".join(config_lines)
        debug_label = "Add debug logging" if debug_mode else "Keep it production-ready"

        prompt = (
            "Insert these configurations into the bot code:\n\n"
            "CONFIGURATION:\n" + config_str + "\n\n"
            "ORIGINAL CODE:\n" + template_code + "\n\n"
            "Requirements:\n"
            "1. Insert the configuration at the TOP of the file after imports\n"
            "2. Replace any placeholder tokens with the actual values\n"
            "3. Add error handling\n"
            "4. " + debug_label + "\n"
            "5. Return ONLY the complete modified code\n\n"
            "MODIFIED CODE:"
        )

        try:
            response = await ai_router.generate(
                prompt=prompt, model=AIModel.V3,
                system_prompt="You are a Python bot developer.",
                temperature=0.1, max_tokens=3000
            )
            if response.success:
                return response.content
            return self._manual_code_insertion(template_code, config)
        except Exception as e:
            logger.error("AI code generation failed: " + str(e))
            return self._manual_code_insertion(template_code, config)

    def _manual_code_insertion(self, code, config):
        config_lines = []
        for key, value in config.items():
            config_lines.append(key.upper() + ' = "' + value + '"')
        config_str = "\n".join(config_lines)
        lines = code.split("\n")
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_index = i + 1
        lines.insert(insert_index, "\n# Configuration\n" + config_str + "\n")
        return "\n".join(lines)

    async def _get_user_bot_count(self, db, user_id):
        result = await db.execute(
            select(func.count(UserBot.id)).where(UserBot.user_id == user_id)
        )
        return result.scalar()

    async def get_user_bots(self, db, user_id):
        result = await db.execute(
            select(UserBot).where(UserBot.user_id == user_id)
            .order_by(UserBot.created_at.desc())
        )
        return result.scalars().all()

    async def get_bot(self, db, bot_id, user_id):
        result = await db.execute(
            select(UserBot).where(UserBot.id == bot_id)
            .where(UserBot.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def delete_bot(self, db, bot_id, user_id):
        bot = await self.get_bot(db, bot_id, user_id)
        if not bot:
            return False
        if bot.status == BotStatus.RUNNING:
            await self.stop_bot(bot)
        if bot.bot_path and os.path.exists(bot.bot_path):
            import shutil
            shutil.rmtree(bot.bot_path)
        await db.delete(bot)
        await db.commit()
        return True

    async def start_bot(self, bot):
        if bot.status == BotStatus.RUNNING:
            return True
        try:
            bot_file = os.path.join(bot.bot_path, "bot.py")
            if not os.path.exists(bot_file):
                return False
            process = await asyncio.create_subprocess_exec(
                "python3", bot_file,
                stdout=open(bot.log_path, "a"),
                stderr=asyncio.subprocess.STDOUT,
                cwd=bot.bot_path
            )
            bot.pid = process.pid
            bot.status = BotStatus.RUNNING
            bot.started_at = datetime.utcnow()
            return True
        except Exception as e:
            logger.error("Failed to start bot: " + str(e))
            bot.status = BotStatus.ERROR
            return False

    async def stop_bot(self, bot):
        if bot.status != BotStatus.RUNNING or not bot.pid:
            return True
        try:
            import signal
            os.kill(bot.pid, signal.SIGTERM)
            bot.status = BotStatus.STOPPED
            bot.pid = None
            return True
        except ProcessLookupError:
            bot.status = BotStatus.STOPPED
            bot.pid = None
            return True
        except Exception as e:
            logger.error("Failed to stop bot: " + str(e))
            return False

    async def get_bot_logs(self, bot, lines=100):
        if not bot.log_path or not os.path.exists(bot.log_path):
            return []
        try:
            with open(bot.log_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception:
            return []


class AIBotGenerator:
    @staticmethod
    async def generate_bot(description, bot_type="telegram", features=None):
        features_list = features or []
        features_str = "\n".join(["- " + feat for feat in features_list])

        prompt = (
            "Create a complete, production-ready " + bot_type + " bot in Python.\n\n"
            "DESCRIPTION:\n" + description + "\n\n"
            "REQUIRED FEATURES:\n" + features_str + "\n\n"
            "Return your response in this exact format:\n\n"
            "===CODE===\n[The complete Python code]\n\n"
            "===REQUIREMENTS===\n[requirements.txt content]\n\n"
            "===DESCRIPTION===\n[Short description]\n\n"
            '===CONFIG_FIELDS===\n[JSON array like: [{"name": "token", "label": "Bot Token", "type": "text"}]]'
        )

        response = await ai_router.generate(
            prompt=prompt, model=AIModel.R1,
            system_prompt="You are an expert Python bot developer.",
            temperature=0.3, max_tokens=4000
        )

        if not response.success:
            raise Exception("Failed to generate bot: " + str(response.error))

        content = response.content
        result = {"code": "", "requirements": "", "description": "", "config_fields": []}

        sections = {
            "code": r"===CODE===(.+?)(?===|$)",
            "requirements": r"===REQUIREMENTS===(.+?)(?===|$)",
            "description": r"===DESCRIPTION===(.+?)(?===|$)",
            "config_fields": r"===CONFIG_FIELDS===(.+?)(?===|$)",
        }

        for key, pattern in sections.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                value = match.group(1).strip()
                if key == "config_fields":
                    try:
                        import json
                        result[key] = json.loads(value)
                    except Exception:
                        result[key] = []
                else:
                    result[key] = value

        return result

    @staticmethod
    async def debug_code(code, error_message=None):
        error_part = ""
        if error_message:
            error_part = "ERROR MESSAGE:\n" + error_message + "\n\n"

        prompt = (
            "Debug and fix this Python code:\n\n"
            "```python\n" + code + "\n```\n\n"
            + error_part +
            "Please fix and return ONLY the fixed code."
        )

        response = await ai_router.generate(
            prompt=prompt, model=AIModel.V3,
            system_prompt="You are a Python debugging expert.",
            temperature=0.2, max_tokens=3000
        )

        if response.success:
            return response.content
        raise Exception("Debug failed: " + str(response.error))


ready_bot_service = ReadyBotService()
user_bot_service = UserBotService()
ai_bot_generator = AIBotGenerator()
