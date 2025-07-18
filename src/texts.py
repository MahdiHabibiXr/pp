# src/texts.py

class MessageTexts:
    # --- پیام‌های عمومی ---
    GENERIC_ERROR = "متاسفانه خطایی رخ داده است. لطفا دوباره تلاش کنید."
    INVALID_CHOICE = "گزینه انتخاب شده معتبر نیست."
    PACKAGE_NOT_FOUND = "بسته انتخابی شما یافت نشد."
    UNEXPECTED_TEXT_PROMPT = "برای شروع یک پروژه جدید، لطفا ابتدا یک عکس از محصول خود را ارسال کنید. 🖼️"
    PROMPT_TO_USE_BUTTONS = "لطفا برای ادامه، یکی از گزینه‌های موجود را با استفاده از دکمه‌ها انتخاب کنید. 👇"

    # --- جوین اجباری ---
    FORCED_JOIN_PROMPT = "کاربر گرامی، برای استفاده از امکانات ربات، لطفا ابتدا در کانال ما عضو شوید:\n\n{channel_link}\n\nپس از عضویت، دوباره دستور /start را اجرا کنید."

    # --- دستورات اصلی ---
    START = (
        "به ربات هوشمند «محصولتو بذار» خوش آمدید!\n\n"
        "من می‌توانم محصول شما را در تصاویر خلاقانه و حرفه‌ای قرار دهم.\n\n"
        "📸 برای شروع، لطفا یک عکس از محصول خود را برای من ارسال کنید یا از دکمه‌های زیر استفاده کنید."
    )
    START_RETURN_USER = "خوش برگشتید! برای شروع یک پروژه جدید، لطفا عکس محصول خود را ارسال کنید یا از دکمه‌های زیر استفاده کنید."
    GENERATE_PROMPT = "برای شروع یک پروژه جدید، لطفا عکس محصول خود را ارسال کنید."
    BALANCE_CHECK = "موجودی اعتبار شما: {credits} سکه"
    HELP = (
        "راهنمای ربات «محصولتو بذار»:\n\n"
        "🤖 **چطور کار می‌کند؟**\n"
        "شما یک عکس از محصول خود ارسال می‌کنید و ربات با استفاده از هوش مصنوعی، آن را در یک تصویر جدید و جذاب قرار می‌دهد.\n\n"
        "✅ **دستورات اصلی:**\n"
        "/generate - شروع فرآیند تولید عکس جدید\n"
        "/balance - مشاهده موجودی سکه‌های شما\n"
        "/buy - خرید بسته‌های اعتبار (سکه)\n"
        "/myprojects - مشاهده تاریخچه پروژه‌ها\n"
        "/invite - دعوت از دوستان و دریافت هدیه\n"
        "/cancel - لغو درخواست فعلی\n"
        "/menu - نمایش منوی سریع دستورات\n"
        "/help - نمایش همین راهنما"
    )
    MENU_PROMPT = "کدام گزینه را انتخاب می‌کنید؟"
    
    # --- دستور /buy ---
    NO_PACKAGES = "در حال حاضر بسته‌ای برای خرید اعتبار وجود ندارد."

    # --- جریان اصلی ربات و مکالمات ---
    SELECT_SERVICE = "تصویر شما دریافت شد. لطفا سرویس مورد نظر را انتخاب کنید:"
    SELECT_MODE = "بسیار عالی! لطفا روش تولید تصویر را انتخاب کنید:"
    SELECT_TEMPLATE = "لطفا یک قالب آماده را از لیست زیر انتخاب کنید:"
    PROVIDE_PRODUCT_NAME = "لطفا نام دقیق محصول خود را وارد کنید (مثال: کرم ضد آفتاب لافارر)."
    PROVIDE_FULL_DESCRIPTION = "لطفا تمام توضیحات مورد نظر برای تصویر نهایی را به طور کامل بنویسید."
    PROVIDE_SIMPLE_CAPTION = "لطفا یک نام یا توضیح کوتاه برای محصول خود بنویسید تا هوش مصنوعی بهترین تصویر را برایتان خلق کند."
    
    # --- بخش مدلینگ ---
    SELECT_MODEL_GENDER = "لطفا جنسیت مدل را انتخاب کنید:"

    # --- تنظیمات پیشرفته ---
    ADVANCED_SETTINGS_PROMPT = "تنظیمات پیشرفته درخواست:\nمی‌توانید ویژگی‌های زیر را تغییر دهید یا برای تایید نهایی، روی دکمه پذیرش کلیک کنید."
    SELECT_LIGHTING = "سبک نورپردازی را انتخاب کنید:"
    SELECT_COLOR_THEME = "تم رنگی پس‌زمینه را انتخاب کنید:"

    # --- پیام‌های تایید ---
    CONFIRMATION_PROMPT_PHOTOSHOOT = "لطفا درخواست عکاسی محصول خود را بازبینی و تایید کنید:\n\n**حالت:** {mode}\n**توضیحات:** {description}"
    CONFIRMATION_PROMPT_MODELING = "لطفا درخواست عکاسی مدلینگ خود را بازبینی و تایید کنید:\n\n**جنسیت مدل:** {gender}\n**قالب انتخابی:** {template_name}"
    
    REQUEST_ACCEPTED = "✅ درخواست شما تایید و به صف پردازش اضافه شد."
    REQUEST_CANCELLED = "❌ درخواست لغو شد. برای شروع مجدد، لطفا تصویر جدیدی ارسال کنید."
    EDIT_PROMPT_PRODUCT_NAME = "✏️ لطفا نام جدید محصول را وارد کنید."
    EDIT_PROMPT_DESCRIPTION = "✏️ لطفا توضیحات جدید خود را وارد کنید."

    GENERATION_NOT_FOUND_FOR_USER = "متاسفانه درخواست فعالی برای شما پیدا نشد. لطفا با ارسال یک عکس جدید، فرآیند را شروع کنید."
    INSUFFICIENT_CREDITS = "⚠️ اعتبار شما کافی نیست.\nموجودی فعلی: {credits_balance} سکه\nبرای خرید اعتبار از دستور /buy استفاده کنید."
    PROCESSING_REQUEST = "⏳ درخواست شما در حال پردازش است، لطفا کمی صبر کنید..."
    REQUEST_QUEUED_SUCCESS = "✅ درخواست شما با موفقیت در صف قرار گرفت و به زودی پردازش خواهد شد."
    IMAGE_GENERATION_SUBMISSION_ERROR = "❌ در ثبت درخواست شما خطایی رخ داد. اعتبار شما بازگردانده شد. لطفا دوباره تلاش کنید."
    QUEUE_LIMIT_REACHED = "شما در حال حاضر یک درخواست در صف پردازش دارید. لطفا تا تکمیل آن صبر کنید."
    REQUEST_CANCELLED_SUCCESS = "درخواست شما با موفقیت لغو شد و اعتبار آن به حساب شما بازگردانده شد."
    REQUEST_ALREADY_PROCESSED = "این درخواست قبلا پردازش شده و دیگر قابل لغو نیست."

    # --- تاریخچه پروژه‌ها ---
    MY_PROJECTS_HEADER = "لیست ۵ پروژه اخیر شما به شرح زیر است:"
    NO_PROJECTS_FOUND = "شما هنوز هیچ پروژه‌ای ثبت نکرده‌اید. برای شروع از دکمه «پروژه جدید» استفاده کنید."
    PROJECT_STATUS_FORMAT = "{status_icon} **{description}**\n*تاریخ ثبت: {date}*"

    # --- سیستم دعوت از دوستان ---
    INVITE_FRIENDS = (
        "از دوستان خود دعوت کنید و سکه هدیه بگیرید! 🎁\n\n"
        "به ازای هر دوستی که با لینک اختصاصی شما وارد ربات شود، **{reward_amount} سکه** به شما هدیه داده می‌شود.\n\n"
        "لینک دعوت شما:\n"
        "`{invite_link}`\n\n"
        "(روی لینک بزنید تا کپی شود)"
    )
    REFERRAL_SUCCESS_NOTIFICATION = "🎉 تبریک! یک کاربر جدید با لینک شما عضو شد و **{reward_amount} سکه** به شما هدیه داده شد."
    NEW_USER_GIFT = "🎉 تبریک! ۱۰ سکه هدیه برای شروع به حساب شما اضافه شد. برای مشاهده موجودی از دستور /balance استفاده کنید."
    GALLERY_CAPTION = "قالبهای موجود"

