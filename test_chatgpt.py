import asyncio
from openai import AsyncOpenAI

aclient = AsyncOpenAI(api_key=os.getenv("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"))
import os

# Выведите версию для проверки
print("OpenAI version:", openai.__version__)

# Убедитесь, что переменная окружения OPENAI_API_KEY установлена
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY не установлен!")

async def get_chatgpt_response(prompt: str) -> str:
    try:
        response = await aclient.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Ты - опытный гид по мотопутешествиям. На основе данных из запроса ты составляешь маршрут для мотопутешествия. "
                "Анализируй маршруты, опубликованные в интернете, опыт других путешественников, твои знания об особенностях мотуров. "
                "Для составления маршрута важно учесть тайминг поездки, погодные условия, заправки, места для питания, отели, достопримечательности и дорожные условия."
            )},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0.7)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка при обращении к ChatGPT: {e}"

async def main():
    prompt = "Пример запроса: Санкт-Петербург - Карелия, даты: 18-29 июня"
    answer = await get_chatgpt_response(prompt)
    print("Ответ ChatGPT:", answer)

if __name__ == "__main__":
    asyncio.run(main())
