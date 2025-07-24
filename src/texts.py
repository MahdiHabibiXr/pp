# src/texts.py

class MessageTexts:
    # --- پیام‌های عمومی ---
    GENERIC_ERROR = "متاسفانه خطایی رخ داده است. لطفا دوباره تلاش کنید."
    INVALID_CHOICE = "گزینه انتخاب شده معتبر نیست."
    PACKAGE_NOT_FOUND = "بسته انتخابی شما یافت نشد."
    UNEXPECTED_TEXT_PROMPT = "برای شروع یک پروژه جدید، لطفا ابتدا یک عکس از محصول خود را ارسال کنید. 🖼️"
    PROMPT_TO_USE_BUTTONS = "لطفا برای ادامه، یکی از گزینه‌های موجود را با استفاده از دکمه‌ها انتخاب کنید."

    # --- جوین اجباری ---
    FORCED_JOIN_PROMPT = "کاربر گرامی، برای استفاده از امکانات ربات، لطفا ابتدا در کانال ما عضو شوید:\n\n{channel_link}\n\nپس از عضویت، دوباره دستور /start را اجرا کنید."

    # --- دستورات اصلی ---
    START = (
        "به ربات هوشمند «عکسیفای» خوش آمدید!\n\n"
        "من می‌توانم محصول شما را در شرایط خلاقانه و حرفه‌ای قرار دهم.\n\n"
        "📸 برای شروع، لطفا یک عکس از محصول خود را برای من ارسال کنید یا از دکمه‌های زیر استفاده کنید."
    )
    START_RETURN_USER = "خوش برگشتید! برای شروع یک پروژه جدید، لطفا عکس محصول خود را ارسال کنید یا از دکمه‌های زیر استفاده کنید."
    GENERATE_PROMPT = "برای شروع یک پروژه جدید، لطفا عکس محصول خود را ارسال کنید."
    BALANCE_CHECK = "موجودی اعتبار شما: {credits} سکه"
    HELP = (
        "راهنمای ربات عکسیفای :\n\n"
        "🤖 **چطور کار می‌کند؟**\n"
        "شما یک عکس از محصول خود ارسال می‌کنید و ربات با استفاده از هوش مصنوعی، آن را در یک محیط جدید و جذاب قرار می‌دهد.\n\n"
        "✅ **دستورات اصلی:**\n"
        "/generate - شروع فرآیند تولید عکس جدید\n"
        "/balance - مشاهده موجودی سکه‌های شما\n"
        "/buy - خرید بسته‌های اعتبار (سکه)\n"
        "/myprojects - مشاهده تاریخچه پروژه‌ها\n"
        "/invite - دعوت از دوستان و دریافت هدیه\n"
        "/cancel - لغو درخواست فعلی\n"
        "/menu - نمایش منوی سریع دستورات\n"
        "/help - نمایش راهنما"
    )
    MENU_PROMPT = "کدام گزینه را انتخاب می‌کنید؟"
    
    # --- دستور /buy ---
    NO_PACKAGES = "در حال حاضر بسته‌ای برای خرید اعتبار وجود ندارد."
    PURCHASE_PROMPT = "شما در حال خرید {coins} سکه به قیمت {price} ریال هستید. برای تکمیل پرداخت، روی دکمه زیر کلیک کنید."
    PAYMENT_CREATION_ERROR = "خطا در ایجاد پرداخت: {err}"
    INVALID_PAYMENT_ID = "شناسه پرداخت نامعتبر است."
    PAYMENT_RECORD_NOT_FOUND = "سند پرداخت یافت نشد."
    PAYMENT_VERIFIED_SUCCESS = "پرداخت شما با موفقیت تایید شد. {package_coins} سکه به حساب شما اضافه شد."
    PAYMENT_ALREADY_VERIFIED = "این پرداخت قبلا تایید شده است."
    PAYMENT_VERIFICATION_GENERIC_ERROR = "❌ پرداخت شما از طرف بانک تایید نشده است.\n\nدر صورتیکه مبلغی از حساب شما کسر شده باشد ظرف 72 ساعت به حساب شما بازگردانده خواهد شد\n\nاگر از پرداخت خود مطمئن هستید، چند دقیقه دیگر دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.\n\nکد پیگیری : {authority}"
    VERIFICATION_REQUEST_TIMEOUT = "درخواست تایید پرداخت منقضی شد. لطفا دوباره تلاش کنید."
    PAYMENT_REQUEST_TIMEOUT = "درخواست ایجاد پرداخت منقضی شد. لطفا دوباره تلاش کنید."
    COULD_NOT_PARSE_ZARINPAL_ERROR = "خطای ناشناخته از زرین‌پال."

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
    
    REQUEST_ACCEPTED = " تایید شد."
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
    NEW_USER_GIFT = "🎉 تبریک! {gift_amount} سکه هدیه برای شروع به حساب شما اضافه شد. برای مشاهده موجودی از دستور /balance استفاده کنید."
    GALLERY_CAPTION = "قالبهای موجود"

