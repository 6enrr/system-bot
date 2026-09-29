import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# ==================== (سيرفر Flask للتشغيل 24/7 على Render) ====================
app = Flask('')


@app.route('/')
def home():
  return 'System Bot is Online & Active 24/7!'


def run():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = threading.Thread(target=run)
  t.start()


# ==================== (إعدادات البوت والـ Intents) ====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # ضروري جداً لقراءة الأوامر التي تبدأ بـ #
intents.guilds = True

bot = commands.Bot(command_prefix='#', intents=intents)

# قواعد بيانات مؤقتة داخل الذاكرة لأنظمة السيستم
warnings_db = {}  # نظام التحذيرات
blacklist_db = set()  # نظام البلاكليست
prison_db = set()  # نظام السجن


@bot.event
async def on_ready():
  print(f'تم تسجيل الدخول بنجاح باسم نظام السيستم: {bot.user.name}')
  await bot.change_presence(activity=discord.Game(name='#help | نظام الإدارة'))


# ==================== (أوامر نظام السيستم الشاملة) ====================

# 1. أمر مسح الشات (#clear)
@bot.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
  if amount > 100:
    amount = 100
  deleted = await ctx.channel.purge(limit=amount + 1)
  msg = await ctx.send(f'🧹 | **تم بنجاح مسح `{len(deleted) - 1}` رسالة!**')
  await msg.delete(delay=3)


# 2. أمر الميوت الكتابي (#mute / #unmute)
@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute_member(ctx, member: discord.Member, *, reason=None):
  role = discord.utils.get(ctx.guild.roles, name='Muted')
  if not role:
    role = await ctx.guild.create_role(
        name='Muted', color=discord.Color.dark_grey()
    )
    for channel in ctx.guild.channels:
      try:
        await channel.set_permissions(role, send_messages=False, speak=False)
      except Exception:
        pass
  await member.add_roles(role, reason=reason)
  await ctx.send(f'🔇 | **تم إعطاء الميوت لـ {member.mention}**')


@bot.command(name='unmute')
@commands.has_permissions(manage_roles=True)
async def unmute_member(ctx, member: discord.Member):
  role = discord.utils.get(ctx.guild.roles, name='Muted')
  if role in member.roles:
    await member.remove_roles(role)
    await ctx.send(f'🔊 | **تم فك الميوت عن {member.mention}**')
  else:
    await ctx.send('❌ | **هذا العضو ليس عليه ميوت أساساً.**')


# 3. نظام السجن (#prison / #unprison / #prisons)
@bot.command(name='prison')
@commands.has_permissions(manage_roles=True)
async def prison_member(ctx, member: discord.Member, *, reason='لا يوجد سبب'):
  prison_db.add(member.id)
  embed = discord.Embed(
      title='⚖️ | **نظام السجن المركزي**',
      description=f'تم سجن العضو {member.mention} بنجاح.',
      color=discord.Color.red(),
  )
  embed.add_field(name='السبب:', value=reason, inline=False)
  await ctx.send(embed=embed)


@bot.command(name='unprison')
@commands.has_permissions(manage_roles=True)
async def unprison_member(ctx, member: discord.Member):
  if member.id in prison_db:
    prison_db.remove(member.id)
    await ctx.send(f'🔓 | **تم إفراج السجن عن العضو {member.mention}**')
  else:
    await ctx.send('❌ | **هذا العضو ليس مسجوناً أساساً.**')


@bot.command(name='prisons')
async def list_prisons(ctx):
  if not prison_db:
    await ctx.send('🏛️ | **لا يوجد أي شخص مسجون في السجن حالياً.**')
  else:
    names = [f'<@{uid}>' for uid in prison_db]
    await ctx.send(
        '🏛️ | **قائمة المسجونين حالياً:** ' + ', '.join(names)
    )


# 4. نظام التحذيرات (#warn / #warns)
@bot.command(name='warn')
@commands.has_permissions(kick_members=True)
async def warn_member(ctx, member: discord.Member, *, reason='لا يوجد سبب'):
  if member.id not in warnings_db:
    warnings_db[member.id] = []
  warnings_db[member.id].append(reason)
  await ctx.send(
      f'⚠️ | **تم تحذير العضو {member.mention}. عدد تحذيراته الآن:'
      f' {len(warnings_db[member.id])}**'
  )


@bot.command(name='warns')
async def check_warns(ctx, member: discord.Member):
  user_warns = warnings_db.get(member.id, [])
  if not user_warns:
    await ctx.send(f'✅ | **العضو {member.mention} ليس لديه أي تحذيرات.**')
  else:
    desc = '\n'.join([f'{i+1}. {w}' for i, w in enumerate(user_warns)])
    embed = discord.Embed(
        title=f'سجل تحذيرات العضو: {member.name}',
        description=desc,
        color=discord.Color.orange(),
    )
    await ctx.send(embed=embed)


# 5. نظام البلاكليست (#blacklist / #unblacklist)
@bot.command(name='blacklist')
@commands.has_permissions(administrator=True)
async def add_blacklist(ctx, member: discord.Member, *, reason=None):
  blacklist_db.add(member.id)
  await ctx.send(
      f'🚫 | **تم وضع العضو {member.mention} في قائمة البلاكليست (Blacklist).**'
  )


@bot.command(name='unblacklist')
@commands.has_permissions(administrator=True)
async def remove_blacklist(ctx, member: discord.Member):
  if member.id in blacklist_db:
    blacklist_db.remove(member.id)
    await ctx.send(
        f'✅ | **تمت إزالة العضو {member.mention} من البلاكليست بنجاح.**'
    )
  else:
    await ctx.send('❌ | **هذا العضو ليس في البلاكليست.**')


# 6. قفل وفتح الروم (#lock / #unlock)
@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx, channel: discord.TextChannel = None):
  channel = channel or ctx.channel
  await channel.set_permissions(ctx.guild.default_role, send_messages=False)
  await ctx.send(f'🔒 | **تم قفل الروم {channel.mention} بنجاح.**')


@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx, channel: discord.TextChannel = None):
  channel = channel or ctx.channel
  await channel.set_permissions(ctx.guild.default_role, send_messages=True)
  await ctx.send(f'🔓 | **تم فتح الروم {channel.mention} بنجاح.**')


# 7. معلومات السيرفر (#server)
@bot.command(name='server', aliases=['serverinfo'])
async def server_info(ctx):
  guild = ctx.guild
  embed = discord.Embed(
      title=f'📊 | معلومات سيرفر: {guild.name}', color=discord.Color.blue()
  )
  if guild.icon:
    embed.set_thumbnail(url=guild.icon.url)
  embed.add_field(name='👑 مالك السيرفر:', value=guild.owner, inline=True)
  embed.add_field(name='👥 عدد الأعضاء:', value=guild.member_count, inline=True)
  embed.add_field(
      name='📅 تاريخ إنشائه:',
      value=guild.created_at.strftime('%Y-%m-%d'),
      inline=True,
  )
  await ctx.send(embed=embed)


# نظام معالجة الأخطاء
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send('❌ | **ليس لديك الصلاحيات الكافية لاستخدام هذا الأمر!**')
  elif isinstance(error, commands.MissingRequiredArgument):
    await ctx.send('❌ | **يرجى كتابة معلومات الأمر بالطريقة الصحيحة!**')


# ==================== (تشغيل البوت والسيرفر) ====================
if __name__ == '__main__':
  keep_alive()
  TOKEN = os.getenv('TOKEN')
  if not TOKEN:
    print('خطأ: لم يتم العثور على التوكن في متغيرات البيئة!')
  else:
    bot.run(TOKEN)
