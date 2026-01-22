"""Builder API client for construction-time LLM calls."""

from typing import Optional, Type, Any, TypeVar
from pydantic import BaseModel, Field
import httpx
import os
import json

# Optional imports for different providers
try:
    from langchain_openai import ChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_anthropic import ChatAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from src.utils.json_utils import extract_json_from_text

T = TypeVar("T", bound=BaseModel)


class BuilderAPIConfig(BaseModel):
    """Configuration for Builder API."""

    provider: str = Field(..., description="API provider (openai/anthropic/azure)")
    model: str = Field(..., description="Model name")
    api_key: str = Field(..., description="API key")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")
    timeout: int = Field(default=60, description="Timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")


class BuilderClient:
    """Builder API client for construction-time LLM calls.
    
    This client is used by PM, Graph Designer, RAG Builder, and other
    construction-time components. It uses a powerful model (GPT-4o, Claude 3.5)
    to generate high-quality agent designs.
    """

    def __init__(self, config: BuilderAPIConfig):
        """Initialize Builder API client.
        
        Args:
            config: Builder API configuration
        """
        self.config = config
        self.client = self._init_client(config)

    def _init_client(self, config: BuilderAPIConfig) -> Any:
        """Initialize LLM client based on provider.
        
        Args:
            config: Builder API configuration
            
        Returns:
            Initialized LLM client
        """
        if config.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError(
                    "langchain-openai is not installed. "
                    "Install it with: pip install langchain-openai"
                )
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                base_url=config.base_url,
                temperature=config.temperature,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        elif config.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError(
                    "langchain-anthropic is not installed. "
                    "Install it with: pip install langchain-anthropic"
                )
            return ChatAnthropic(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    async def call(
        self, prompt: str, schema: Optional[Type[BaseModel]] = None
    ) -> str | BaseModel:
        """Call Builder API with optional structured output.
        
        Args:
            prompt: Input prompt
            schema: Optional Pydantic schema for structured output
            
        Returns:
            Response string or structured output
        """
        if schema:
            # Use new universal structured generator
            return await self.generate_structured(prompt, schema)
        else:
            # Regular text output
            response = await self.client.ainvoke(prompt)
            return response.content

    async def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T],
        temperature: Optional[float] = None
    ) -> T:
        """
        通用的结构化输出生成器
        自动处理 DeepSeek 等不支持 response_format 的情况
        
        Args:
            prompt: 输入提示词
            response_model: Pydantic 模型类
            temperature: 可选的温度参数
        
        Returns:
            验证后的 Pydantic 模型实例
        """
        temp = temperature if temperature is not None else self.config.temperature
        
        # 获取 Pydantic 的 Schema
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

        # -------------------------------------------------------
        # 尝试 1: 原生支持模式 (LangChain with_structured_output)
        # -------------------------------------------------------
        try:
            structured_llm = self.client.with_structured_output(response_model)
            result = await structured_llm.ainvoke(prompt)
            return result

        except Exception as e:
            # 捕获各种可能的错误
            error_str = str(e).lower()
            
            # 检查是否是 response_format 不支持的错误
            if any(keyword in error_str for keyword in [
                "response_format", "unavailable", "400", 
                "bad request", "invalid_request_error"
            ]):
                print(f"⚠️  API 不支持原生 JSON 模式，切换到 Prompt 增强模式...")
                return await self._generate_structured_fallback(
                    prompt, response_model, schema_str, temp
                )
            else:
                # 其他错误（如余额不足）直接抛出
                raise e

    async def _generate_structured_fallback(
        self, 
        prompt: str, 
        response_model: Type[T], 
        schema_str: str,
        temperature: float
    ) -> T:
        """
        回退模式：通过 Prompt 强制模型输出 JSON，并使用正则提取
        
        Args:
            prompt: 原始提示词
            response_model: Pydantic 模型类
            schema_str: JSON Schema 字符串
            temperature: 温度参数
        
        Returns:
            验证后的 Pydantic 模型实例
        """
        # 1. 深度修改 Prompt：把 Schema 塞进去
        fallback_prompt = (
            f"{prompt}\n\n"
            f"🛑 CRITICAL INSTRUCTION: OUTPUT FORMAT ENFORCEMENT 🛑\n"
            f"You MUST output a valid JSON object matching the following schema.\n"
            f"Do NOT include any conversational text, explanations, or markdown code blocks.\n"
            f"Output ONLY the raw JSON object.\n\n"
            f"Required JSON Schema:\n"
            f"```json\n{schema_str}\n```\n\n"
            f"Your response (JSON only):"
        )

        # 2. 普通文本模式调用
        response = await self.client.ainvoke(fallback_prompt)
        raw_text = response.content

        # 3. 清洗和解析
        try:
            json_str = extract_json_from_text(raw_text)
        except ValueError as e:
            print(f"❌ JSON 提取失败: {e}")
            print(f"原始文本: {raw_text[:200]}...")
            raise ValueError(f"Failed to extract JSON from LLM response: {e}")
        
        # 4. Pydantic 校验 (这一步最关键，确保格式对了)
        try:
            return response_model.model_validate_json(json_str)
        except Exception as e:
            print(f"❌ Pydantic 验证失败: {e}")
            print(f"提取的 JSON: {json_str[:200]}...")
            raise ValueError(f"Failed to validate JSON against schema: {e}")

    async def health_check(self) -> bool:
        """Check API connectivity.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Simple test call
            response = await self.client.ainvoke("Hello")
            return True
        except Exception as e:
            print(f"Builder API health check failed: {e}")
            return False

    @classmethod
    def from_env(cls) -> "BuilderClient":
        """Create Builder client from environment variables.
        
        Returns:
            Initialized BuilderClient
        """
        config = BuilderAPIConfig(
            provider=os.getenv("BUILDER_PROVIDER", "openai"),
            model=os.getenv("BUILDER_MODEL", "gpt-4o"),
            api_key=os.getenv("BUILDER_API_KEY", ""),
            base_url=os.getenv("BUILDER_BASE_URL"),
            timeout=int(os.getenv("BUILDER_TIMEOUT", "60")),
            max_retries=int(os.getenv("BUILDER_MAX_RETRIES", "3")),
            temperature=float(os.getenv("BUILDER_TEMPERATURE", "0.7")),
        )
        return cls(config)