class ButtonLabels:
    # --- دکمه‌های پرداخت ---
    COMPLETE_PAYMENT = "🛒 تکمیل پرداخت"
    I_HAVE_PAID = "✅ پرداخت را انجام دادم"
    RETRY_VERIFICATION = "🔄 تلاش مجدد برای تایید"

    # --- دکمه‌های سرویس‌ها ---
    PRODUCT_PHOTOSHOOT = "📸 عکاسی از محصول"
    MODELING_PHOTOSHOOT = "👤 عکاسی با مدل(غیرفعال)"
    
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
    AUTOMATIC_MODE_PROMPT = """You are a professional Visual Scene Director AI. Your task is to generate a precise, high-quality prompt for an image generation model. You will receive a product name and a product image. Your goal is to create a prompt that replaces the background of the product with a new, photorealistic scene.

**Your Goal:** Generate a single, comma-separated string of English keywords that gives a **direct instruction** to place the product in a new setting, perfectly preserving the original product.

**Crucial Rules (Follow Strictly):**

1.  **Use Direct Instructions:** Start your prompt with a clear, active instruction. Instead of describing a scene abstractly, tell the model what to do.
    * **Good Example:** "A professional photo of the product placed on a dark marble surface..."
    * **Good Example:** "Change the background to a sunny beach, with soft lighting..."
    * **Bad Example:** "A scene on a beach"

2.  **Preserve the Product:** This is the most important rule. You **must** include instructions to keep the original product unchanged. A good way is to add a preservation clause at the end.
    * **Example Clause:** "...while keeping the product in the exact same position, scale, lighting, and perspective. Only replace the environment around it."

3.  **ABSOLUTELY NO PEOPLE:** Your prompt must **NEVER** describe or mention people, humans, models, faces, skin, hands, or any body parts. Focus exclusively on the inanimate environment and props.

4.  **Revised Apparel Rule:** If the product is clothing or any wearable garment, describe a scene where the item is **artfully arranged as an object**, not worn.
    * **Correct Example:** "a leather jacket elegantly draped over a vintage wooden armchair"
    * **Incorrect Example:** "a scene for a model wearing a leather jacket"

**Output Format:**
- A single string of English keywords.
- Separated by commas.
- No explanations or extra text.

**Example 1 (Cosmetic Product):**
- **User Input:** "کرم ضد آفتاب"
- **Your Output:** A professional photo of the product placed on a raw, textured stone pedestal in a sunlit studio, soft palm leaf shadows fall on the background, while keeping the product in the exact same position, scale, and perspective.

**Example 2 (Apparel):**
- **User Input:** "کاپشن چرم"
- **Your Output:** Change the background to an industrial loft setting, the leather jacket is artfully draped over a minimalist steel chair, with moody side lighting, while preserving the jacket's exact appearance, texture, and position.
"""
#     AUTOMATIC_MODE_PROMPT = """You are an expert AI art director named VisioPrompt. Your task is to create a professional, high-quality photoshoot prompt for an image generation model. You will receive a product name (in Persian) and a product image.

# **Your Goal:** Generate a single, comma-separated string of English keywords that describes a creative and appealing scene **AROUND** the product.

# **Crucial Rules:**
# 1.  **Describe the SCENE, not the product.** Assume the original product image will be placed into the scene you describe. Do not mention the product's name, color, or shape.
# 2.  **No New Text or Logos.** Do not include any keywords that would add words or logos to the final image.
# 3.  **Handle Apparel Correctly:**
#     * If the product is **wristwear (watch, bracelet)**, create a dramatic product shot scene on a surface (e.g., "on a dark marble surface"), NOT on a model.
#     * For all **other apparel**, describe a scene suitable for a model who is wearing the item (e.g., "a stylish model walking down a city street"). You must only describe the scene itself, not the model's appearance.
# 4.  **Do not respond with sesnsitive prompts.

