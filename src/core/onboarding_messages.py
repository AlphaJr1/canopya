MESSAGES = {
    'welcome': """Halo! 👋 Selamat datang di Canopya!

Saya akan membantu Anda merawat tanaman hidroponik dengan:
• 📊 Monitoring pH, TDS, dan suhu
• 💡 Panduan lengkap perawatan
• 🚨 Alert otomatis jika ada masalah
• ⚡ Quick actions untuk perbaikan

Sebelum mulai, saya perlu kenalan dulu dengan Anda. Siap? 😊

Siapa nama Anda?""",

    'ask_plant_name': """Senang berkenalan dengan Anda, {name}! 🌱

Sekarang, tanaman apa yang sedang Anda tanam?""",

    'ask_growth_stage': """Baik, {plant_name} ya! 🌿

Sekarang di tahap pertumbuhan apa?
1️⃣ Seedling (Bibit/Baru ditanam)
2️⃣ Vegetatif (Tumbuh daun)
3️⃣ Berbuah/Berbunga""",

    'confirm_data': """Oke, saya sudah catat data Anda:

👤 Nama: {name}
🌱 Tanaman: {plant_name} ({plant_type})
📊 Tahap: {growth_stage}

Apakah data ini sudah benar?
Ketik *Ya* untuk lanjut, atau *Tidak* untuk input ulang.""",

    'tutorial': """Sekarang saya akan tunjukkan apa saja yang bisa saya bantu:

🔍 Monitoring Sensor
Tanyakan kondisi tanaman Anda:
• _"bagaimana kondisi tanaman saya?"_
• _"cek pH dan TDS"_

💡 Panduan & Tips
Tanyakan cara merawat tanaman:
• _"bagaimana cara mengatur pH?"_
• _"kapan harus ganti nutrisi?"_
• _"cara mengatasi daun kuning"_

⚡ Quick Actions
Lakukan aksi langsung:
• _"tambah nutrisi"_
• _"turunkan pH"_
• _"kasih air"_

🚨 Alert Otomatis
Saya akan kirim notifikasi jika ada masalah dengan tanaman Anda.

---

Yuk coba sekarang! Tanyakan apa saja tentang tanaman Anda 😊""",

    'follow_up_invalid_name': """Bisa tolong ketik nama Anda sekali lagi?""",

    'follow_up_invalid_plant': """Bisa tolong ketik ulang nama tanamannya? Contoh: kangkung, tomat, selada""",

    'follow_up_invalid_stage': """Pilih salah satu ya:
1️⃣ Seedling (baru ditanam)
2️⃣ Vegetatif (tumbuh daun)
3️⃣ Berbuah/Berbunga""",

    'restart_onboarding': """Oke, kita mulai dari awal ya! 🔄

Siapa nama Anda?""",

    'onboarding_completed': """Sekarang Anda bisa langsung bertanya atau minta bantuan.

💡 Tips: Ketik *profil* kapan saja untuk lihat/edit data Anda!

Selamat menanam! 🌱""",

    'profile_view': """📋 Profil Anda:

👤 Nama: {full_name}
   Dipanggil: {nickname}
🌱 Tanaman: {plant_name} ({plant_type})
📊 Tahap: {growth_stage}

Mau edit data? Ketik:
1️⃣ *edit nama*
2️⃣ *edit tanaman*
3️⃣ *edit tahap*
4️⃣ *reset profil* (onboarding ulang)""",

    'edit_name_prompt': """Oke, siapa nama baru Anda?""",

    'edit_plant_prompt': """Oke, tanaman apa yang sekarang Anda tanam?""",

    'edit_stage_prompt': """Oke, sekarang di tahap apa?
1️⃣ Seedling (Bibit)
2️⃣ Vegetatif (Tumbuh daun)
3️⃣ Berbuah/Berbunga""",

    'edit_confirm': """Konfirmasi perubahan:
{field}: {old_value} → {new_value}

Lanjutkan? Ketik *Ya* atau *Tidak*""",

    'edit_success': """✅ Profil berhasil diupdate!

Ketik *profil* untuk lihat data terbaru.""",

    'edit_cancelled': """Perubahan dibatalkan. Data tetap seperti semula."""
}


def get_message(key: str, **kwargs) -> str:
    """
    Get formatted message template
    
    Args:
        key: Message key
        **kwargs: Variables untuk format message
    
    Returns:
        Formatted message string
    """
    template = MESSAGES.get(key, "")
    try:
        return template.format(**kwargs)
    except KeyError as e:
        # Missing variable, return template as-is
        return template

# Plant type mapping untuk auto-detection
PLANT_TYPES = {
    'leafy': [
        'kangkung', 'selada', 'lettuce', 'bayam', 'spinach', 'pakcoy', 
        'sawi', 'kale', 'arugula', 'rocket', 'kailan', 'caisim'
    ],
    'fruiting': [
        'tomat', 'tomato', 'cabai', 'chili', 'pepper', 'terong', 'eggplant',
        'timun', 'cucumber', 'melon', 'semangka', 'watermelon', 'strawberry', 'stroberi'
    ],
    'herbs': [
        'basil', 'kemangi', 'mint', 'peppermint', 'parsley', 'peterseli',
        'cilantro', 'coriander', 'ketumbar', 'oregano', 'thyme', 'rosemary'
    ]
}

def detect_plant_type(plant_name: str) -> str:
    """
    Auto-detect plant type dari nama tanaman
    
    Args:
        plant_name: Nama tanaman
    
    Returns:
        Plant type: 'leafy', 'fruiting', 'herbs', atau 'unknown'
    """
    plant_name_lower = plant_name.lower().strip()
    
    for plant_type, keywords in PLANT_TYPES.items():
        if any(keyword in plant_name_lower for keyword in keywords):
            return plant_type
    
    return 'unknown'

# Growth stage mapping
GROWTH_STAGES = {
    'seedling': ['seedling', 'bibit', 'biji', 'semai', 'seed', '1', 'satu'],
    'vegetative': ['vegetatif', 'vegetative', 'daun', 'leaf', 'tumbuh', '2', 'dua'],
    'fruiting': ['fruiting', 'berbuah', 'bunga', 'flower', 'buah', 'fruit', '3', 'tiga']
}

def detect_growth_stage(message: str) -> str:
    """
    Detect growth stage dari user message
    
    Args:
        message: User message
    
    Returns:
        Growth stage: 'seedling', 'vegetative', 'fruiting', atau 'unknown'
    """
    message_lower = message.lower().strip()
    
    for stage, keywords in GROWTH_STAGES.items():
        if any(keyword in message_lower for keyword in keywords):
            return stage
    
    return 'unknown'

if __name__ == "__main__":
    # Test messages
    print("Testing Onboarding Messages...\n")
    
    print("1. Welcome:")
    print(get_message('welcome'))
    print("\n" + "="*50 + "\n")
    
    print("2. Ask Plant Name:")
    print(get_message('ask_plant_name', name="Budi"))
    print("\n" + "="*50 + "\n")
    
    print("3. Plant Type Detection:")
    test_plants = ["kangkung", "tomat", "kemangi", "strawberry", "xyz"]
    for plant in test_plants:
        plant_type = detect_plant_type(plant)
        print(f"{plant} -> {plant_type}")
    print("\n" + "="*50 + "\n")
    
    print("4. Growth Stage Detection:")
    test_stages = ["seedling", "vegetatif", "berbuah", "1", "tiga", "xyz"]
    for stage in test_stages:
        detected = detect_growth_stage(stage)
        print(f"{stage} -> {detected}")
