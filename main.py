import discord
from discord.ui import Select, View, Button
from flask import Flask
import threading
from config import SECTIONS

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

app = Flask('')

@app.route('/')
def home():
    return "System Bot is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# قائمة اختيار الأقسام (Dropdown)
class SystemSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="اعدادات البوت", value="bot_settings", emoji="⚙️"),
            discord.SelectOption(label="الاوامر الادارية", value="admin_commands", emoji="🛡️"),
            discord.SelectOption(label="الاوامر العامة", value="public_commands", emoji="🌐"),
            discord.SelectOption(label="الاعدادات", value="settings", emoji="🔧"),
            discord.SelectOption(label="الرولات الخاصة", value="special_roles", emoji="👑"),
            discord.SelectOption(label="القروبات", value="groups", emoji="👥"),
        ]
        super().__init__(placeholder="اختر من القائمة لعرض الاوامر", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        section_data = SECTIONS.get(selected_key)
        
        if section_data:
            embed = discord.Embed(
                title=section_data["title"],
                description=section_data["description"] + "\n\ncoin store",
                color=0x2b2d31
            )
            await interaction.response.edit_message(embed=embed)
        else:
            await interaction.response.send_message("عذراً، القسم غير موجود.", ephemeral=True)

# واجهة تحتوي على القائمة المنسدلة وزر الدعم الخارجي
class SystemView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SystemSelect())
        # زر الدعم الخارجي (Support)
        self.add_item(Button(label="support", url="https://discord.gg/your-invite-link", emoji="🔗"))

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("System Bot is ready!")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # أمر إرسال لوحة التحكم الخاصة بالسيستم
    if message.content.startswith('!system'):
        # الافتراضي يظهر قسم "اعدادات البوت" أول ما يفتح الرسالة
        default_section = SECTIONS["bot_settings"]
        embed = discord.Embed(
            title=default_section["title"],
            description=default_section["description"] + "\n\ncoin store",
            color=0x2b2d31
        )
        await message.channel.send(embed=embed, view=SystemView())

if __name__ == "__main__":
    keep_alive()
    import os
    client.run(os.getenv('DISCORD_TOKEN'))