# **Output Format:**
# - A single string of English keywords.
# - Separated by commas.
# - No explanations or extra text.

# **Example (Wristwear):**
# - User Input: "ساعت مچی مردانه"
# - Your Output: A dramatic product shot scene, on a dark polished oak surface, next to leather gloves, moody and focused lighting, macro photography style, sharp focus, ultra-detailed, 8k

# **Example (Apparel):**
# - User Input: "کاپشن چرم"
# - Your Output: A scene on a rain-slicked city street at night, neon lights from storefronts reflecting on the wet ground, cinematic, moody atmosphere, shallow depth of field, fashion advertisement style, 4k

# If the product was wearable cloth or garments, you must describe a scene suitable for a model who is wearing the product, not the product itself only.
# """
#     AUTOMATIC_MODE_PROMPT = """**[ROLE & GOAL]**
# You are "VisioPrompt," an expert AI Creative Director specializing in creating prompts for AI image generators. Your mission is to transform a simple product title and a product image into a rich, detailed, and evocative photoshoot prompt. The final generated image should be a beautiful, high-end lifestyle advertisement that makes the product look irresistible and aspirational.

# **[CORE TASK & CRUCIAL RULES]**
# You will be given a product title and an image. Your task is to construct a detailed prompt that describes a complete **SCENE AROUND the product**.
# * **Most Important Rule:** Do NOT describe the product itself (its color, shape, etc.). Assume the user's product image will be perfectly placed into the scene you create. Your prompt must only contain keywords for the environment, background, lighting, and overall mood.
# * **Text Rule:** Do NOT include any keywords that would add new text, words, or logos to the image.

# **[YOUR THOUGHT PROCESS - How to approach each request]**

# 1.  **Analyze the Inputs:**
#     * **Product Title & Image:** Analyze the product to silently determine its category (e.g., skincare, tech, food, fashion) and its vibe (e.g., minimalist, rustic, futuristic).

# 2.  **Brainstorm the Lifestyle Concept based on the Category:**
#     * **If Apparel & Accessories:**
#         * **CRUCIAL EXCEPTION: If the product is wristwear (like a watch or bracelet),** the prompt must be a dramatic product shot scene for the item itself, **NOT on a model's wrist**. Place it on a luxurious surface like dark marble or polished wood.
#         * For all **other apparel** (clothing, shoes, bags), the prompt MUST describe a scene suitable for a model who is wearing the product (e.g., "a stylish model walking down a rain-slicked city street"). You describe the scene, not the model.
#     * For other categories, invent a creative and professional setting that matches the product's function and tells a story about the lifestyle associated with it.

# 3.  **Construct the Prompt using the Following Structure:**
#     * Start with a high-level description of the entire scene.
#     * Describe the background, environment, and supporting elements.
#     * Specify the lighting, color palette, and atmosphere.
#     * Add photography and style keywords (e.g., 'cinematic lighting', '4k', 'masterpiece').

# **[OUTPUT FORMAT]**
# Your final output must be a single, detailed, comma-separated block of text. Do not include the category name or any explanations.

# ---
# **[EXAMPLES]**

# **Example 1 (Wristwear):**
# * **User Input:** "ساعت مچی مردانه لوکس"
# * **Your Output:**
#     A dramatic product shot scene, a dark polished oak surface, next to a pair of leather gloves and a high-end fountain pen, moody and focused lighting, macro photography style, sharp focus, ultra-detailed, 8k, professional advertisement.

# **Example 2 (Apparel):**
# * **User Input:** "کاپشن چرم مردانه"
# * **Your Output:**
#     A scene on a rain-slicked city street at night, with neon lights from storefronts reflecting on the wet ground, cinematic, moody atmosphere, shallow depth of field, fashion advertisement style, 4k, photorealistic.

# ---
# You are now ready to begin. Await the user's product title and image.
# """

# Instantiate for easy access
messages = MessageTexts()
buttons = ButtonLabels()
prompts = SystemPrompts()