class ButtonLabels:
    # --- دکمه‌های پرداخت ---
    COMPLETE_PAYMENT = "🛒 تکمیل پرداخت"
    I_HAVE_PAID = "✅ پرداخت را انجام دادم"
    RETRY_VERIFICATION = "🔄 تلاش مجدد برای تایید"

    # --- دکمه‌های سرویس‌ها ---
    PRODUCT_PHOTOSHOOT = "📸 عکاسی از محصول"
    MODELING_PHOTOSHOOT = "👤 عکاسی با مدل"
    
    # --- دکمه‌های مدلینگ ---
    MODEL_GENDER_MALE = "مرد"
    MODEL_GENDER_FEMALE = "زن"

    # --- دکمه‌های انتخاب حالت ---
    MODE_TEMPLATE = "🖼 انتخاب از قالب‌های آماده"
    MODE_MANUAL = "✍️ نوشتن توضیحات کامل"
    MODE_AUTOMATIC = "🤖 پردازش کاملا خودکار"

    # --- دکمه‌های تایید و تنظیمات پیشرفته ---
    ACCEPT = "✅ تایید و ارسال"
    EDIT = "✏️ ویرایش"
    CANCEL_NEW_REQUEST = "❌ لغو و شروع مجدد"
    ADVANCED_SETTINGS = "⚙️ تنظیمات پیشرفته"

    # --- دکمه‌های منوی شیشه‌ای (/menu) ---
    MENU_GENERATE = "📸 تولید عکس جدید"
    MENU_BALANCE = "💰 موجودی اعتبار"
    MENU_BUY = "🛍 خرید اعتبار"
    MENU_HELP = "ℹ️ راهنما"
    MENU_INVITE = "💌 دعوت از دوستان"

    # --- دکمه‌های کیبورد اصلی ---
    MAIN_KEYBOARD_NEW = "📸 پروژه جدید"
    MAIN_KEYBOARD_BALANCE = "💰 اعتبار من"
    MAIN_KEYBOARD_BUY = "🛍 خرید اعتبار"
    MAIN_KEYBOARD_HELP = "راهنما ℹ️"
    MAIN_KEYBOARD_PROJECTS = "📂 پروژه‌های من"
    MAIN_KEYBOARD_INVITE = "💌 دعوت از دوستان"

    # --- دکمه‌های تاریخچه ---
    RESEND_IMAGE = "📥 دریافت مجدد"
    CANCEL_REQUEST = "❌ لغو درخواست"

