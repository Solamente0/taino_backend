# apps/analyzer/tasks.py
import base64
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from openai import OpenAI

from apps.analyzer.models import AnalyzerLog
from apps.ai_chat.models import AISession, ChatAIConfig

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True)
def document_analyzer_task(
    self,
    user_pid: str,
    prompt: str,
    files_data: list = None,
    voice_data: dict = None,
    ai_session_id: str = None,
    ai_type: str = "v_x",
):
    try:
        user = User.objects.get(pid=user_pid)
        ai_config = ChatAIConfig.objects.filter(static_name=ai_type, is_active=True).first()

        if not ai_config:
            return {"status": "error", "message": f"AI configuration '{ai_type}' not found"}

        client = OpenAI(
            base_url=ai_config.base_url or "https://openrouter.ai/api/v1",
            api_key=ai_config.api_key,
        )

        # Build messages
        messages = [{"role": "system", "content": ai_config.get_combined_system_prompt()}]

        # ✅ شروع با محتوای کاربر
        user_content = []

        # ✅ اول صدا را اضافه کنید (اگر وجود دارد)
        if voice_data:
            print(f"🎙️ Adding voice: {voice_data['filename']}", flush=True)

            content_type = voice_data.get("content_type", "audio/wav")  # ✅ حالا wav است
            content_b64 = voice_data.get("content_b64", "")

            # ✅ فرمت اکنون wav است
            audio_format = "wav"

            user_content.append(
                {"type": "input_audio", "input_audio": {"data": content_b64, "format": audio_format}}  # ✅ wav
            )

            print(f"✅ Voice added as WAV format", flush=True)

        # ✅ بعد prompt متنی را اضافه کنید
        if prompt and prompt.strip():
            user_content.append({"type": "text", "text": prompt})
            print(f"📝 Text prompt added: {len(prompt)} chars", flush=True)

        # ✅ سپس فایل‌ها (تصاویر/PDF)
        if files_data:
            print(f"📎 Processing {len(files_data)} files", flush=True)

            for idx, file_info in enumerate(files_data):
                try:
                    file_name = file_info.get("name", f"file_{idx}")
                    content_type = file_info.get("content_type", "")
                    content_b64 = file_info.get("content_b64", "")

                    if not content_b64:
                        continue

                    if content_type.startswith("image/") or content_type == "application/pdf":
                        # برای تصاویر و PDF از data URL استفاده کنید
                        data_url = f"data:{content_type};base64,{content_b64}"

                        user_content.append({"type": "image_url", "image_url": {"url": data_url, "detail": "high"}})
                        print(f"✅ Added file: {file_name}", flush=True)

                except Exception as file_error:
                    print(f"❌ Error processing file {idx}: {file_error}", flush=True)
                    continue

        # اضافه کردن پیام کاربر
        messages.append({"role": "user", "content": user_content})

        print(f"📤 Sending to AI - content blocks: {len(user_content)}", flush=True)
        if voice_data:
            print(f"   ✓ Voice: {voice_data.get('duration', 0)}s", flush=True)
        if prompt:
            print(f"   ✓ Text: {len(prompt)} chars", flush=True)
        if files_data:
            print(f"   ✓ Files: {len(files_data)}", flush=True)

        # API call
        try:
            response = client.chat.completions.create(
                model=ai_config.model_name,
                messages=messages,
                temperature=ai_config.default_temperature,
                max_tokens=ai_config.default_max_tokens,
            )

            analysis_text = response.choices[0].message.content
            print(f"✅ AI response: {len(analysis_text)} chars", flush=True)

        except Exception as api_error:
            print(f"❌ API Error: {api_error}", flush=True)
            logger.error(f"OpenRouter API error: {api_error}", exc_info=True)
            raise

        # Save to database
        ai_session = None
        if ai_session_id:
            try:
                ai_session = AISession.objects.get(pid=ai_session_id, user=user)
            except AISession.DoesNotExist:
                pass

        log = AnalyzerLog.objects.create(
            user=user,
            prompt=prompt,
            analysis_text=analysis_text,
            ai_type=ai_type,
            ai_session=ai_session,
        )

        print(f"💾 Analysis saved for user {user_pid}", flush=True)

        return {
            "status": "success",
            "analysis": analysis_text,
            "log_pid": str(log.pid),
        }

    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        logger.error(f"Error in document_analyzer_task: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
