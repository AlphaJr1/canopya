"""
Onboarding Messages Templates
Natural, friendly, dan step-by-step messages untuk user onboarding

MESSAGES = {

Saya akan membantu Anda merawat tanaman hidroponik dengan:
• 📊 Monitoring pH, TDS, dan suhu
• 💡 Panduan lengkap perawatan
• 🚨 Alert otomatis jika ada masalah
• ⚡ Quick actions untuk perbaikan

Sebelum mulai, saya perlu kenalan dulu dengan Anda. Siap? 😊

    

Sekarang, tanaman apa yang sedang Anda tanam?

    

1️⃣ Seedling (Bibit/Baru ditanam)
2️⃣ Vegetatif (Tumbuh daun)
3️⃣ Berbuah/Berbunga

    

👤 Nama: {name}
🌱 Tanaman: {plant_name} ({plant_type})
📊 Tahap: {growth_stage}

Apakah data ini sudah benar?
    

Sekarang saya akan tunjukkan apa saja yang bisa saya bantu:

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

Yuk coba sekarang! Tanyakan apa saja tentang tanaman Anda 😊

    

Bisa tolong ketik nama Anda sekali lagi?
    

Bisa tolong ketik ulang nama tanamannya? 
    

Pilih salah satu ya:
1️⃣ Seedling (baru ditanam)
2️⃣ Vegetatif (tumbuh daun)
3️⃣ Berbuah/Berbunga

    

    

Sekarang Anda bisa langsung bertanya atau minta bantuan.

}

"""

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
