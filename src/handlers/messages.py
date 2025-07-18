# src/handlers/messages.py

import logging
import tempfile
from pathlib import Path
from uuid import UUID
from datetime import datetime

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from beanie.operators import In, And

from src.bot import bot
from src.models.generation import Generation
from src.models.user import User
from src.models.app_config import AppConfig
from src.services.tapsage_storage import tapsage_upload
from src.services.tapsage_client import TapsageClient
from src.services.replicate_client import ReplicateClient
from src.texts import messages, buttons, prompts
from src.services.openai_client import OpenAIClient

logger = logging.getLogger("pp_bot.handlers.messages")


@bot.message_handler(content_types=["photo"])
async def handle_photo(message: Message):
    """
    Starts the generation flow by creating a Generation document
    and asking the user to select a service.
    """
    chat_id = message.chat.id
    
    gen = Generation(
        chat_id=chat_id,
        photo_file_id=message.photo[-1].file_id,
        status="init",
        model_name="black-forest-labs/flux-kontext-pro"
    )
    await gen.insert()
    logger.info(f"[handle_photo] New generation created. uid={gen.uid}")

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(buttons.PRODUCT_PHOTOSHOOT, callback_data=f"select_service_{gen.uid}_photoshoot"),
        InlineKeyboardButton(buttons.MODELING_PHOTOSHOOT, callback_data=f"select_service_{gen.uid}_modeling")
    )

    await bot.send_message(chat_id, messages.SELECT_SERVICE, reply_markup=markup)


@bot.message_handler(content_types=['text'])
async def handle_text_messages(message: Message):
    """
    Handles text messages based on the user's current conversation state.
    UPDATED: Sanitizes user input for both quotes and newlines.
    """
    chat_id = message.chat.id
    
    # Handlers for main menu buttons in commands.py are checked first.
    if message.text.startswith('/'):
        return

    # Find the latest pending generation for the user
    gen = await Generation.find(
        Generation.chat_id == chat_id,
        In(Generation.status, [
            "awaiting_mode_selection", "awaiting_template_selection",
            "awaiting_description", "awaiting_product_name", "awaiting_confirmation"
        ])
    ).sort(-Generation.created_at).first_or_none()

    if not gen:
        await bot.send_message(chat_id, messages.UNEXPECTED_TEXT_PROMPT)
        return

    # Sanitize the input text by escaping double quotes and replacing newlines for database storage.
    sanitized_text = message.text.replace('"', '\\"').replace('\n', '\\n')

    # --- State-aware logic ---
    if gen.status in ["awaiting_description", "awaiting_product_name"]:
        logger.info(f"[handle_text] Received text for state: {gen.status}")
        if gen.status == "awaiting_product_name":
            gen.product_name = sanitized_text
            await show_confirmation_prompt(gen)
        elif gen.status == "awaiting_description":
            gen.description = sanitized_text
            await show_confirmation_prompt(gen)
    else:
        logger.warning(f"[handle_text] User sent text '{message.text}' while in state '{gen.status}', which expects a button click.")
        await bot.send_message(chat_id, messages.PROMPT_TO_USE_BUTTONS)


async def show_confirmation_prompt(gen: Generation):
    """
    UPDATED: Desanitizes text before showing it to the user for a clean display.
    """
    gen.status = "awaiting_confirmation"
    await gen.save()

    caption = ""
    if gen.service == "photoshoot":
        mode_text = ""
        if gen.generation_mode == "template": mode_text = "قالب آماده"
        elif gen.generation_mode == "manual": mode_text = "دستی"
        elif gen.generation_mode == "automatic": mode_text = "خودکار"

        description_text = ""
        if gen.generation_mode == "template":
            cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
            template_name = "N/A"
            if cfg and cfg.style_templates:
                for t in cfg.style_templates:
                    if t["id"] == gen.template_id:
                        template_name = t["name"]; break

            # Create a display-friendly version of the product name
            display_product_name = gen.product_name.replace('\\n', '\n').replace('\\"', '"')
            description_text = f"قالب: {template_name}\nنام محصول: {display_product_name}"
        else:
            # Create a display-friendly version of the description
            display_description = gen.description.replace('\\n', '\n').replace('\\"', '"')
            description_text = display_description

        caption = messages.CONFIRMATION_PROMPT_PHOTOSHOOT.format(mode=mode_text, description=description_text)
    
    elif gen.service == "modeling":
        cfg = await AppConfig.find_one(AppConfig.type == "modeling_templates")
        template_name = "N/A"
        gender_text = "زن" if gen.model_gender == "female" else "مرد"
        templates_list = cfg.female_templates if gen.model_gender == "female" else cfg.male_templates
        
        if cfg and templates_list:
            for t in templates_list:
                if t["id"] == gen.template_id:
                    template_name = t["name"]; break
        
        caption = messages.CONFIRMATION_PROMPT_MODELING.format(
            gender=gender_text,
            template_name=template_name
        )

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(buttons.ACCEPT, callback_data=f"confirm_{gen.uid}_accept"),
        InlineKeyboardButton(buttons.EDIT, callback_data=f"confirm_{gen.uid}_edit"),
        InlineKeyboardButton(buttons.CANCEL_NEW_REQUEST, callback_data=f"confirm_{gen.uid}_cancel")
    )

    await bot.send_photo(
        gen.chat_id,
        photo=gen.photo_file_id,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )


