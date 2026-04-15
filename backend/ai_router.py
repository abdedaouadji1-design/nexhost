"""
NexHost V6 - AI Router
======================
Smart AI provider router with fallback mechanism
Supports multiple DeepSeek unofficial APIs
"""
import asyncio
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import httpx
from datetime import datetime, timedelta

from config import settings

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """Available AI models"""
    V3 = "deepseek chat"
    R1 = "deepseek reasoning"


@dataclass
class AIResponse:
    """AI response wrapper"""
    success: bool
    content: str
    model: str
    provider: str
    latency_ms: float
    error: Optional[str] = None
    cached: bool = False


class AIProvider:
    """Base AI provider class"""
    
    def __init__(self, name: str, base_url: str, api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.AI_TIMEOUT),
            follow_redirects=True,
            headers={
                "User-Agent": "NexHost-V6/1.0",
                "Accept": "application/json",
            }
        )
        self.is_healthy = True
        self.last_error: Optional[str] = None
    
    async def generate(
        self, 
        prompt: str, 
        model: AIModel = AIModel.V3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """Generate response from AI"""
        raise NotImplementedError
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            response = await self.client.get(
                self.base_url,
                timeout=5.0
            )
            self.is_healthy = response.status_code < 500
            return self.is_healthy
        except Exception as e:
            self.is_healthy = False
            self.last_error = str(e)
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class PrimaryProvider(AIProvider):
    """Primary DeepSeek Provider (xvest3.ru)"""
    
    def __init__(self):
        super().__init__(
            name="Primary-XVest",
            base_url=settings.AI_PRIMARY_URL,
            api_key=settings.AI_PRIMARY_KEY
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: AIModel = AIModel.V3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """Generate using primary API"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            payload = {
                "key": self.api_key,
                "model": model.value,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Extract content based on response format
            content = self._extract_content(data)
            
            return AIResponse(
                success=True,
                content=content,
                model=model.value,
                provider=self.name,
                latency_ms=latency
            )
            
        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            self.is_healthy = False
            self.last_error = str(e)
            logger.error(f"Primary provider error: {e}")
            
            return AIResponse(
                success=False,
                content="",
                model=model.value,
                provider=self.name,
                latency_ms=latency,
                error=str(e)
            )
    
    def _extract_content(self, data: Dict[str, Any]) -> str:
        """Extract content from API response"""
        # Try different response formats
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice:
                return choice["message"].get("content", "")
            elif "text" in choice:
                return choice["text"]
        
        if "response" in data:
            return data["response"]
        
        if "content" in data:
            return data["content"]
        
        if "result" in data:
            return data["result"]
        
        return str(data)


class SecondaryProvider(AIProvider):
    """Secondary DeepSeek Provider (onrender.com)"""
    
    def __init__(self):
        super().__init__(
            name="Secondary-Render",
            base_url=settings.AI_SECONDARY_URL,
            api_key=settings.AI_SECONDARY_KEY
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: AIModel = AIModel.V3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """Generate using secondary API"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model.value,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            
            content = self._extract_content(data)
            
            return AIResponse(
                success=True,
                content=content,
                model=model.value,
                provider=self.name,
                latency_ms=latency
            )
            
        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            self.is_healthy = False
            self.last_error = str(e)
            logger.error(f"Secondary provider error: {e}")
            
            return AIResponse(
                success=False,
                content="",
                model=model.value,
                provider=self.name,
                latency_ms=latency,
                error=str(e)
            )
    
    def _extract_content(self, data: Dict[str, Any]) -> str:
        """Extract content from API response"""
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0].get("message", {}).get("content", "")
        if "response" in data:
            return data["response"]
        return str(data)


class TertiaryProvider(AIProvider):
    """Tertiary DeepSeek Provider (serv00.net)"""
    
    def __init__(self):
        super().__init__(
            name="Tertiary-Serv00",
            base_url=settings.AI_TERTIARY_URL,
            api_key=None
        )
    
    async def generate(
        self, 
        prompt: str, 
        model: AIModel = AIModel.V3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AIResponse:
        """Generate using tertiary API"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            payload = {
                "message": prompt,
                "model": model.value
            }
            
            response = await self.client.post(
                self.base_url,
                data=payload,  # Form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()
            
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            
            content = data.get("response", data.get("message", data.get("result", str(data))))
            
            return AIResponse(
                success=True,
                content=content,
                model=model.value,
                provider=self.name,
                latency_ms=latency
            )
            
        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            self.is_healthy = False
            self.last_error = str(e)
            logger.error(f"Tertiary provider error: {e}")
            
            return AIResponse(
                success=False,
                content="",
                model=model.value,
                provider=self.name,
                latency_ms=latency,
                error=str(e)
            )


class SimpleCache:
    """Simple in-memory cache for AI responses"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
    
    def _generate_key(self, prompt: str, model: str) -> str:
        """Generate cache key"""
        key_string = f"{prompt}:{model}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, prompt: str, model: str) -> Optional[str]:
        """Get cached response"""
        key = self._generate_key(prompt, model)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry["expires_at"]:
                logger.info(f"Cache hit for key: {key[:8]}...")
                return entry["content"]
            else:
                del self.cache[key]
        return None
    
    def set(self, prompt: str, model: str, content: str):
        """Cache response"""
        key = self._generate_key(prompt, model)
        self.cache[key] = {
            "content": content,
            "expires_at": datetime.now() + timedelta(seconds=self.ttl)
        }
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()


class AIRouter:
    """
    Smart AI Router with:
    - Multiple provider support
    - Automatic fallback
    - Response caching
    - Health monitoring
    - Load balancing
    """
    
    def __init__(self):
        self.providers: List[AIProvider] = [
            PrimaryProvider(),
            SecondaryProvider(),
            TertiaryProvider()
        ]
        self.cache = SimpleCache(ttl_seconds=settings.AI_CACHE_TTL)
        self.current_provider_index = 0
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0
        }
    
    async def generate(
        self,
        prompt: str,
        model: AIModel = AIModel.V3,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_cache: bool = True,
        prefer_provider: Optional[str] = None
    ) -> AIResponse:
        """
        Generate AI response with smart fallback
        
        Args:
            prompt: User prompt
            model: AI model to use
            system_prompt: System instructions
            temperature: Creativity (0-1)
            max_tokens: Max response length
            use_cache: Whether to use caching
            prefer_provider: Preferred provider name
        
        Returns:
            AIResponse with result or error
        """
        self.stats["total_requests"] += 1
        
        # Check cache first
        if use_cache:
            cached = self.cache.get(prompt, model.value)
            if cached:
                self.stats["cache_hits"] += 1
                return AIResponse(
                    success=True,
                    content=cached,
                    model=model.value,
                    provider="cache",
                    latency_ms=0,
                    cached=True
                )
        
        # Get ordered list of providers
        providers = self._get_provider_order(prefer_provider)
        
        last_error = None
        
        # Try each provider with retries
        for provider in providers:
            if not provider.is_healthy:
                logger.warning(f"Skipping unhealthy provider: {provider.name}")
                continue
            
            for attempt in range(settings.AI_MAX_RETRIES):
                try:
                    logger.info(f"Trying {provider.name}, attempt {attempt + 1}")
                    
                    response = await provider.generate(
                        prompt=prompt,
                        model=model,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    if response.success:
                        # Cache successful response
                        if use_cache:
                            self.cache.set(prompt, model.value, response.content)
                        
                        self.stats["successful_requests"] += 1
                        logger.info(f"Success with {provider.name} in {response.latency_ms:.0f}ms")
                        return response
                    else:
                        logger.warning(f"Provider {provider.name} returned error: {response.error}")
                        
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Provider {provider.name} exception: {e}")
                    await asyncio.sleep(settings.AI_RETRY_DELAY * (attempt + 1))
        
        # All providers failed
        self.stats["failed_requests"] += 1
        logger.error("All AI providers failed")
        
        return AIResponse(
            success=False,
            content="",
            model=model.value,
            provider="all_failed",
            latency_ms=0,
            error=f"All providers failed. Last error: {last_error}"
        )
    
    def _get_provider_order(self, prefer: Optional[str] = None) -> List[AIProvider]:
        """Get providers in priority order"""
        providers = self.providers.copy()
        
        # Move preferred provider to front
        if prefer:
            for i, p in enumerate(providers):
                if p.name == prefer:
                    providers.insert(0, providers.pop(i))
                    break
        
        # Sort by health
        providers.sort(key=lambda p: not p.is_healthy)
        
        return providers
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers"""
        results = {}
        for provider in self.providers:
            results[provider.name] = await provider.health_check()
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            **self.stats,
            "providers": [
                {
                    "name": p.name,
                    "healthy": p.is_healthy,
                    "last_error": p.last_error
                }
                for p in self.providers
            ],
            "cache_size": len(self.cache.cache)
        }
    
    async def close_all(self):
        """Close all provider connections"""
        for provider in self.providers:
            await provider.close()


# Global AI router instance
ai_router = AIRouter()


# Convenience functions
async def ai_chat(
    message: str,
    model: str = "v3",
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """Simple chat interface"""
    ai_model = AIModel.V3 if model == "v3" else AIModel.R1
    
    response = await ai_router.generate(
        prompt=message,
        model=ai_model,
        system_prompt=system_prompt,
        **kwargs
    )
    
    if response.success:
        return response.content
    else:
        raise Exception(response.error or "AI generation failed")


async def ai_code_fix(code: str, language: str = "python") -> str:
    """Fix code using AI"""
    prompt = f"""Fix and improve this {language} code. Return ONLY the fixed code without explanations:

```{language}
{code}
```
"""
    return await ai_chat(prompt, system_prompt="You are an expert programmer. Fix code issues and return only the corrected code.")


async def ai_code_explain(code: str, language: str = "python") -> str:
    """Explain code using AI"""
    prompt = f"""Explain this {language} code in detail:

```{language}
{code}
```
"""
    return await ai_chat(prompt, system_prompt="You are a programming teacher. Explain code clearly with examples.")


async def ai_bot_generator(description: str, bot_type: str = "telegram") -> str:
    """Generate bot code using AI"""
    prompt = f"""Create a complete, working {bot_type} bot in Python based on this description:

{description}

Requirements:
- Use python-telegram-bot library
- Include proper error handling
- Add comments in Arabic
- Make it production-ready
- Include requirements.txt content as comment

Return ONLY the complete Python code."""
    
    return await ai_chat(prompt, system_prompt="You are a bot developer. Create complete, working bot code.")


async def ai_insert_token(code: str, token: str, chat_id: Optional[str] = None) -> str:
    """Insert token into bot code using AI"""
    prompt = f"""Insert this token into the bot code:
TOKEN = "{token}"
{f'CHAT_ID = "{chat_id}"' if chat_id else ''}

Original code:
{code}

Return the complete code with token inserted in the correct place."""
    
    return await ai_chat(prompt, system_prompt="You are a bot developer. Insert tokens securely.")