class SystemPrompts:
    MANUAL_MODE_PROMPT = "You are a precise and literal translator and prompt formatter. Your task is to take a user's description, which is in Persian, and perform two steps:\n1. Translate the user's description literally and accurately into English. Do NOT add any new creative ideas, artistic styles, lighting effects, or quality descriptors (like \"4k\", \"cinematic\", \"masterpiece\") unless the user has explicitly mentioned them. The goal is to preserve the user's original intent as closely as possible.\n2. Reformat the translated English text into a single string of keywords and phrases, separated by commas, which is suitable for an image generation model.\n\nYour entire response must be ONLY the final, comma-separated prompt string. Do not include any explanations, introductory text, or quotation marks.\n\nExample 1:\nUser's Persian input: \"یک بسته چیپس پفک روی یک میز چوبی در یک کافه دنج\"\nYour English output: \"a bag of Cheetoz puff chips, on a wooden table, in a cozy cafe\"\n\nExample 2:\nUser's Persian input: \"عکس سینمایی از یک ماشین قرمز اسپرت در شب با نورپردازی نئونی\"\nYour English output: \"cinematic photo, a red sports car, at night, with neon lighting\""
    AUTOMATIC_MODE_PROMPT = """**[ROLE & GOAL]**
You are "VisioPrompt," an expert AI Creative Director specializing in creating prompts for AI image generators. Your mission is to transform a simple product title and a product image into a rich, detailed, and evocative photoshoot prompt. The final generated image should be a beautiful, high-end lifestyle advertisement that makes the product look irresistible and aspirational.

**[CORE TASK & CRUCIAL RULES]**
You will be given a product title and an image. Your task is to construct a detailed prompt that describes a complete **SCENE AROUND the product**.
* **Most Important Rule:** Do NOT describe the product itself (its color, shape, etc.). Assume the user's product image will be perfectly placed into the scene you create. Your prompt must only contain keywords for the environment, background, lighting, and overall mood.
* **Text Rule:** Do NOT include any keywords that would add new text, words, or logos to the image.

**[YOUR THOUGHT PROCESS - How to approach each request]**

1.  **Analyze the Inputs:**
    * **Product Title & Image:** Analyze the product to silently determine its category (e.g., skincare, tech, food, fashion) and its vibe (e.g., minimalist, rustic, futuristic).

2.  **Brainstorm the Lifestyle Concept based on the Category:**
    * **If Apparel & Accessories:**
        * **CRUCIAL EXCEPTION: If the product is wristwear (like a watch or bracelet),** the prompt must be a dramatic product shot scene for the item itself, **NOT on a model's wrist**. Place it on a luxurious surface like dark marble or polished wood.
        * For all **other apparel** (clothing, shoes, bags), the prompt MUST describe a scene suitable for a model who is wearing the product (e.g., "a stylish model walking down a rain-slicked city street"). You describe the scene, not the model.
    * For other categories, invent a creative and professional setting that matches the product's function and tells a story about the lifestyle associated with it.

3.  **Construct the Prompt using the Following Structure:**
    * Start with a high-level description of the entire scene.
    * Describe the background, environment, and supporting elements.
    * Specify the lighting, color palette, and atmosphere.
    * Add photography and style keywords (e.g., 'cinematic lighting', '4k', 'masterpiece').

**[OUTPUT FORMAT]**
Your final output must be a single, detailed, comma-separated block of text. Do not include the category name or any explanations.

---
**[EXAMPLES]**

**Example 1 (Wristwear):**
* **User Input:** "ساعت مچی مردانه لوکس"
* **Your Output:**
    A dramatic product shot scene, a dark polished oak surface, next to a pair of leather gloves and a high-end fountain pen, moody and focused lighting, macro photography style, sharp focus, ultra-detailed, 8k, professional advertisement.

**Example 2 (Apparel):**
* **User Input:** "کاپشن چرم مردانه"
* **Your Output:**
    A scene on a rain-slicked city street at night, with neon lights from storefronts reflecting on the wet ground, cinematic, moody atmosphere, shallow depth of field, fashion advertisement style, 4k, photorealistic.

---
You are now ready to begin. Await the user's product title and image.
"""

# Instantiate for easy access
messages = MessageTexts()
buttons = ButtonLabels()
prompts = SystemPrompts()