async def process_generation_request(generation_id: UUID):
    """
    OVERHAULED: This function now prepares the final prompt in-house
    before queueing the request.
    """
    gen = await Generation.find_one(Generation.uid == generation_id)
    if not gen: return logger.error(f"Could not find generation uid={generation_id}")

    chat_id = gen.chat_id
    user = await User.find_one(User.chat_id == chat_id)

    # 1. Get cost
    costs_cfg = await AppConfig.find_one(AppConfig.type == "service_costs")
    cost = 1
    if costs_cfg and costs_cfg.service_costs:
        try:
            mode = gen.generation_mode or "template"
            cost = costs_cfg.service_costs[gen.service][mode]
        except (TypeError, KeyError):
            logger.error(f"Could not determine cost... Using fallback.")
    gen.cost = cost

    # 2. Check credits
    if not user or user.credits < gen.cost:
        gen.status = "error"; gen.error = "Insufficient credits"; await gen.save()
        return await bot.send_message(chat_id, messages.INSUFFICIENT_CREDITS.format(credits_balance=user.credits if user else 0))

    # 3. Check queue limit
    is_paid = user.paid
    if not is_paid:
        queued_item = await Generation.find_one(And(Generation.chat_id == chat_id, Generation.status == "inqueue"))
        if queued_item:
            gen.status = "cancelled"; gen.error = "Queue limit reached"; await gen.save()
            return await bot.send_message(chat_id, messages.QUEUE_LIMIT_REACHED)

    loading_message = None
    try:
        loading_message = await bot.send_message(chat_id, messages.PROCESSING_REQUEST)

        # 4. Download image bytes (needed for both upload and OpenAI)
        file_info = await bot.get_file(gen.photo_file_id)
        file_bytes = await bot.download_file(file_info.file_path)

        # 5. Generate final prompt based on service and mode
        final_prompt = ""
        openai_client = OpenAIClient()
        
        # --- PHOTOSHOOT SERVICE ---
        if gen.service == "photoshoot":
            if gen.generation_mode == "template":
                cfg = await AppConfig.find_one(AppConfig.type == "style_templates")
                if cfg and cfg.style_templates:
                    for t in cfg.style_templates:
                        if t["id"] == gen.template_id:
                            final_prompt = t["prompt"]; break
            
            elif gen.generation_mode == "manual":
                # system_prompt = "You are a precise and literal translator and prompt formatter. Your task is to take a user's description, which is in Persian, and perform two steps:\n1. Translate the user's description literally and accurately into English. Do NOT add any new creative ideas, artistic styles, lighting effects, or quality descriptors (like \"4k\", \"cinematic\", \"masterpiece\") unless the user has explicitly mentioned them. The goal is to preserve the user's original intent as closely as possible.\n2. Reformat the translated English text into a single string of keywords and phrases, separated by commas, which is suitable for an image generation model.\n\nYour entire response must be ONLY the final, comma-separated prompt string. Do not include any explanations, introductory text, or quotation marks.\n\nExample 1:\nUser's Persian input: \"یک بسته چیپس پفک روی یک میز چوبی در یک کافه دنج\"\nYour English output: \"a bag of Cheetoz puff chips, on a wooden table, in a cozy cafe\"\n\nExample 2:\nUser's Persian input: \"عکس سینمایی از یک ماشین قرمز اسپرت در شب با نورپردازی نئونی\"\nYour English output: \"cinematic photo, a red sports car, at night, with neon lighting\""
                final_prompt = await openai_client.generate_prompt_from_text(prompts.MANUAL_MODE_PROMPT, gen.description)

            elif gen.generation_mode == "automatic":
                # system_prompt = "**[ROLE & GOAL]**\nYou are \"VisioPrompt,\" an expert AI Creative Director specializing in creating prompts for AI image generators. Your mission is to transform a simple product title and a product image into a rich, detailed, and evocative photoshoot prompt. The final generated image should be a beautiful, high-end lifestyle advertisement that makes the product look irresistible and aspirational.\n\n**[CORE TASK & CRUCIAL RULES]**\nYou will be given a product title and an image. Your task is to construct a detailed prompt that describes a complete **SCENE AROUND the product**.\n* **Most Important Rule:** Do NOT describe the product itself (its color, shape, etc.). Assume the user's product image will be perfectly placed into the scene you create. Your prompt must only contain keywords for the environment, background, lighting, and overall mood.\n* **Text Rule:** Do NOT include any keywords that would add new text, words, or logos to the image.\n\n**[YOUR THOUGHT PROCESS - How to approach each request]**\n\n1.  **Analyze the Inputs:**\n    * **Product Title & Image:** Analyze the product to silently determine its category (e.g., skincare, tech, food, fashion) and its vibe (e.g., minimalist, rustic, futuristic).\n\n2.  **Brainstorm the Lifestyle Concept based on the Category:**\n    * **If Apparel & Accessories:**\n        * **CRUCIAL EXCEPTION: If the product is wristwear (like a watch or bracelet),** the prompt must be a dramatic product shot scene for the item itself, **NOT on a model's wrist**. Place it on a luxurious surface like dark marble or polished wood.\n        * For all **other apparel** (clothing, shoes, bags), the prompt MUST describe a scene suitable for a model who is wearing the product (e.g., \"a stylish model walking down a rain-slicked city street\"). You describe the scene, not the model.\n    * For other categories, invent a creative and professional setting that matches the product's function and tells a story about the lifestyle associated with it.\n\n3.  **Construct the Prompt using the Following Structure:**\n    * Start with a high-level description of the entire scene.\n    * Describe the background, environment, and supporting elements.\n    * Specify the lighting, color palette, and atmosphere.\n    * Add photography and style keywords (e.g., 'cinematic lighting', '4k', 'masterpiece').\n\n**[OUTPUT FORMAT]**\nYour final output must be a single, detailed, comma-separated block of text. Do not include the category name or any explanations.\n\n---\n**[EXAMPLES]**\n\n**Example 1 (Wristwear):**\n* **User Input:** \"ساعت مچی مردانه لوکس\"\n* **Your Output:**\n    A dramatic product shot scene, a dark polished oak surface, next to a pair of leather gloves and a high-end fountain pen, moody and focused lighting, macro photography style, sharp focus, ultra-detailed, 8k, professional advertisement.\n\n**Example 2 (Apparel):**\n* **User Input:** \"کاپشن چرم مردانه\"\n* **Your Output:**\n    A scene on a rain-slicked city street at night, with neon lights from storefronts reflecting on the wet ground, cinematic, moody atmosphere, shallow depth of field, fashion advertisement style, 4k, photorealistic.\n\n---\nYou are now ready to begin. Await the user's product title and image.If no image provided, avoid generating prompt based on the image and just user text input. Instead of decriging or naming the product in the output prompt use \"this product\" in the prompt so the image generator can generate an image bsed on the provided product image. This is not a chat session so you SHOULD response with a prompt even with not enough data"
                final_prompt = await openai_client.generate_prompt_from_image(prompts.AUTOMATIC_MODE_PROMPT, gen.description, file_bytes)
        
        # --- MODELING SERVICE ---
        elif gen.service == "modeling":
            cfg = await AppConfig.find_one(AppConfig.type == "modeling_templates")
            templates = cfg.female_templates if gen.model_gender == "female" else cfg.male_templates
            if cfg and templates:
                for t in templates:
                    if t["id"] == gen.template_id:
                        final_prompt = t["prompt"]; break
        
        gen.prompt = final_prompt
        logger.info(f"Final prompt for uid={gen.uid}: {final_prompt}")

        # 6. Upload image to storage
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_bytes(file_bytes)
        input_url = await tapsage_upload(tmp_path, file_name=tmp_path.name)
        gen.input_url = str(input_url)
        tmp_path.unlink()

        # 7. Deduct credits and queue
        user.credits -= gen.cost
        await user.save()
        gen.is_paid_user = is_paid
        gen.status = "inqueue"
        await gen.save()

        logger.info(f"uid={gen.uid} successfully placed in queue.")
        await bot.delete_message(chat_id, loading_message.message_id)
        await bot.send_message(chat_id, messages.REQUEST_QUEUED_SUCCESS)

    except Exception as e:
        logger.exception(f"Processing/Queueing failed for uid={gen.uid}: {e}")
        if loading_message: await bot.delete_message(chat_id, loading_message.message_id)
        if 'user' in locals() and user and gen.cost:
            user.credits += gen.cost; await user.save()
        gen.status = "error"; gen.error = str(e); await gen.save()
        await bot.send_message(chat_id, messages.IMAGE_GENERATION_SUBMISSION_ERROR)